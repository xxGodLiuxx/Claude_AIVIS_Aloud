# Claude AIVIS Aloud

Claude Codeの応答メッセージをAIVIS Speech Engineでリアルタイム朗読するツール

## 最新バージョン: v3.3.0 (2025-09-03)

### 🎉 v3.3.0 統合版の特徴
- エンタープライズ機能とJSONL監視強化の統合
- 6段階の明確なセッション切り替えプロセス
- バックグラウンド常駐モード対応（24時間連続稼働）
- スラッシュコマンド `/aloud` による簡単起動
- グレースフルシャットダウン実装

## 概要

Claude AIVIS Aloudは、Claude Code CLI（コマンドラインインターフェース）が生成するJSONLファイルを監視し、応答メッセージをリアルタイムで音声朗読するツールです。

**主な特徴：**
- 📝 JSONLファイルのリアルタイム監視による応答メッセージの即座の朗読
- 🧠 Think Hard Mode（思考モード）と通常応答で異なる音量設定（思考：0.5、通常：1.0）
- 🎯 日本語に特化した自然な読み上げ
- ⚡ 低遅延での音声生成
- 🔧 話者IDのカスタマイズ可能
- 🔄 セッション自動切り替え機能
- 💾 プロセス管理・PIDファイル対応

## 重要な注意事項とリスク

### ⚠️ セキュリティ上の重要な警告

このツールは**JSONLファイルをリアルタイム監視**する設計のため、以下のリスクがあります：

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
4. AIVIS Speech Engineがポート10101で自動起動することを確認

## インストール

### 方法1: GitHubからクローン

```bash
# リポジトリのクローン
git clone https://github.com/xxGodLiuxx/Claude_AIVIS_Aloud.git
cd Claude_AIVIS_Aloud

# 依存関係のインストール
pip install -r requirements.txt
```

### 方法2: 直接ダウンロード

最新版のスクリプトファイルを直接ダウンロード:
- [kanon_aloud_v3.2.1.py](https://github.com/xxGodLiuxx/Claude_AIVIS_Aloud/blob/main/kanon_aloud_v3.2.1.py)

## Claude Code CLIスラッシュコマンド設定（推奨）

### /aloudコマンドの設定

Claude Code CLIでスラッシュコマンドを使用すると、簡単に起動・常駐させることができます。

1. **設定ファイルの作成**
   
   `~/.claude/commands/aloud.md` を作成:

   ```markdown
   ---
   description: Claude AIVIS Aloud v3.2.1をバックグラウンド起動
   allowed-tools: ["Bash"]
   run_in_background: true
   ---

   python /path/to/kanon_aloud_v3.2.1.py
   ```

2. **使用方法**
   
   Claude Code CLI内で:
   ```
   /aloud
   ```

   これだけで音声読み上げが開始されます！

## 使用方法

### 基本的な使用

```bash
# 直接実行
python kanon_aloud_v3.2.1.py

# バックグラウンド実行（Windows）
start /B python kanon_aloud_v3.2.1.py

# バックグラウンド実行（Unix系）
nohup python kanon_aloud_v3.2.1.py &
```

### プロセス管理

```bash
# プロセス確認
# Windows
tasklist | findstr python

# Unix系
ps aux | grep kanon_aloud

# グレースフルシャットダウン（推奨）
# Windows
taskkill /PID <process_id>

# Unix系
kill -TERM $(cat ~/.claude/kanon_aloud.pid)

# 強制終了（非推奨）
kill -9 <process_id>
```

## 設定

### 主要設定項目（スクリプト内）

```python
# AivisSpeech Engine設定
AIVIS_BASE_URL = "http://127.0.0.1:10101"
AIVIS_SPEAKER_ID = 1325133120  # 話者ID

# 音量設定
VOLUME_NORMAL = 1.0     # 通常応答の音量
VOLUME_THINKING = 0.5   # Thinking部分の音量

# 朗読速度設定
NARRATION_SPEED_NORMAL = 1.0    # 通常朗読
NARRATION_SPEED_THINKING = 1.1  # 思考部分は少し速め
```

## 話者IDのカスタマイズ

AIVIS Speechは複数の話者（ボイス）をサポートしています。

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
   - スクリプト内の`AIVIS_SPEAKER_ID`を変更
   - 各話者のスタイル（ノーマル、ハッピー等）ごとに異なるIDがあります

## トラブルシューティング

### よくある問題と解決方法

1. **「エンジンに接続できません」エラー**
   - AIVIS Speech Engineが起動しているか確認
   - ポート番号（デフォルト: 10101）が正しいか確認
   - ファイアウォール設定を確認

2. **音声が再生されない**
   - システムの音量設定を確認
   - オーディオデバイスが正しく選択されているか確認
   - Pythonの`pygame`が正しくインストールされているか確認

3. **文字化けする**
   - UTF-8エンコーディングが正しく設定されているか確認
   - Windows環境の場合、コマンドプロンプトの文字コード設定を確認

4. **タイムアウトエラー**
   - Claude Code CLIでは`run_in_background: true`を設定
   - またはターミナルで直接バックグラウンド実行

## 長期運用のための機能

### v3.2.1での改善点

1. **メモリ管理**
   - deque maxlen設定による制限
   - ファイルハンドルの適切なクローズ
   - スレッド終了処理の最適化

2. **プロセス管理**
   - PIDファイル自動管理
   - 重複プロセス防止機能
   - シグナルハンドリング（SIGTERM/SIGINT/SIGBREAK）

3. **ログ管理**
   - 7日以上古いログの自動削除
   - ログローテーション機能

4. **エラーハンドリング**
   - 具体的な例外処理
   - リソース解放の保証

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

開発: オープンソースコミュニティ  
技術支援: Claude (Anthropic)

## サポート

問題報告やフィーチャーリクエストは[Issues](https://github.com/xxGodLiuxx/Claude_AIVIS_Aloud/issues)へお願いします。

## 更新履歴

詳細は[RELEASE_NOTES.md](RELEASE_NOTES.md)を参照してください。

### 最近のリリース

- **v3.2.1 (2025-08-27)**: Claude Code CLI最適化版
  - バックグラウンド実行サポート
  - グレースフルシャットダウン実装
  - プロセス管理強化（PIDファイル）
  - 長期運用対応（24時間連続稼働）
  - エラーハンドリング改善

- **v3.2.0 (2025-08-27)**: Windows安定動作版
  - セッション自動切り替え改善
  - ファイル監視の安定性向上

---

**免責事項**: 本ツールは個人開発のツールであり、Anthropic社およびAIVIS Project公式とは無関係です。使用は自己責任でお願いします。