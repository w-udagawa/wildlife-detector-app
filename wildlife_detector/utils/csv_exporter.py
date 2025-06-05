"""
CSV Exporter - CSV出力機能
検出結果の詳細なCSV出力とレポート生成

このモジュールは野生生物検出結果を様々な形式のCSVファイルとして出力する機能を提供します。
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd

from ..core.species_detector import DetectionResult

class CSVExporter:
    """CSV出力クラス"""
    
    def __init__(self, output_dir: str):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリ
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def export_results(self, results: List[DetectionResult], base_filename: str = None) -> str:
        """
        検出結果をCSVファイルに出力
        
        Args:
            results: 検出結果のリスト
            base_filename: ベースファイル名（自動生成可能）
            
        Returns:
            str: 出力されたCSVファイルのパス
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"wildlife_detection_results_{timestamp}.csv"
        
        output_path = self.output_dir / base_filename
        
        try:
            # CSVデータの準備
            csv_data = self._prepare_csv_data(results)
            
            # CSVファイルの書き込み
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
                else:
                    # 空の結果の場合のヘッダー
                    fieldnames = ['image_path', 'status', 'error_message']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
            
            self.logger.info(f"CSV出力完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"CSV出力エラー: {str(e)}")
            raise
    
    def _prepare_csv_data(self, results: List[DetectionResult]) -> List[Dict[str, Any]]:
        """CSVデータの準備"""
        csv_data = []
        
        for result in results:
            base_row = {
                'image_path': result.image_path,
                'image_filename': os.path.basename(result.image_path),
                'processing_time_seconds': round(result.processing_time, 3),
                'success': result.success,
                'error_message': result.error_message if not result.success else ''
            }
            
            if result.success and result.detections:
                # 検出された各個体について行を作成
                for i, detection in enumerate(result.detections):
                    row = base_row.copy()
                    row.update({
                        'detection_id': i + 1,
                        'species': detection.get('species', ''),
                        'scientific_name': detection.get('scientific_name', ''),
                        'common_name': detection.get('common_name', ''),
                        'confidence': round(detection.get('confidence', 0), 4),
                        'category': detection.get('category', ''),
                        'bbox_x1': detection.get('bbox', [0, 0, 0, 0])[0],
                        'bbox_y1': detection.get('bbox', [0, 0, 0, 0])[1],
                        'bbox_x2': detection.get('bbox', [0, 0, 0, 0])[2],
                        'bbox_y2': detection.get('bbox', [0, 0, 0, 0])[3],
                        'total_detections_in_image': len(result.detections),
                    })
                    csv_data.append(row)
            else:
                # 検出されなかった場合
                row = base_row.copy()
                row.update({
                    'detection_id': 0,
                    'species': '',
                    'scientific_name': '',
                    'common_name': '',
                    'confidence': 0,
                    'category': '',
                    'bbox_x1': 0,
                    'bbox_y1': 0,
                    'bbox_x2': 0,
                    'bbox_y2': 0,
                    'total_detections_in_image': 0,
                })
                csv_data.append(row)
        
        return csv_data
    
    def export_summary(self, results: List[DetectionResult], base_filename: str = None) -> str:
        """
        処理サマリーをCSVファイルに出力
        
        Args:
            results: 検出結果のリスト
            base_filename: ベースファイル名（自動生成可能）
            
        Returns:
            str: 出力されたCSVファイルのパス
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"wildlife_detection_summary_{timestamp}.csv"
        
        output_path = self.output_dir / base_filename
        
        try:
            # サマリーデータの計算
            summary_data = self._calculate_summary(results)
            
            # CSVファイルの書き込み
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['metric', 'value', 'description']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for metric, value, description in summary_data:
                    writer.writerow({
                        'metric': metric,
                        'value': value,
                        'description': description
                    })
            
            self.logger.info(f"サマリーCSV出力完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"サマリーCSV出力エラー: {str(e)}")
            raise
    
    def _calculate_summary(self, results: List[DetectionResult]) -> List[tuple]:
        """サマリーデータの計算"""
        if not results:
            return [('total_images', 0, '処理対象画像数')]
        
        total_images = len(results)
        successful_images = len([r for r in results if r.success])
        failed_images = total_images - successful_images
        
        # 検出統計
        images_with_detections = len([r for r in results if r.success and r.detections])
        total_detections = sum(len(r.detections) for r in results if r.success)
        
        # 種統計
        species_counter = {}
        category_counter = {}
        
        for result in results:
            if result.success and result.detections:
                for detection in result.detections:
                    species = detection.get('common_name', 'Unknown')
                    category = detection.get('category', 'Unknown')
                    
                    species_counter[species] = species_counter.get(species, 0) + 1
                    category_counter[category] = category_counter.get(category, 0) + 1
        
        unique_species = len(species_counter)
        most_common_species = max(species_counter.items(), key=lambda x: x[1])[0] if species_counter else 'N/A'
        
        # 性能統計
        processing_times = [r.processing_time for r in results if r.processing_time > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        total_processing_time = sum(processing_times)
        
        # 信頼度統計
        confidences = []
        for result in results:
            if result.success and result.detections:
                confidences.extend([d.get('confidence', 0) for d in result.detections])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        min_confidence = min(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        
        summary_data = [
            # 基本統計
            ('total_images', total_images, '処理対象画像数'),
            ('successful_images', successful_images, '正常処理画像数'),
            ('failed_images', failed_images, '処理失敗画像数'),
            ('success_rate_percent', round((successful_images / total_images) * 100, 2), '処理成功率（%）'),
            
            # 検出統計
            ('images_with_detections', images_with_detections, '検出ありの画像数'),
            ('detection_rate_percent', round((images_with_detections / total_images) * 100, 2), '検出率（%）'),
            ('total_detections', total_detections, '総検出数'),
            ('avg_detections_per_image', round(total_detections / total_images, 2), '画像あたり平均検出数'),
            
            # 種統計
            ('unique_species_count', unique_species, '検出された種数'),
            ('most_common_species', most_common_species, '最頻出種'),
            
            # カテゴリ統計
            ('bird_detections', category_counter.get('bird', 0), '鳥類検出数'),
            ('mammal_detections', category_counter.get('mammal', 0), '哺乳類検出数'),
            ('reptile_detections', category_counter.get('reptile', 0), '爬虫類検出数'),
            ('amphibian_detections', category_counter.get('amphibian', 0), '両生類検出数'),
            
            # 性能統計
            ('total_processing_time_seconds', round(total_processing_time, 2), '総処理時間（秒）'),
            ('avg_processing_time_seconds', round(avg_processing_time, 3), '平均処理時間（秒）'),
            ('images_per_second', round(total_images / total_processing_time, 2) if total_processing_time > 0 else 0, '処理速度（画像/秒）'),
            
            # 信頼度統計
            ('avg_confidence', round(avg_confidence, 4), '平均信頼度'),
            ('min_confidence', round(min_confidence, 4), '最低信頼度'),
            ('max_confidence', round(max_confidence, 4), '最高信頼度'),
        ]
        
        return summary_data
    
    def export_species_list(self, results: List[DetectionResult], base_filename: str = None) -> str:
        """
        検出された種のリストをCSVファイルに出力
        
        Args:
            results: 検出結果のリスト
            base_filename: ベースファイル名（自動生成可能）
            
        Returns:
            str: 出力されたCSVファイルのパス
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"wildlife_species_list_{timestamp}.csv"
        
        output_path = self.output_dir / base_filename
        
        try:
            # 種統計の計算
            species_stats = self._calculate_species_stats(results)
            
            # CSVファイルの書き込み
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'common_name', 'scientific_name', 'category',
                    'detection_count', 'image_count', 'avg_confidence',
                    'min_confidence', 'max_confidence'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(species_stats)
            
            self.logger.info(f"種リストCSV出力完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"種リストCSV出力エラー: {str(e)}")
            raise
    
    def _calculate_species_stats(self, results: List[DetectionResult]) -> List[Dict[str, Any]]:
        """種別統計の計算"""
        species_data = {}
        
        for result in results:
            if result.success and result.detections:
                image_species = set()  # この画像で検出された種（重複除去用）
                
                for detection in result.detections:
                    species = detection.get('species', 'Unknown')
                    common_name = detection.get('common_name', 'Unknown')
                    scientific_name = detection.get('scientific_name', species)
                    category = detection.get('category', 'Unknown')
                    confidence = detection.get('confidence', 0)
                    
                    if species not in species_data:
                        species_data[species] = {
                            'common_name': common_name,
                            'scientific_name': scientific_name,
                            'category': category,
                            'detection_count': 0,
                            'image_count': 0,
                            'confidences': []
                        }
                    
                    species_data[species]['detection_count'] += 1
                    species_data[species]['confidences'].append(confidence)
                    
                    # 画像カウント（1つの画像で同じ種が複数検出されても1回だけカウント）
                    image_species.add(species)
                
                # 画像カウントの更新
                for species in image_species:
                    species_data[species]['image_count'] += 1
        
        # 結果の整形
        species_stats = []
        for species, data in species_data.items():
            confidences = data['confidences']
            stats = {
                'common_name': data['common_name'],
                'scientific_name': data['scientific_name'],
                'category': data['category'],
                'detection_count': data['detection_count'],
                'image_count': data['image_count'],
                'avg_confidence': round(sum(confidences) / len(confidences), 4),
                'min_confidence': round(min(confidences), 4),
                'max_confidence': round(max(confidences), 4)
            }
            species_stats.append(stats)
        
        # 検出回数順でソート
        species_stats.sort(key=lambda x: x['detection_count'], reverse=True)
        
        return species_stats
    
    def export_all(self, results: List[DetectionResult], base_filename_prefix: str = None) -> Dict[str, str]:
        """
        すべての形式でCSVを出力
        
        Args:
            results: 検出結果のリスト
            base_filename_prefix: ファイル名プレフィックス
            
        Returns:
            Dict[str, str]: 出力ファイルパスの辞書
        """
        if base_filename_prefix is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename_prefix = f"wildlife_detection_{timestamp}"
        
        output_files = {}
        
        try:
            # 詳細結果
            details_file = f"{base_filename_prefix}_results.csv"
            output_files['results'] = self.export_results(results, details_file)
            
            # サマリー
            summary_file = f"{base_filename_prefix}_summary.csv"
            output_files['summary'] = self.export_summary(results, summary_file)
            
            # 種リスト
            species_file = f"{base_filename_prefix}_species_list.csv"
            output_files['species_list'] = self.export_species_list(results, species_file)
            
            self.logger.info(f"全形式CSV出力完了: {len(output_files)}ファイル")
            return output_files
            
        except Exception as e:
            self.logger.error(f"CSV一括出力エラー: {str(e)}")
            raise

class CSVAnalyzer:
    """CSV結果の分析クラス"""
    
    @staticmethod
    def load_results(csv_path: str) -> pd.DataFrame:
        """CSV結果ファイルを読み込み"""
        try:
            return pd.read_csv(csv_path, encoding='utf-8')
        except Exception as e:
            logging.error(f"CSV読み込みエラー: {str(e)}")
            raise
    
    @staticmethod
    def analyze_temporal_patterns(df: pd.DataFrame, image_path_column: str = 'image_path') -> Dict[str, Any]:
        """時系列パターンの分析（ファイル名から推定）"""
        # TODO: ファイル名から撮影時刻を推定する実装
        # 例: IMG_20240101_120000.jpg のような形式の解析
        pass
    
    @staticmethod
    def analyze_spatial_patterns(df: pd.DataFrame) -> Dict[str, Any]:
        """空間パターンの分析（位置情報が利用可能な場合）"""
        # TODO: GPS情報が利用可能な場合の空間分析
        pass
    
    @staticmethod
    def generate_report(df: pd.DataFrame) -> str:
        """分析レポートの生成"""
        report = []
        report.append("=== Wildlife Detection Analysis Report ===\\n")
        
        # 基本統計
        total_images = df['image_path'].nunique()
        total_detections = len(df[df['detection_id'] > 0])
        unique_species = df[df['common_name'] != '']['common_name'].nunique()
        
        report.append(f"総画像数: {total_images}")
        report.append(f"総検出数: {total_detections}")
        report.append(f"検出種数: {unique_species}\\n")
        
        # 上位種
        if total_detections > 0:
            top_species = df[df['common_name'] != '']['common_name'].value_counts().head(5)
            report.append("検出頻度上位種:")
            for species, count in top_species.items():
                report.append(f"  {species}: {count}回")
            report.append("")
        
        # カテゴリ別統計
        if 'category' in df.columns:
            category_stats = df[df['category'] != '']['category'].value_counts()
            report.append("カテゴリ別検出数:")
            for category, count in category_stats.items():
                report.append(f"  {category}: {count}回")
        
        return "\\n".join(report)
