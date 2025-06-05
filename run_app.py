"""
Wildlife Detector 開発用起動スクリプト
"""

import sys
import os
from pathlib import Path

def main():
    """メイン関数"""
    print("Wildlife Detector - 開発版起動中...")
    
    # プロジェクトルートをパスに追加
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        # アプリケーションのメイン関数をインポートして実行
        from wildlife_detector.main import main as app_main
        return app_main()
        
    except ImportError as e:
        print(f"エラー: 必要なモジュールがインストールされていません")
        print(f"詳細: {e}")
        print("\n以下のコマンドで依存関係をインストールしてください:")
        print("pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())