# Claude AIVIS Aloud

Claude Codeの応答メッセージをAIVIS Speech Engineでリアルタイム朗読するツール

## 概要

Claude AIVIS Aloudは、Claude Code CLI（コマンドラインインターフェース）が生成するJSONファイルを監視し、応答メッセージをリアルタイムで音声朗読するツールです。

**主な特徴：**
- 📝 JSONファイルのリアルタイム監視による応答メッセージの即座の朗読
- 🧠 Think Hard Mode（思考モード）と通常応答で異なる音量設定（思考：0.5、通常：1.0）
- 🎯 日本語に特化した自然な読み上げ
- ⚡ 低遅延での音声生成
- 🔧 話者IDのカスタマイズ可能

## 重要な注意事項とリスク

### ⚠️ セキュリティ上の重要な警告

このツールは**JSONファイルをリアルタイム監視**する設計のため、以下のリスクがあります：

1. **ファイルアクセス権限**: システムの特定ディレクトリへの読み取りアクセスが必要
2. **プライバシー**: Claude Codeとのやり取りが音声として読み上げられます
3. **システムリソース**: 継続的なファイル監視によりCPU/メモリを消費します
4. **音声出力**: 周囲の環境によっては不適切な場合があります

**本ツールの使用は完全に自己責任でお願いします。**

## 動作要件

### 必須要件
- Windows 10/11（推奨）、macOS、Linux
- Python 3.8以上
- AIVIS Speech Engine（公式サイトより最新版をダウンロード推奨）
- メモリ: 2GB以上の空き容量
- Claude Code CLI環境

### AIVIS Speech Engineのインストール

1. [AIVIS Project公式サイト](https://aivis-project.com/)から最新版をダウンロード
2. インストーラーを実行してセットアップ
3. デフォルトポート（50021）でエンジンが起動することを確認

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/[your-username]/Claude_AIVIS_Aloud.git
cd Claude_AIVIS_Aloud

# 依存関係のインストール
pip install -r requirements.txt

# AIVIS Speech Engineを起動（別ターミナル）
# Windowsの場合: AivisSpeech.exeを実行
# その他: ドキュメント参照
```

## 使用方法

### 基本的な使用

```bash
# メインスクリプトの実行
python claude_aivis_aloud.py
```

### 設定のカスタマイズ

`config.json`で以下の設定が可能です：

```json
{
  "speaker_id": 2001,  // 話者ID（後述のカスタマイズガイド参照）
  "normal_volume": 1.0,  // 通常音量
  "thinking_volume": 0.5,  // Think Hard Mode時の音量
  "engine_host": "localhost",
  "engine_port": 50021
}
```

## 話者IDのカスタマイズ

AIVIS Speech Engineは複数の話者（ボイス）をサポートしています。

### 利用可能な話者の確認

```python
import requests
response = requests.get("http://localhost:50021/speakers")
speakers = response.json()
for speaker in speakers:
    print(f"ID: {speaker['id']}, Name: {speaker['name']}")
```

### 話者IDの変更

`config.json`の`speaker_id`を変更することで、お好みのボイスに切り替えできます：

- 2001: 標準的な女性ボイス（デフォルト）
- 2002: 落ち着いた女性ボイス
- その他: AIVIS Speech Engineのドキュメントを参照

## トラブルシューティング

### よくある問題と解決方法

1. **「エンジンに接続できません」エラー**
   - AIVIS Speech Engineが起動しているか確認
   - ポート番号（デフォルト: 50021）が正しいか確認
   - ファイアウォール設定を確認

2. **音声が再生されない**
   - システムの音量設定を確認
   - オーディオデバイスが正しく選択されているか確認
   - Pythonの`pygame`が正しくインストールされているか確認

3. **文字化けする**
   - UTF-8エンコーディングが正しく設定されているか確認
   - Windows環境の場合、コマンドプロンプトの文字コード設定を確認

## 謝辞

このプロジェクトは以下のオープンソースプロジェクトに深く感謝します：

- **[AIVIS Project](https://github.com/Aivis-Project)** - 素晴らしい日本語音声合成エンジンの開発・提供
  - [AivisSpeech Engine](https://github.com/Aivis-Project/AivisSpeech-Engine)
  - [AivisSpeech](https://github.com/Aivis-Project/AivisSpeech)
- **VOICEVOX Project** - AIVIS Speech Engineのベースとなったエンジン
- **Anthropic Claude** - 高度なAI対話システムの提供

特にAIVIS Projectチームには、日本語音声合成技術をオープンソースで提供していただいたことに心から感謝いたします。

## ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

ただし、AIVIS Speech Engine自体はLGPL-3.0ライセンスです。エンジンの利用に関しては、[AIVIS Projectのライセンス](https://github.com/Aivis-Project/AivisSpeech-Engine/blob/master/LICENSE)を必ず確認してください。

## 開発者

開発: JaH  
技術支援: Claude (Anthropic)

## サポート

問題報告やフィーチャーリクエストは[Issues](https://github.com/[your-username]/Claude_AIVIS_Aloud/issues)へお願いします。

## 更新履歴

- v1.0.0 (2025-08-21): 初回リリース
  - JSONファイルリアルタイム監視機能
  - Think Hard Mode対応（音量差異化）
  - 日本語特化の自然な読み上げ

---

**免責事項**: 本ツールは個人開発のツールであり、Anthropic社およびAIVIS Project公式とは無関係です。使用は自己責任でお願いします。