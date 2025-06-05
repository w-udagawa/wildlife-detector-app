"""
設定管理モジュール
Wildlife Detectorアプリケーションの設定を管理
"""
import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class AppConfig:
    """アプリケーション設定クラス"""
    # SpeciesNet設定
    batch_size: int = 32
    confidence_threshold: float = 0.1
    country_filter: str = "JPN"  # 日本の野生生物に特化
    
    # ファイル処理設定
    supported_formats: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
    max_image_size: tuple = (2048, 2048)  # 最大画像サイズ
    
    # 出力設定
    output_csv_name: str = "detection_results.csv"
    create_species_folders: bool = True
    copy_images_to_folders: bool = True
    
    # パフォーマンス設定
    use_gpu: bool = True
    max_workers: int = 4
    memory_limit_mb: int = 4096
    
    # GUI設定
    window_size: tuple = (1200, 800)
    progress_update_interval: int = 100  # ミリ秒
    
    @classmethod
    def get_default(cls) -> 'AppConfig':
        """デフォルト設定を取得"""
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得"""
        return {
            'batch_size': self.batch_size,
            'confidence_threshold': self.confidence_threshold,
            'country_filter': self.country_filter,
            'supported_formats': self.supported_formats,
            'max_image_size': self.max_image_size,
            'output_csv_name': self.output_csv_name,
            'create_species_folders': self.create_species_folders,
            'copy_images_to_folders': self.copy_images_to_folders,
            'use_gpu': self.use_gpu,
            'max_workers': self.max_workers,
            'memory_limit_mb': self.memory_limit_mb,
            'window_size': self.window_size,
            'progress_update_interval': self.progress_update_interval
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AppConfig':
        """辞書から設定を作成"""
        return cls(**config_dict)

class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_file: str = "wildlife_detector_config.json"):
        self.config_file = config_file
        self.config = AppConfig.get_default()
    
    def load_config(self) -> AppConfig:
        """設定ファイルから設定を読み込み"""
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                self.config = AppConfig.from_dict(config_dict)
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗しました: {e}")
                print("デフォルト設定を使用します")
                self.config = AppConfig.get_default()
        return self.config
    
    def save_config(self) -> bool:
        """現在の設定をファイルに保存"""
        try:
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def update_config(self, **kwargs) -> None:
        """設定を更新"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def get_config(self) -> AppConfig:
        """現在の設定を取得"""
        return self.config
