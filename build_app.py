"""
Wildlife Detector ビルドスクリプト
PyInstallerを使用して実行ファイルを作成
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_pyinstaller():
    """PyInstallerのインストール確認"""
    try:
        import PyInstaller
        logger.info(f"PyInstaller バージョン: {PyInstaller.__version__}")
        return True
    except ImportError:
        logger.error("PyInstallerがインストールされていません")
        logger.error("次のコマンドでインストールしてください: pip install pyinstaller")
        return False

def clean_build_directories():
    """ビルドディレクトリのクリーンアップ"""
    build_dirs = ['build', 'dist', '__pycache__']
    
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                logger.info(f"削除完了: {dir_name}")
            except Exception as e:
                logger.warning(f"削除失敗: {dir_name} - {e}")

def create_spec_file():
    """PyInstaller specファイルの作成"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['wildlife_detector/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('wildlife_detector/gui', 'gui'),
        ('wildlife_detector/core', 'core'),
        ('wildlife_detector/utils', 'utils'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'numpy',
        'pandas',
        'PIL',
        'cv2',
        'speciesnet',
        'tqdm',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WildlifeDetector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUIアプリケーションなのでコンソールを非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # アイコンファイルがある場合はここに指定
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WildlifeDetector',
)
'''
    
    with open('WildlifeDetector.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    logger.info("specファイルを作成しました: WildlifeDetector.spec")

def build_application():
    """アプリケーションのビルド"""
    logger.info("アプリケーションのビルドを開始します...")
    
    try:
        # PyInstallerコマンドの実行
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'WildlifeDetector.spec'
        ]
        
        logger.info(f"実行コマンド: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("ビルドが正常に完了しました")
            return True
        else:
            logger.error(f"ビルドエラー: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"ビルド中に例外が発生しました: {e}")
        return False

def create_installer_files():
    """インストーラー用ファイルの作成"""
    dist_dir = Path('dist/WildlifeDetector')
    
    if not dist_dir.exists():
        logger.error("distディレクトリが見つかりません")
        return False
    
    # READMEファイルの作成
    readme_content = """
Wildlife Detector - 野生生物検出アプリケーション
================================================

## 概要
Google SpeciesNetを使用した高精度な鳥類・哺乳類検出デスクトップアプリケーションです。

## 機能
- 数万枚規模の画像バッチ処理
- 94.5%の高精度種レベル分類
- CSV結果出力
- 画像の自動振り分け機能
- 使いやすいGUIインターフェース

## 使用方法
1. WildlifeDetector.exe を実行
2. 「入力・設定」タブで画像ファイルまたはフォルダを選択
3. 出力フォルダを指定
4. 「検出処理開始」をクリック
5. 「結果」タブで結果を確認
6. 必要に応じてCSV出力やファイル振り分けを実行

## システム要件
- Windows 10/11 (64bit)
- RAM: 4GB以上推奨
- ストレージ: 2GB以上の空き容量
- GPU: NVIDIA GPU (オプション、高速化のため)

## サポート
問題や質問がある場合は、開発チームまでお問い合わせください。

## ライセンス
このソフトウェアは野生生物研究および保護活動での使用を目的としています。
商用利用については別途ライセンスが必要です。

Powered by Google SpeciesNet
"""
    
    with open(dist_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # バッチファイルの作成（簡単起動用）
    batch_content = """@echo off
echo Wildlife Detector を起動しています...
WildlifeDetector.exe
pause
"""
    
    with open(dist_dir / 'start.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    logger.info("インストーラー用ファイルを作成しました")
    return True

def create_archive():
    """配布用アーカイブの作成"""
    dist_dir = Path('dist/WildlifeDetector')
    
    if not dist_dir.exists():
        logger.error("distディレクトリが見つかりません")
        return False
    
    try:
        import zipfile
        
        archive_name = 'WildlifeDetector_v1.0.0.zip'
        
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, dist_dir.parent)
                    zipf.write(file_path, arc_name)
        
        logger.info(f"配布用アーカイブを作成しました: {archive_name}")
        return True
        
    except Exception as e:
        logger.error(f"アーカイブ作成エラー: {e}")
        return False

def verify_build():
    """ビルド結果の検証"""
    exe_path = Path('dist/WildlifeDetector/WildlifeDetector.exe')
    
    if not exe_path.exists():
        logger.error("実行ファイルが見つかりません")
        return False
    
    # ファイルサイズチェック
    file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
    logger.info(f"実行ファイルサイズ: {file_size:.1f} MB")
    
    if file_size < 50:
        logger.warning("実行ファイルが小さすぎます。依存関係が不足している可能性があります")
    
    # その他の必要ファイルチェック
    dist_dir = exe_path.parent
    required_files = ['_internal']  # PyInstallerが作成するディレクトリ
    
    for item in required_files:
        if not (dist_dir / item).exists():
            logger.warning(f"必要なファイル/ディレクトリが見つかりません: {item}")
    
    logger.info("ビルド検証完了")
    return True

def main():
    """メイン関数"""
    logger.info("=" * 60)
    logger.info("Wildlife Detector ビルドスクリプト")
    logger.info("=" * 60)
    
    # 前提条件チェック
    if not check_pyinstaller():
        return 1
    
    # ビルドプロセス
    steps = [
        ("クリーンアップ", clean_build_directories),
        ("specファイル作成", create_spec_file),
        ("アプリケーションビルド", build_application),
        ("インストーラーファイル作成", create_installer_files),
        ("ビルド検証", verify_build),
        ("配布アーカイブ作成", create_archive),
    ]
    
    for step_name, step_func in steps:
        logger.info(f"\\n[{step_name}] 実行中...")
        
        if step_func():
            logger.info(f"[{step_name}] 完了")
        else:
            logger.error(f"[{step_name}] 失敗")
            return 1
    
    logger.info("\\n" + "=" * 60)
    logger.info("ビルドが正常に完了しました！")
    logger.info("配布ファイル:")
    logger.info("  - dist/WildlifeDetector/ (実行可能ディレクトリ)")
    logger.info("  - WildlifeDetector_v1.0.0.zip (配布用アーカイブ)")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())