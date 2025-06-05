"""
Wildlife Detector - 設定管理
アプリケーション設定の保存・読み込み・管理
"""

import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """アプリケーション設定"""
    
    # 検出設定
    confidence_threshold: float = 0.5
    region_filter: str = "JPN"  # 地域フィルター
    batch_size: int = 32
    
    # パフォーマンス設定
    max_workers: int = 4
    use_gpu: bool = True
    memory_limit_gb: float = 4.0
    
    # UI設定
    window_width: int = 1200
    window_height: int = 800
    theme: str = "light"  # light, dark
    language: str = "ja"
    auto_save_results: bool = True
    
    # 出力設定
    default_output_directory: str = ""
    create_subdirectories: bool = True
    backup_original_files: bool = False
    
    # ファイル処理設定
    supported_formats: list = None
    max_image_size_mb: float = 50.0
    resize_large_images: bool = True
    target_image_size: int = 1024
    
    # ログ設定
    log_level: str = "INFO"
    log_to_file: bool = True
    max_log_files: int = 10
    
    # 詳細設定
    enable_preview: bool = True
    show_bounding_boxes: bool = True
    export_thumbnails: bool = False
    thumbnail_size: int = 200
    
    def __post_init__(self):
        """初期化後の処理"""
        if self.supported_formats is None:
            self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        if not self.default_output_directory:
            self.default_output_directory = str(Path.home() / "WildlifeDetector" / "Output")
    
    @classmethod
    def get_default(cls) -> 'AppConfig':
        """デフォルト設定の取得"""
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """辞書から設定オブジェクトを作成"""
        # 未知のキーを除去
        valid_keys = set(cls.__dataclass_fields__.keys())
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        
        return cls(**filtered_data)
    
    def validate(self) -> list:
        """設定値の検証"""
        errors = []
        
        # 信頼度閾値
        if not 0.0 <= self.confidence_threshold <= 1.0:
            errors.append("confidence_threshold は 0.0 から 1.0 の間である必要があります")
        
        # バッチサイズ
        if self.batch_size < 1:
            errors.append("batch_size は 1 以上である必要があります")
        
        # ワーカー数
        if self.max_workers < 1:
            errors.append("max_workers は 1 以上である必要があります")
        
        # メモリ制限
        if self.memory_limit_gb < 0.5:
            errors.append("memory_limit_gb は 0.5 以上である必要があります")
        
        # ウィンドウサイズ
        if self.window_width < 800 or self.window_height < 600:
            errors.append("ウィンドウサイズは最小 800x600 である必要があります")
        
        # 画像サイズ制限
        if self.max_image_size_mb < 1.0:
            errors.append("max_image_size_mb は 1.0 以上である必要があります")
        
        if self.target_image_size < 256:
            errors.append("target_image_size は 256 以上である必要があります")
        
        # サムネイルサイズ
        if self.thumbnail_size < 50:
            errors.append("thumbnail_size は 50 以上である必要があります")
        
        return errors

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = AppConfig.get_default()
        
        # 設定ディレクトリの作成
        config_dir = Path(self.config_file).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ConfigManager初期化: {self.config_file}")
    
    def _get_default_config_path(self) -> str:
        """デフォルト設定ファイルパスの取得"""
        config_dir = Path.home() / "WildlifeDetector" / "config"
        return str(config_dir / "wildlife_detector_config.json")
    
    def load_config(self) -> AppConfig:
        """設定の読み込み"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.config = AppConfig.from_dict(data)
                logger.info("設定ファイルを読み込みました")
                
                # 設定の検証
                errors = self.config.validate()
                if errors:
                    logger.warning("設定検証エラー:")
                    for error in errors:
                        logger.warning(f"  - {error}")
                    logger.warning("デフォルト値を使用します")
                    self.config = AppConfig.get_default()
            else:
                logger.info("設定ファイルが見つかりません。デフォルト設定を使用します")
                self.config = AppConfig.get_default()
                # デフォルト設定を保存
                self.save_config()
        
        except Exception as e:
            logger.error(f"設定読み込みエラー: {str(e)}")
            logger.info("デフォルト設定を使用します")
            self.config = AppConfig.get_default()
        
        return self.config
    
    def save_config(self) -> bool:
        """設定の保存"""
        try:
            # 設定の検証
            errors = self.config.validate()
            if errors:
                logger.error("設定保存前の検証エラー:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # JSON形式で保存
            config_data = self.config.to_dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"設定を保存しました: {self.config_file}")
            return True
        
        except Exception as e:
            logger.error(f"設定保存エラー: {str(e)}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """設定の部分更新"""
        try:
            # 現在の設定を辞書に変換
            current_dict = self.config.to_dict()
            
            # 更新
            current_dict.update(kwargs)
            
            # 新しい設定オブジェクトを作成
            self.config = AppConfig.from_dict(current_dict)
            
            # 検証
            errors = self.config.validate()
            if errors:
                logger.error("設定更新後の検証エラー:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            logger.info(f"設定を更新しました: {list(kwargs.keys())}")
            return True
        
        except Exception as e:
            logger.error(f"設定更新エラー: {str(e)}")
            return False
    
    def reset_to_default(self) -> bool:
        """デフォルト設定にリセット"""
        try:
            self.config = AppConfig.get_default()
            success = self.save_config()
            
            if success:
                logger.info("設定をデフォルトにリセットしました")
            
            return success
        
        except Exception as e:
            logger.error(f"設定リセットエラー: {str(e)}")
            return False
    
    def backup_config(self, backup_name: Optional[str] = None) -> str:
        """設定のバックアップ"""
        try:
            if backup_name is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"config_backup_{timestamp}.json"
            
            config_dir = Path(self.config_file).parent
            backup_path = config_dir / backup_name
            
            if Path(self.config_file).exists():
                import shutil
                shutil.copy2(self.config_file, backup_path)
                logger.info(f"設定をバックアップしました: {backup_path}")
                return str(backup_path)
            else:
                logger.warning("バックアップ対象の設定ファイルが存在しません")
                return ""
        
        except Exception as e:
            logger.error(f"設定バックアップエラー: {str(e)}")
            return ""
    
    def restore_config(self, backup_path: str) -> bool:
        """設定の復元"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                logger.error(f"バックアップファイルが見つかりません: {backup_path}")
                return False
            
            # バックアップファイルを読み込んで検証
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_config = AppConfig.from_dict(data)
            errors = test_config.validate()
            
            if errors:
                logger.error("バックアップファイルの検証エラー:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # 現在の設定をバックアップ
            self.backup_config("config_before_restore.json")
            
            # バックアップファイルを復元
            import shutil
            shutil.copy2(backup_file, self.config_file)
            
            # 設定を再読み込み
            self.load_config()
            
            logger.info(f"設定を復元しました: {backup_path}")
            return True
        
        except Exception as e:
            logger.error(f"設定復元エラー: {str(e)}")
            return False
    
    def get_config(self) -> AppConfig:
        """現在の設定を取得"""
        return self.config
    
    def get_config_info(self) -> Dict[str, Any]:
        """設定情報の取得"""
        config_file_path = Path(self.config_file)
        
        info = {
            'config_file': str(config_file_path),
            'exists': config_file_path.exists(),
            'size_bytes': 0,
            'modified_time': None,
            'is_valid': True,
            'validation_errors': []
        }
        
        try:
            if config_file_path.exists():
                stat = config_file_path.stat()
                info['size_bytes'] = stat.st_size
                info['modified_time'] = stat.st_mtime
            
            # 設定の検証
            errors = self.config.validate()
            if errors:
                info['is_valid'] = False
                info['validation_errors'] = errors
        
        except Exception as e:
            logger.error(f"設定情報取得エラー: {str(e)}")
            info['error'] = str(e)
        
        return info
    
    def export_config(self, export_path: str) -> bool:
        """設定のエクスポート"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            config_data = self.config.to_dict()
            
            # エクスポート情報を追加
            from datetime import datetime
            config_data['_export_info'] = {
                'export_time': datetime.now().isoformat(),
                'app_version': '1.0.0',
                'export_source': str(self.config_file)
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"設定をエクスポートしました: {export_path}")
            return True
        
        except Exception as e:
            logger.error(f"設定エクスポートエラー: {str(e)}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """設定のインポート"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"インポートファイルが見つかりません: {import_path}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # エクスポート情報を除去
            if '_export_info' in data:
                export_info = data.pop('_export_info')
                logger.info(f"インポート元: {export_info.get('export_source', 'unknown')}")
            
            # 設定を検証
            test_config = AppConfig.from_dict(data)
            errors = test_config.validate()
            
            if errors:
                logger.error("インポートファイルの検証エラー:")
                for error in errors:
                    logger.error(f"  - {error}")
                return False
            
            # 現在の設定をバックアップ
            self.backup_config("config_before_import.json")
            
            # 設定を更新
            self.config = test_config
            success = self.save_config()
            
            if success:
                logger.info(f"設定をインポートしました: {import_path}")
            
            return success
        
        except Exception as e:
            logger.error(f"設定インポートエラー: {str(e)}")
            return False
