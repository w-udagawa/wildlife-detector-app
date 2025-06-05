# Wildlife Detector - クイックスタートガイド

## 🚀 即座にアプリケーションを試す

### 1. 依存関係の確認とインストール

```bash
# リポジトリのクローン
git clone https://github.com/w-udagawa/wildlife-detector-app.git
cd wildlife-detector-app

# Pythonバージョン確認（3.8以上が必要）
python --version

# 仮想環境の作成（推奨）
python -m venv wildlife_env
source wildlife_env/bin/activate  # Linux/Mac
# または
wildlife_env\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 基本動作テスト

```bash
# テストスクリプトの実行
python test_app.py
```

全てのテストが成功すれば、アプリケーションは正常に動作します。

### 3. アプリケーションの起動

```bash
# 開発版の起動
python run_app.py

# または直接起動
python -m wildlife_detector.main
```

## 📋 使用手順

### ステップ1: 画像の準備
- 検出したい野生生物の画像を準備
- サポート形式: JPG, JPEG, PNG, BMP, TIFF
- 推奨: 高解像度（1024x1024以上）

### ステップ2: アプリケーション操作
1. **入力・設定タブ**
   - 「ファイルを選択」または「フォルダを選択」
   - 出力フォルダを指定
   - 必要に応じて設定を調整

2. **検出処理開始**
   - 「検出処理開始」ボタンをクリック
   - 処理進捗タブで進行状況を確認

3. **結果確認**
   - 結果タブで検出結果を確認
   - CSV出力やファイル振り分けを実行

## ⚙️ 主要設定

### 検出設定
- **信頼度閾値**: 0.1（低い値ほど多くの候補を検出）
- **バッチサイズ**: 32（メモリに応じて調整）
- **地域フィルター**: JPN（日本の野生生物に特化）

### パフォーマンス設定
- **最大ワーカー数**: 4（CPUコア数に応じて調整）
- **GPU使用**: 有効（NVIDIA GPU使用時）

## 🐛 トラブルシューティング

### よくある問題

**Q: テストで失敗する**
```bash
# 個別にパッケージをインストール
pip install PySide6 numpy pandas Pillow opencv-python
```

**Q: 「SpeciesNet がインストールされていません」警告**
- 正常です。モックアップモードで動作します
- 実際のSpeciesNetは以下でインストール（試験段階）:
```bash
pip install git+https://github.com/google/cameratrapai.git
```

**Q: GUI が起動しない**
- PySide6が正しくインストールされているか確認
- Windowsの場合、Microsoft Visual C++ Redistributableが必要な場合があります

**Q: 処理が遅い**
- バッチサイズを小さくする（16 or 8）
- 最大ワーカー数を減らす
- 画像サイズを制限

## 📁 出力ファイル説明

### CSV出力
- `wildlife_detection_results_YYYYMMDD_HHMMSS.csv`: 全検出結果
- `wildlife_detection_summary_YYYYMMDD_HHMMSS.csv`: 処理統計
- `wildlife_species_list_YYYYMMDD_HHMMSS.csv`: 検出種一覧

### ファイル振り分け
```
output_folder/
├── スズメ/           # 検出された種ごと
├── ハシブトガラス/
├── no_detection/     # 検出されなかった画像
└── multiple_species/ # 複数種が検出された画像
```

## 🔧 開発者向け

### ビルド（実行ファイル作成）
```bash
python build_app.py
```

### モジュール構造
```
wildlife_detector/
├── core/           # 検出エンジン
├── gui/            # ユーザーインターフェース  
└── utils/          # 出力・ファイル管理
```

## 📞 サポート

- 問題が発生した場合は `test_app.py` の結果を確認
- ログファイル: `%USERPROFILE%\WildlifeDetector\logs\wildlife_detector.log`
- GitHub Issues: https://github.com/w-udagawa/wildlife-detector-app/issues

---
**Wildlife Detector v1.0.0**  
Powered by Google SpeciesNet (Mock Mode)