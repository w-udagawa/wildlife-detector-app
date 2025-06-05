"""
ファイル管理モジュール
Wildlife Detectorアプリケーションのファイル操作を管理
"""
import os
import shutil
import json
import hashlib
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class FileOrganizationReport:
    """ファイル組織化レポート"""
    total_files: int = 0
    organized_files: int = 0
    created_folders: int = 0
    errors: List[str] = None
    species_distribution: Dict[str, int] = None
    disk_usage_before: int = 0
    disk_usage_after: int = 0
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.species_distribution is None:
            self.species_distribution = {}


class FileManager:
    """ファイル管理クラス"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.backup_path = self.base_path / "backups"
        self.organized_path = self.base_path / "organized"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        self.backup_path.mkdir(parents=True, exist_ok=True)
        self.organized_path.mkdir(parents=True, exist_ok=True)
    
    def organize_by_species(self, detection_results: List[Dict], 
                          source_dir: str, create_copies: bool = True) -> FileOrganizationReport:
        """
        検出結果に基づいてファイルを種別で整理
        
        Args:
            detection_results: 検出結果のリスト
            source_dir: ソースディレクトリ
            create_copies: True=コピー、False=移動
        
        Returns:
            FileOrganizationReport: 組織化レポート
        """
        start_time = datetime.now()
        report = FileOrganizationReport()
        source_path