# Wildlife Detector

<div align="center">

![Wildlife Detector Logo](https://img.shields.io/badge/Wildlife-Detector-green.svg)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/w-udagawa/wildlife-detector-app.svg)](https://github.com/w-udagawa/wildlife-detector-app/issues)

**Google SpeciesNetを使用した高精度野生生物検出デスクトップアプリケーション**

[🚀 クイックスタート](#クイックスタート) • [📖 ドキュメント](#ドキュメント) • [🐛 Issues](https://github.com/w-udagawa/wildlife-detector-app/issues) • [💬 Discussions](https://github.com/w-udagawa/wildlife-detector-app/discussions)

</div>

## ✨ 特徴

- 🦅 **高精度検出**: Google SpeciesNetによる94.5%の種レベル分類精度
- ⚡ **大量処理**: 数万枚規模の画像バッチ処理対応
- 📊 **詳細分析**: CSV出力・統計情報・種別集計
- 📁 **自動整理**: 検出結果に基づく画像の自動フォルダ分類
- 🖥️ **使いやすいGUI**: 直感的なデスクトップインターフェース
- 🔧 **カスタマイズ可能**: 信頼度閾値・処理設定の詳細調整

## 🎯 対象ユーザー

- **野生生物研究者**: フィールド調査画像の自動分析
- **環境保護団体**: 生物多様性モニタリング
- **自然愛好家**: 撮影した野生生物の同定支援
- **教育機関**: 生物学教育・研究での活用

## 🚀 クイックスタート

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/w-udagawa/wildlife-detector-app.git
cd wildlife-detector-app

# 仮想環境の作成（推奨）
python -m venv wildlife_env
source wildlife_env/bin/activate  # Linux/Mac
# または
wildlife_env\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt

# 動作テスト
python test_app.py

# アプリケーション起動
python run_app.py
```

### 基本的な使用方法

1. **画像選択**: ファイルまたはフォルダを選択
2. **出力設定**: 結果の保存先を指定
3. **検出実行**: 「検出処理開始」をクリック
4. **結果確認**: CSV出力・画像振り分けを実行

詳細は [QUICKSTART.md](QUICKSTART.md) をご覧ください。

## 📊 検出可能な生物

### 鳥類 (2000種以上)
- スズメ (Passer montanus)
- ハシブトガラス (Corvus macrorhynchos)
- アオサギ (Ardea cinerea)
- ノスリ (Buteo buteo)
- など多数

### 哺乳類
- ニホンザル (Macaca fuscata)
- ニホンジカ (Cervus nippon)
- イノシシ (Sus scrofa)
- タヌキ (Nyctereutes procyonoides)
- キツネ (Vulpes vulpes)
- など多数

## 🏗️ プロジェクト構造

```
wildlife_detector/
├── core/                   # 検出エンジン
│   ├── config.py          # 設定管理
│   ├── species_detector.py # SpeciesNet統合
│   └── batch_processor.py # バッチ処理
├── gui/                   # ユーザーインターフェース
│   └── main_window.py     # メインGUI
├── utils/                 # ユーティリティ
│   ├── csv_exporter.py    # CSV出力
│   └── file_manager.py    # ファイル管理
└── main.py               # エントリーポイント
```

## 🔧 技術仕様

- **フレームワーク**: PySide6 (Qt6)
- **AI モデル**: Google SpeciesNet
- **言語**: Python 3.8+
- **パッケージング**: PyInstaller
- **対応OS**: Windows 10/11, macOS, Linux

## 📈 パフォーマンス

- **処理速度**: ~2秒/画像 (CPU), ~0.5秒/画像 (GPU)
- **検出精度**: 99.4% (動物検出), 94.5% (種分類)
- **メモリ使用量**: 2-4GB (設定により調整可能)

## 🤝 貢献

このプロジェクトへの貢献を歓迎します！

- 🐛 [バグ報告](https://github.com/w-udagawa/wildlife-detector-app/issues/new?template=bug_report.md)
- 💡 [機能要求](https://github.com/w-udagawa/wildlife-detector-app/issues/new?template=feature_request.md)
- 📝 [プルリクエスト](https://github.com/w-udagawa/wildlife-detector-app/pulls)

詳細は [CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

## 🙏 謝辞

- **Google SpeciesNet チーム**: 素晴らしいAIモデルの提供
- **野生生物研究コミュニティ**: 貴重なフィードバックと協力
- **オープンソースコミュニティ**: 使用しているライブラリの開発

## 📞 サポート

- 💬 [GitHub Discussions](https://github.com/w-udagawa/wildlife-detector-app/discussions)
- 🐛 [Issue Tracker](https://github.com/w-udagawa/wildlife-detector-app/issues)

## 🗺️ ロードマップ

- [ ] **v1.1**: リアルタイム動画処理
- [ ] **v1.2**: Web アプリケーション版
- [ ] **v1.3**: スマートフォンアプリ
- [ ] **v2.0**: カスタムモデル訓練機能

---

<div align="center">

**Wildlife Detector v1.0.0** | Powered by Google SpeciesNet

[⬆ トップに戻る](#wildlife-detector)

</div>
