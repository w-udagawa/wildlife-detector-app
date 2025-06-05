"""
Wildlife Detector テストスクリプト
基本的な動作確認とデバッグ用
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """必要なモジュールのインポートテスト"""
    print("=" * 50)
    print("インポートテスト開始")
    print("=" * 50)
    
    try:
        print("✓ 基本Pythonモジュール:")
        import numpy as np
        print(f"  - numpy: {np.__version__}")
        
        import pandas as pd
        print(f"  - pandas: {pd.__version__}")
        
        from PIL import Image
        print(f"  - Pillow: {Image.__version__}")
        
        print("\n✓ Wildlife Detectorモジュール:")
        from wildlife_detector.core.config import ConfigManager, AppConfig
        print("  - config module: OK")
        
        from wildlife_detector.core.species_detector import SpeciesDetector, DetectionResult
        print("  - species_detector module: OK")
        
        from wildlife_detector.core.batch_processor import BatchProcessor
        print("  - batch_processor module: OK")
        
        from wildlife_detector.utils.csv_exporter import CSVExporter
        print("  - csv_exporter module: OK")
        
        from wildlife_detector.utils.file_manager import FileManager
        print("  - file_manager module: OK")
        
        print("\n✓ GUIモジュール:")
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6 import __version__ as pyside_version
            print(f"  - PySide6: {pyside_version}")
            
            from wildlife_detector.gui.main_window import MainWindow
            print("  - main_window module: OK")
        except ImportError as e:
            print(f"  - PySide6 エラー: {e}")
            return False
        
        print("\n全てのインポートテストが成功しました！")
        return True
        
    except ImportError as e:
        print(f"\n❌ インポートエラー: {e}")
        return False

def test_config():
    """設定管理テスト"""
    print("\n" + "=" * 50)
    print("設定管理テスト")
    print("=" * 50)
    
    try:
        from wildlife_detector.core.config import ConfigManager, AppConfig
        
        # デフォルト設定の作成
        config = AppConfig.get_default()
        print(f"✓ デフォルト設定作成: batch_size={config.batch_size}")
        
        # 設定マネージャーの作成
        config_manager = ConfigManager("test_config.json")
        loaded_config = config_manager.load_config()
        print(f"✓ 設定ロード: confidence_threshold={loaded_config.confidence_threshold}")
        
        # 設定変更と保存
        config_manager.update_config(batch_size=16, confidence_threshold=0.2)
        save_result = config_manager.save_config()
        print(f"✓ 設定保存: {save_result}")
        
        # クリーンアップ
        if os.path.exists("test_config.json"):
            os.remove("test_config.json")
        
        print("設定管理テストが成功しました！")
        return True
        
    except Exception as e:
        print(f"❌ 設定管理テストエラー: {e}")
        return False

def test_species_detector():
    """種検出器テスト"""
    print("\n" + "=" * 50)
    print("種検出器テスト")
    print("=" * 50)
    
    try:
        from wildlife_detector.core.config import AppConfig
        from wildlife_detector.core.species_detector import SpeciesDetector
        
        # 検出器の作成と初期化
        config = AppConfig.get_default()
        detector = SpeciesDetector(config)
        
        init_result = detector.initialize()
        print(f"✓ 検出器初期化: {init_result}")
        
        # モデル情報の取得
        model_info = detector.get_model_info()
        print(f"✓ モデル情報: {model_info}")
        
        # サポート種数の確認
        supported_species = detector.get_supported_species()
        print(f"✓ サポート種数: {len(supported_species)}")
        
        if supported_species:
            print(f"  例: {supported_species[:3]}")
        
        # クリーンアップ
        detector.cleanup()
        print("✓ クリーンアップ完了")
        
        print("種検出器テストが成功しました！")
        return True
        
    except Exception as e:
        print(f"❌ 種検出器テストエラー: {e}")
        return False

def test_csv_exporter():
    """CSV出力テスト"""
    print("\n" + "=" * 50)
    print("CSV出力テスト")
    print("=" * 50)
    
    try:
        from wildlife_detector.utils.csv_exporter import CSVExporter
        from wildlife_detector.core.species_detector import DetectionResult
        
        # テスト用出力ディレクトリ
        test_output_dir = "test_output"
        os.makedirs(test_output_dir, exist_ok=True)
        
        # CSVエクスポーターの作成
        exporter = CSVExporter(test_output_dir)
        print("✓ CSVエクスポーター作成")
        
        # テスト用検出結果の作成
        test_detections = [
            {
                'species': 'Passer montanus',
                'common_name': 'スズメ',
                'scientific_name': 'Passer montanus',
                'confidence': 0.95,
                'category': 'bird',
                'bbox': [10, 20, 100, 150]
            }
        ]
        
        test_result = DetectionResult("test_image.jpg", test_detections)
        results = [test_result]
        
        # CSV出力テスト
        csv_path = exporter.export_results(results, "test_results.csv")
        print(f"✓ CSV出力: {csv_path}")
        
        # ファイル存在確認
        if os.path.exists(csv_path):
            print("✓ CSVファイル作成確認")
        
        # クリーンアップ
        import shutil
        if os.path.exists(test_output_dir):
            shutil.rmtree(test_output_dir)
        
        print("CSV出力テストが成功しました！")
        return True
        
    except Exception as e:
        print(f"❌ CSV出力テストエラー: {e}")
        return False

def test_gui_creation():
    """GUI作成テスト（非表示）"""
    print("\n" + "=" * 50)
    print("GUI作成テスト")
    print("=" * 50)
    
    try:
        from PySide6.QtWidgets import QApplication
        from wildlife_detector.gui.main_window import MainWindow
        
        # QApplicationの作成
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("✓ QApplication作成")
        
        # メインウィンドウの作成（表示はしない）
        main_window = MainWindow()
        print("✓ MainWindow作成")
        
        # ウィンドウタイトルの確認
        title = main_window.windowTitle()
        print(f"✓ ウィンドウタイトル: {title}")
        
        # タブ数の確認
        tab_count = main_window.tab_widget.count()
        print(f"✓ タブ数: {tab_count}")
        
        # クリーンアップ
        main_window.close()
        
        print("GUI作成テストが成功しました！")
        return True
        
    except Exception as e:
        print(f"❌ GUI作成テストエラー: {e}")
        return False

def main():
    """メインテスト関数"""
    print("Wildlife Detector テストスクリプト")
    print("=" * 50)
    
    tests = [
        ("インポートテスト", test_imports),
        ("設定管理テスト", test_config),
        ("種検出器テスト", test_species_detector),
        ("CSV出力テスト", test_csv_exporter),
        ("GUI作成テスト", test_gui_creation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} で予期しないエラー: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print("=" * 50)
    print(f"✓ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"合計: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 全てのテストが成功しました！")
        print("アプリケーションは正常に動作する準備ができています。")
        return 0
    else:
        print(f"\n⚠️  {failed}個のテストが失敗しました。")
        print("問題を修正してから再度テストしてください。")
        return 1

if __name__ == "__main__":
    sys.exit(main())