"""
Wildlife Detector - ファイル管理機能
画像の自動振り分け、コピー、移動、リネーム機能
"""

import logging
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..core.species_detector import DetectionResult

logger = logging.getLogger(__name__)

class FileManager:
    """ファイル管理クラス"""
    
    def __init__(self, output_directory: str):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # タイムスタンプ生成
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"FileManager初期化: {self.output_directory}")
    
    def organize_images_by_species(self, results: List[DetectionResult], 
                                 copy_files: bool = True,
                                 confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """種別による画像の自動振り分け"""
        
        logger.info(f"画像振り分け開始: {len(results)} 枚")
        logger.info(f"コピーモード: {copy_files}, 信頼度閾値: {confidence_threshold}")
        
        # 振り分け結果の記録
        organization_result = {
            'success': True,
            'total_images': len(results),
            'processed_images': 0,
            'failed_images': 0,
            'species_folders': {},
            'error_files': [],
            'no_detection_count': 0,
            'multiple_species_count': 0
        }
        
        try:
            # 基本フォルダの作成
            base_folder = self.output_directory / f"organized_images_{self.timestamp}"
            base_folder.mkdir(exist_ok=True)
            
            # 特別フォルダの作成
            no_detection_folder = base_folder / "no_detection"
            multiple_species_folder = base_folder / "multiple_species"
            no_detection_folder.mkdir(exist_ok=True)
            multiple_species_folder.mkdir(exist_ok=True)
            
            for result in results:
                try:
                    # ファイル存在確認
                    source_path = Path(result.image_path)
                    if not source_path.exists():
                        logger.warning(f"ソースファイルが見つかりません: {source_path}")
                        organization_result['error_files'].append({
                            'file': str(source_path),
                            'error': 'ファイルが見つかりません'
                        })
                        organization_result['failed_images'] += 1
                        continue
                    
                    # 信頼度フィルタリング
                    filtered_detections = result.filter_by_confidence(confidence_threshold)
                    
                    if not filtered_detections:
                        # 検出なしまたは信頼度不足
                        target_folder = no_detection_folder
                        folder_name = "no_detection"
                        organization_result['no_detection_count'] += 1
                    
                    elif len(filtered_detections) == 1:
                        # 単一種検出
                        detection = filtered_detections[0]
                        folder_name = self._sanitize_folder_name(detection.common_name)
                        target_folder = base_folder / folder_name
                        target_folder.mkdir(exist_ok=True)
                        
                        # 種別フォルダ記録
                        if folder_name not in organization_result['species_folders']:
                            organization_result['species_folders'][folder_name] = {
                                'species_name': detection.common_name,
                                'scientific_name': detection.scientific_name,
                                'category': detection.category,
                                'file_count': 0,
                                'avg_confidence': 0.0,
                                'files': []
                            }
                    
                    else:
                        # 複数種検出
                        target_folder = multiple_species_folder
                        folder_name = "multiple_species"
                        organization_result['multiple_species_count'] += 1
                    
                    # ファイルのコピーまたは移動
                    target_filename = self._generate_target_filename(
                        source_path, result, filtered_detections
                    )
                    target_path = target_folder / target_filename
                    
                    # ファイル名の重複回避
                    target_path = self._avoid_filename_collision(target_path)
                    
                    if copy_files:
                        shutil.copy2(source_path, target_path)
                        logger.debug(f"コピー: {source_path} -> {target_path}")
                    else:
                        shutil.move(str(source_path), str(target_path))
                        logger.debug(f"移動: {source_path} -> {target_path}")
                    
                    # 統計更新
                    organization_result['processed_images'] += 1
                    
                    if folder_name in organization_result['species_folders']:
                        folder_info = organization_result['species_folders'][folder_name]
                        folder_info['file_count'] += 1
                        folder_info['files'].append(str(target_path))
                        
                        # 平均信頼度の更新
                        if filtered_detections:
                            confidences = [d.confidence for d in filtered_detections]
                            avg_conf = sum(confidences) / len(confidences)
                            current_avg = folder_info['avg_confidence']
                            count = folder_info['file_count']
                            folder_info['avg_confidence'] = (
                                (current_avg * (count - 1) + avg_conf) / count
                            )
                
                except Exception as e:
                    logger.error(f"画像振り分けエラー {result.image_path}: {str(e)}")
                    organization_result['error_files'].append({
                        'file': result.image_path,
                        'error': str(e)
                    })
                    organization_result['failed_images'] += 1
            
            # 振り分け結果レポートの作成
            self._create_organization_report(base_folder, organization_result)
            
            organization_result['output_directory'] = str(base_folder)
            
            logger.info(f"画像振り分け完了: {organization_result['processed_images']}/{organization_result['total_images']} 枚")
            logger.info(f"種別フォルダ数: {len(organization_result['species_folders'])}")
            
        except Exception as e:
            logger.error(f"画像振り分けでエラーが発生: {str(e)}")
            organization_result['success'] = False
            organization_result['error'] = str(e)
        
        return organization_result
    
    def _sanitize_folder_name(self, species_name: str) -> str:
        """フォルダ名の無害化"""
        # Windowsで使用できない文字を除去/置換
        invalid_chars = '<>:"/\\|?*'
        sanitized = species_name
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 連続するアンダースコアを単一に
        while '__' in sanitized:
            sanitized = sanitized.replace('__', '_')
        
        # 前後の空白とピリオドを除去
        sanitized = sanitized.strip(' .')
        
        # 空の場合のフォールバック
        if not sanitized:
            sanitized = "unknown_species"
        
        return sanitized
    
    def _generate_target_filename(self, source_path: Path, 
                                result: DetectionResult,
                                detections: List) -> str:
        """ターゲットファイル名の生成"""
        
        # 基本ファイル名
        base_name = source_path.stem
        extension = source_path.suffix
        
        # 検出情報の追加
        if detections:
            if len(detections) == 1:
                detection = detections[0]
                confidence_str = f"{detection.confidence:.3f}"
                species_short = detection.species[:10] if detection.species else "unknown"
                filename = f"{base_name}_{species_short}_{confidence_str}{extension}"
            else:
                filename = f"{base_name}_multi_{len(detections)}species{extension}"
        else:
            filename = f"{base_name}_no_detection{extension}"
        
        return filename
    
    def _avoid_filename_collision(self, target_path: Path) -> Path:
        """ファイル名の重複回避"""
        if not target_path.exists():
            return target_path
        
        base_name = target_path.stem
        extension = target_path.suffix
        parent = target_path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter:03d}{extension}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
            
            if counter > 999:  # 無限ループ防止
                timestamp = datetime.now().strftime("%H%M%S")
                new_name = f"{base_name}_{timestamp}{extension}"
                return parent / new_name
    
    def _create_organization_report(self, base_folder: Path, 
                                  organization_result: Dict[str, Any]):
        """振り分け結果レポートの作成"""
        
        report_path = base_folder / "organization_report.txt"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("Wildlife Detector - 画像振り分けレポート\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"出力ディレクトリ: {base_folder}\n\n")
                
                # 全体統計
                f.write("=== 全体統計 ===\n")
                f.write(f"総画像数: {organization_result['total_images']}\n")
                f.write(f"処理成功: {organization_result['processed_images']}\n")
                f.write(f"処理失敗: {organization_result['failed_images']}\n")
                f.write(f"検出なし: {organization_result['no_detection_count']}\n")
                f.write(f"複数種検出: {organization_result['multiple_species_count']}\n\n")
                
                # 種別統計
                if organization_result['species_folders']:
                    f.write("=== 種別統計 ===\n")
                    species_folders = organization_result['species_folders']
                    sorted_species = sorted(species_folders.items(), 
                                          key=lambda x: x[1]['file_count'], 
                                          reverse=True)
                    
                    for folder_name, info in sorted_species:
                        f.write(f"\n{info['species_name']} ({info['scientific_name']})\n")
                        f.write(f"  - カテゴリ: {info['category']}\n")
                        f.write(f"  - ファイル数: {info['file_count']}\n")
                        f.write(f"  - 平均信頼度: {info['avg_confidence']:.3f}\n")
                        f.write(f"  - フォルダ: {folder_name}\n")
                
                # エラーファイル
                if organization_result['error_files']:
                    f.write("\n=== エラーファイル ===\n")
                    for error_info in organization_result['error_files']:
                        f.write(f"- {error_info['file']}: {error_info['error']}\n")
            
            logger.info(f"振り分けレポート作成: {report_path}")
            
        except Exception as e:
            logger.error(f"レポート作成エラー: {str(e)}")
    
    def create_backup(self, source_files: List[str], 
                     backup_name: Optional[str] = None) -> str:
        """ファイルのバックアップ作成"""
        
        if backup_name is None:
            backup_name = f"backup_{self.timestamp}"
        
        backup_folder = self.output_directory / backup_name
        backup_folder.mkdir(exist_ok=True)
        
        logger.info(f"バックアップ作成開始: {len(source_files)} ファイル")
        
        success_count = 0
        error_files = []
        
        for source_file in source_files:
            try:
                source_path = Path(source_file)
                if not source_path.exists():
                    error_files.append(f"{source_file}: ファイルが見つかりません")
                    continue
                
                target_path = backup_folder / source_path.name
                target_path = self._avoid_filename_collision(target_path)
                
                shutil.copy2(source_path, target_path)
                success_count += 1
                
            except Exception as e:
                error_files.append(f"{source_file}: {str(e)}")
        
        logger.info(f"バックアップ完了: {success_count}/{len(source_files)} ファイル")
        
        if error_files:
            logger.warning(f"バックアップエラー: {len(error_files)} ファイル")
            
            # エラーレポート作成
            error_report_path = backup_folder / "backup_errors.txt"
            with open(error_report_path, 'w', encoding='utf-8') as f:
                f.write("バックアップエラーレポート\n")
                f.write("=" * 30 + "\n\n")
                for error in error_files:
                    f.write(f"{error}\n")
        
        return str(backup_folder)
    
    def clean_empty_folders(self, base_directory: Optional[str] = None) -> int:
        """空フォルダの削除"""
        
        if base_directory is None:
            base_directory = str(self.output_directory)
        
        base_path = Path(base_directory)
        removed_count = 0
        
        logger.info(f"空フォルダクリーンアップ開始: {base_path}")
        
        try:
            # 深い階層から順に処理
            for folder in sorted(base_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
                if folder.is_dir() and folder != base_path:
                    try:
                        folder.rmdir()  # 空フォルダのみ削除される
                        logger.debug(f"空フォルダ削除: {folder}")
                        removed_count += 1
                    except OSError:
                        # フォルダが空でない場合は無視
                        pass
        
        except Exception as e:
            logger.error(f"空フォルダクリーンアップエラー: {str(e)}")
        
        logger.info(f"空フォルダクリーンアップ完了: {removed_count} フォルダ削除")
        return removed_count
    
    def get_disk_usage(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """ディスク使用量の取得"""
        
        if directory is None:
            directory = str(self.output_directory)
        
        path = Path(directory)
        
        try:
            total_size = 0
            file_count = 0
            folder_count = 0
            
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
                    file_count += 1
                elif item.is_dir():
                    folder_count += 1
            
            # 可読形式のサイズ
            size_mb = total_size / (1024 * 1024)
            size_gb = size_mb / 1024
            
            return {
                'directory': str(path),
                'total_size_bytes': total_size,
                'total_size_mb': round(size_mb, 2),
                'total_size_gb': round(size_gb, 3),
                'file_count': file_count,
                'folder_count': folder_count
            }
        
        except Exception as e:
            logger.error(f"ディスク使用量取得エラー: {str(e)}")
            return {
                'directory': str(path),
                'error': str(e)
            }
    
    def get_output_directory(self) -> str:
        """出力ディレクトリのパス取得"""
        return str(self.output_directory)
