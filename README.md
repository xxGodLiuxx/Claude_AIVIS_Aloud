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

### AIVIS Speechのインストール

1. [AIVIS Project公式サイト](https://aivis-project.com/)からAIVIS Speechをダウンロード
   - **重要**: GitHub版ではなく、必ず公式サイトからダウンロードしてください
   - Windows版またはmacOS版を選択
2. インストーラーを実行してセットアップ
3. 初回起動時にデフォルトの音声モデルが自動ダウンロードされます
4. AIVIS Speech Engineがポート50021で自動起動することを確認

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/JaH/Claude_AIVIS_Aloud.git
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

AIVIS Speechは複数の話者（ボイス）をサポートしています。詳細な手順は`docs/VOICE_CUSTOMIZATION.md`を参照してください。

### クイックスタート

1. **話者一覧の確認**
   ```bash
   python examples/list_speakers.py
   ```

2. **新しい話者の追加**
   - [AivisHub](https://hub.aivis-project.com/)から話者モデルを選択
   - 例: [花音](https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6)
   - AIVIS Speechの「音声合成モデル追加」メニューから追加
   - 詳細手順: `examples/install_kanon.md`参照

3. **話者IDの設定**
   - `config.json`の`speaker_id`に、確認したIDを設定
   - 各話者のスタイル（ノーマル、ハッピー等）ごとに異なるIDがあります

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

問題報告やフィーチャーリクエストは[Issues](https://github.com/JaH/Claude_AIVIS_Aloud/issues)へお願いします。

## 更新履歴

- v1.3.0 (2025-08-21): リアルタイム処理最適化
  - **重要な修正**: セッション切り替え時のメッセージスキップ問題を修正
  - リアルタイム応答性の向上（ファイル末尾から監視開始）
  - `skip_initial_messages`関数の改良（設定可能なスキップ数、デフォルト0）
  - 新規セッション開始時も含めて全メッセージを確実に読み上げ

- v1.2.0 (2025-08-21): Thinkingモード強化
  - Thinkingモードでのナンバリングリスト処理最適化
  - バレットポイントの読み上げ改善
  - 数字を含む読み上げの自然性向上

- v1.1.0 (2025-08-21): バグ修正版
  - ナンバリングリスト、時刻形式、大文字アルファベットの処理改善
  - 通常モードでの読み上げ最適化

- v1.0.0 (2025-08-21): 初回リリース
  - JSONファイルリアルタイム監視機能
  - Think Hard Mode対応（音量差異化）
  - 日本語特化の自然な読み上げ

---

**免責事項**: 本ツールは個人開発のツールであり、Anthropic社およびAIVIS Project公式とは無関係です。使用は自己責任でお願いします。