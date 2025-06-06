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

@dataclass
class ProcessingStats:
    """処理統計情報"""
    total_images: int = 0
    processed_images: int = 0
    successful_detections: int = 0
    failed_detections: int = 0
    total_detections: int = 0
    processing_time: float = 0.0
    average_time_per_image: float = 0.0
    species_counts: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'total_images': self.total_images,
            'processed_images': self.processed_images,
            'successful_detections': self.successful_detections,
            'failed_detections': self.failed_detections,
            'total_detections': self.total_detections,
            'processing_time': self.processing_time,
            'average_time_per_image': self.average_time_per_image,
            'species_counts': self.species_counts,
            'error_counts': self.error_counts
        }

class BatchProcessor:
    """バッチ処理エンジン"""
    
    def __init__(self, config):
        """
        初期化
        
        Args:
            config: AppConfig インスタンス
        """
        self.config = config
        self.detector = None
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
        self.progress_callback: Optional[Callable] = None
        self.completion_callback: Optional[Callable] = None
        
        # 結果保存
        self.results: List[DetectionResult] = []
        self.stats: Optional[ProcessingStats] = None
        self.results_lock = threading.Lock()
        self._start_time = 0.0
    
    def initialize(self) -> bool:
        """バッチ処理器の初期化"""
        try:
            # SpeciesDetectorの初期化
            self.detector = SpeciesDetector(self.config)
            if not self.detector.initialize():
                self.logger.error("SpeciesDetector の初期化に失敗しました")
                return False
            
            self.logger.info("BatchProcessor が初期化されました")
            return True
            
        except Exception as e:
            self.logger.error(f"BatchProcessor 初期化エラー: {str(e)}")
            return False
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.detector:
            self.detector.cleanup()
            self.detector = None
        self.logger.info("BatchProcessor がクリーンアップされました")
    
    def cancel_processing(self):
        """処理のキャンセル"""
        self.stop_requested = True
        self.logger.info("バッチ処理のキャンセルが要求されました")
    
    def set_progress_callback(self, callback: Callable):
        """進捗更新コールバックを設定"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable):
        """完了コールバックを設定"""
        self.completion_callback = callback
    
    def process_batch(self, image_paths: List[str], progress_callback: Callable = None) -> List[DetectionResult]:
        """
        バッチ処理の実行
        
        Args:
            image_paths: 処理する画像パスのリスト
            progress_callback: 進捗コールバック関数
            
        Returns:
            List[DetectionResult]: 検出結果のリスト
        """
        if not self.detector:
            raise Exception("BatchProcessor が初期化されていません")
        
        job_id = f"batch_{int(time.time())}"
        
        # ジョブとプログレスの初期化
        self.current_job = BatchJob(image_paths, "", job_id)
        self.progress = BatchProgress(job_id, total=len(image_paths))
        self.results = []
        self.is_running = True
        self.stop_requested = False
        self._start_time = time.time()
        
        if progress_callback:
            self.progress_callback = progress_callback
        
        self.logger.info(f"バッチ処理開始: {len(image_paths)}枚の画像を処理")
        
        try:
            # 並列処理の実行
            if self.max_workers == 1:
                # シングルスレッド処理
                results = self._process_sequential(image_paths)
            else:
                # マルチスレッド処理
                results = self._process_parallel(image_paths)
            
            # 統計情報の生成
            self._generate_statistics(results)
            
            # 処理時間の更新
            self.progress.elapsed_time = time.time() - self._start_time
            
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
            
            # 進捗コールバック
            if self.progress_callback:
                self.progress_callback(
                    i, len(image_paths), 
                    "処理中", 
                    os.path.basename(image_path)
                )
            
            # 画像処理
            result = self.detector.detect_species(image_path)
            results.append(result)
            
            # 進捗更新
            self._update_progress_counts(result.success)
        
        return results
    
    def _process_parallel(self, image_paths: List[str]) -> List[DetectionResult]:
        """並列処理"""
        results = []
        completed_count = 0
        
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
                completed_count += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 進捗コールバック
                    if self.progress_callback:
                        self.progress_callback(
                            completed_count, len(image_paths),
                            "処理中",
                            os.path.basename(image_path)
                        )
                    
                    # 進捗更新
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
    
    def _update_progress_counts(self, success: bool):
        """進捗カウントの更新"""
        with self.results_lock:
            if self.progress:
                self.progress.processed += 1
                if success:
                    self.progress.success += 1
                else:
                    self.progress.failed += 1
                
                self.progress.elapsed_time = time.time() - self._start_time
    
    def _generate_statistics(self, results: List[DetectionResult]):
        """統計情報の生成"""
        successful_detections = 0
        total_detections = 0
        species_counts = {}
        error_counts = {}
        total_processing_time = 0.0
        
        for result in results:
            total_processing_time += result.processing_time
            
            if result.success:
                successful_detections += 1
                total_detections += len(result.detections)
                
                # 種別カウント
                for detection in result.detections:
                    species = detection.get('common_name', 'Unknown')
                    species_counts[species] = species_counts.get(species, 0) + 1
            else:
                # エラーカウント
                error_msg = result.error_message or 'Unknown Error'
                error_counts[error_msg] = error_counts.get(error_msg, 0) + 1
        
        # 統計オブジェクトの作成
        self.stats = ProcessingStats(
            total_images=len(results),
            processed_images=len(results),
            successful_detections=successful_detections,
            failed_detections=len(results) - successful_detections,
            total_detections=total_detections,
            processing_time=time.time() - self._start_time,
            average_time_per_image=total_processing_time / len(results) if results else 0.0,
            species_counts=species_counts,
            error_counts=error_counts
        )
    
    def get_statistics(self) -> ProcessingStats:
        """統計情報を取得"""
        return self.stats or ProcessingStats()
    
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
            if not self.stats:
                return
            
            summary = {
                "processing_stats": self.stats.to_dict(),
                "timestamp": time.time()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"結果サマリーを保存しました: {output_path}")
            
        except Exception as e:
            self.logger.error(f"結果サマリー保存エラー: {str(e)}")

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
