"""
Batch Processor - バッチ処理エンジン
大量の画像に対する効率的な並列処理を提供

このモジュールは数千枚の画像を効率的に処理するためのバッチ処理機能を提供します。
"""

import os
import logging
import time
from typing import List, Dict, Callable, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import threading
from dataclasses import dataclass, field
from queue import Queue
import json

from .species_detector import SpeciesDetector, DetectionResult

@dataclass
class BatchJob:
    """バッチ処理ジョブの定義"""
    image_paths: List[str]
    output_dir: str
    job_id: str
    total_images: int = field(init=False)
    
    def __post_init__(self):
        self.total_images = len(self.image_paths)

@dataclass
class BatchProgress:
    """バッチ処理の進捗情報"""
    job_id: str
    processed: int = 0
    total: int = 0
    success: int = 0
    failed: int = 0
    current_file: str = ""
    elapsed_time: float = 0.0
    estimated_remaining: float = 0.0
    
    @property
    def progress_percentage(self) -> float:
        """進捗の割合（0-100）"""
        if self.total == 0:
            return 0.0
        return (self.processed / self.total) * 100
    
    @property
    def success_rate(self) -> float:
        """成功率（0-100）"""
        if self.processed == 0:
            return 0.0
        return (self.success / self.processed) * 100

class BatchProcessor:
    """バッチ処理エンジン"""
    
    def __init__(self, config, species_detector: SpeciesDetector):
        """
        初期化
        
        Args:
            config: AppConfig インスタンス
            species_detector: 種検出器インスタンス
        """
        self.config = config
        self.detector = species_detector
        self.logger = logging.getLogger(__name__)
        
        # 処理設定
        self.max_workers = getattr(config, 'max_workers', 4)
        self.batch_size = getattr(config, 'batch_size', 32)
        
        # 進捗管理
        self.current_job: Optional[BatchJob] = None
        self.progress: Optional[BatchProgress] = None
        self.is_running = False
        self.stop_requested = False
        
        # コールバック関数
        self.progress_callback: Optional[Callable[[BatchProgress], None]] = None
        self.completion_callback: Optional[Callable[[List[DetectionResult]], None]] = None
        
        # 結果保存
        self.results: List[DetectionResult] = []
        self.results_lock = threading.Lock()
    
    def set_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """進捗更新コールバックを設定"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[List[DetectionResult]], None]):
        """完了コールバックを設定"""
        self.completion_callback = callback
    
    def process_batch(self, image_paths: List[str], output_dir: str, job_id: str = None) -> List[DetectionResult]:
        """
        バッチ処理の実行
        
        Args:
            image_paths: 処理する画像パスのリスト
            output_dir: 出力ディレクトリ
            job_id: ジョブID（自動生成可能）
            
        Returns:
            List[DetectionResult]: 検出結果のリスト
        """
        if job_id is None:
            job_id = f"batch_{int(time.time())}"
        
        # ジョブとプログレスの初期化
        self.current_job = BatchJob(image_paths, output_dir, job_id)
        self.progress = BatchProgress(job_id, total=len(image_paths))
        self.results = []
        self.is_running = True
        self.stop_requested = False
        
        self.logger.info(f"バッチ処理開始: {len(image_paths)}枚の画像を処理")
        start_time = time.time()
        
        try:
            # 出力ディレクトリの作成
            os.makedirs(output_dir, exist_ok=True)
            
            # 並列処理の実行
            if self.max_workers == 1:
                # シングルスレッド処理
                results = self._process_sequential(image_paths)
            else:
                # マルチスレッド処理
                results = self._process_parallel(image_paths)
            
            # 処理時間の更新
            self.progress.elapsed_time = time.time() - start_time
            
            # 完了コールバックの実行
            if self.completion_callback:
                self.completion_callback(results)
            
            self.logger.info(f"バッチ処理完了: {self.progress.success}成功 / {self.progress.failed}失敗")
            return results
            
        except Exception as e:
            self.logger.error(f"バッチ処理エラー: {str(e)}")
            raise
        finally:
            self.is_running = False
    
    def _process_sequential(self, image_paths: List[str]) -> List[DetectionResult]:
        """シーケンシャル処理"""
        results = []
        
        for i, image_path in enumerate(image_paths):
            if self.stop_requested:
                self.logger.info("処理が中断されました")
                break
            
            self._update_progress(current_file=os.path.basename(image_path))
            
            # 画像処理
            result = self.detector.detect_species(image_path)
            results.append(result)
            
            # 進捗更新
            self._update_progress_counts(result.success)
            
        return results
    
    def _process_parallel(self, image_paths: List[str]) -> List[DetectionResult]:
        """並列処理"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # すべてのタスクを投入
            future_to_path = {
                executor.submit(self._process_single_image, path): path 
                for path in image_paths
            }
            
            # 結果を収集
            for future in as_completed(future_to_path):
                if self.stop_requested:
                    self.logger.info("処理が中断されました")
                    # 未完了のタスクをキャンセル
                    for f in future_to_path:
                        f.cancel()
                    break
                
                image_path = future_to_path[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 進捗更新
                    self._update_progress(current_file=os.path.basename(image_path))
                    self._update_progress_counts(result.success)
                    
                except Exception as e:
                    self.logger.error(f"画像処理エラー ({image_path}): {str(e)}")
                    # エラー結果を作成
                    error_result = DetectionResult(
                        image_path=image_path,
                        detections=[],
                        success=False,
                        error_message=str(e)
                    )
                    results.append(error_result)
                    self._update_progress_counts(False)
        
        return results
    
    def _process_single_image(self, image_path: str) -> DetectionResult:
        """単一画像の処理（並列処理用）"""
        return self.detector.detect_species(image_path)
    
    def _update_progress(self, current_file: str = ""):
        """進捗情報の更新"""
        if self.progress:
            if current_file:
                self.progress.current_file = current_file
            
            # 残り時間の推定
            if self.progress.processed > 0:
                avg_time_per_image = self.progress.elapsed_time / self.progress.processed
                remaining_images = self.progress.total - self.progress.processed
                self.progress.estimated_remaining = avg_time_per_image * remaining_images
            
            # コールバックの実行
            if self.progress_callback:
                self.progress_callback(self.progress)
    
    def _update_progress_counts(self, success: bool):
        """進捗カウントの更新"""
        with self.results_lock:
            if self.progress:
                self.progress.processed += 1
                if success:
                    self.progress.success += 1
                else:
                    self.progress.failed += 1
                
                self.progress.elapsed_time = time.time() - self._start_time if hasattr(self, '_start_time') else 0
    
    def stop_processing(self):
        """処理の停止要求"""
        self.stop_requested = True
        self.logger.info("バッチ処理の停止が要求されました")
    
    def get_progress(self) -> Optional[BatchProgress]:
        """現在の進捗情報を取得"""
        return self.progress
    
    def is_processing(self) -> bool:
        """処理中かどうかを確認"""
        return self.is_running
    
    def get_results(self) -> List[DetectionResult]:
        """処理結果を取得"""
        with self.results_lock:
            return self.results.copy()
    
    def save_results_summary(self, output_path: str):
        """結果サマリーをJSONで保存"""
        try:
            if not self.results or not self.progress:
                return
            
            summary = {
                "job_info": {
                    "job_id": self.progress.job_id,
                    "total_images": self.progress.total,
                    "processed": self.progress.processed,
                    "success": self.progress.success,
                    "failed": self.progress.failed,
                    "success_rate": self.progress.success_rate,
                    "processing_time": self.progress.elapsed_time
                },
                "species_summary": self._generate_species_summary(),
                "performance_stats": self._generate_performance_stats()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"結果サマリーを保存しました: {output_path}")
            
        except Exception as e:
            self.logger.error(f"結果サマリー保存エラー: {str(e)}")
    
    def _generate_species_summary(self) -> Dict:
        """検出された種のサマリーを生成"""
        species_count = {}
        total_detections = 0
        
        for result in self.results:
            if result.success and result.detections:
                for detection in result.detections:
                    species = detection.get('common_name', 'Unknown')
                    species_count[species] = species_count.get(species, 0) + 1
                    total_detections += 1
        
        # 上位種の取得
        top_species = sorted(species_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_detections": total_detections,
            "unique_species_count": len(species_count),
            "top_species": [{"species": species, "count": count} for species, count in top_species],
            "detection_rate": (len([r for r in self.results if r.detections]) / len(self.results)) * 100 if self.results else 0
        }
    
    def _generate_performance_stats(self) -> Dict:
        """パフォーマンス統計を生成"""
        if not self.results:
            return {}
        
        processing_times = [r.processing_time for r in self.results if r.processing_time > 0]
        
        if not processing_times:
            return {}
        
        return {
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "min_processing_time": min(processing_times),
            "max_processing_time": max(processing_times),
            "total_processing_time": sum(processing_times),
            "images_per_second": len(processing_times) / sum(processing_times) if sum(processing_times) > 0 else 0
        }

class BatchImageFinder:
    """バッチ処理用画像ファイル検索"""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    @staticmethod
    def find_images(input_path: str, recursive: bool = True) -> List[str]:
        """
        画像ファイルを検索
        
        Args:
            input_path: 検索対象のパス（ファイルまたはディレクトリ）
            recursive: サブディレクトリも検索するか
            
        Returns:
            List[str]: 見つかった画像ファイルのパスリスト
        """
        image_paths = []
        
        path = Path(input_path)
        
        if path.is_file():
            # 単一ファイルの場合
            if path.suffix.lower() in BatchImageFinder.SUPPORTED_EXTENSIONS:
                image_paths.append(str(path))
        elif path.is_dir():
            # ディレクトリの場合
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for ext in BatchImageFinder.SUPPORTED_EXTENSIONS:
                image_paths.extend([
                    str(p) for p in path.glob(f"{pattern}{ext}")
                    if p.is_file()
                ])
                image_paths.extend([
                    str(p) for p in path.glob(f"{pattern}{ext.upper()}")
                    if p.is_file()
                ])
        
        return sorted(list(set(image_paths)))  # 重複除去とソート
    
    @staticmethod
    def validate_images(image_paths: List[str]) -> List[str]:
        """
        画像ファイルの妥当性をチェック
        
        Args:
            image_paths: チェック対象の画像パスリスト
            
        Returns:
            List[str]: 有効な画像ファイルのパスリスト
        """
        valid_paths = []
        
        for path in image_paths:
            try:
                if os.path.exists(path) and os.path.getsize(path) > 0:
                    # 簡単な画像ファイルチェック
                    from PIL import Image
                    with Image.open(path) as img:
                        img.verify()  # ファイルが有効な画像かチェック
                    valid_paths.append(path)
            except Exception:
                continue  # 無効なファイルはスキップ
        
        return valid_paths
