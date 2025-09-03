# クイックスタートガイド

Claude AIVIS Aloudを5分で動かすための最短手順です。

## 📋 前提条件

- Windows 10/11 または macOS
- Python 3.8以上がインストール済み
- Claude Code CLIがインストール済み

## 🚀 セットアップ手順

### 1. AIVIS Speechをインストール（2分）

1. [AIVIS Project公式サイト](https://aivis-project.com/)にアクセス
2. 「ダウンロード」から自分のOSに合ったバージョンをダウンロード
3. インストーラーを実行
4. AIVIS Speechを起動（初回起動時に基本モデルが自動ダウンロードされます）

### 2. Claude AIVIS Aloudをセットアップ（1分）

```bash
# リポジトリをクローン
git clone https://github.com/xxGodLiuxx/Claude_AIVIS_Aloud.git
cd Claude_AIVIS_Aloud

# 必要なパッケージをインストール
pip install -r requirements.txt
```

### 3. 話者を選択（2分）

#### 🎯 推奨方法：AivisHubから話者をダウンロード

1. [AivisHub](https://hub.aivis-project.com/)にアクセス
2. お好みの話者を選択（例：[花音](https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6)）
3. AIVIS Speechの「音声合成モデル追加」でURLを入力してインストール
4. インストール後、以下のコマンドで話者IDを確認：
   ```bash
   python examples/list_speakers.py
   ```

#### 別の方法：デフォルト話者のIDを確認

デフォルトの話者を使用する場合：

```bash
# 利用可能な話者を確認
python examples/list_speakers.py
```

表示されたIDをメモします。

### 4. 設定ファイルを編集（1分）

`config.json`を開いて、確認したIDを設定：

```json
{
  "voice": {
    "speaker_id": 1325133120,  // ← 確認したIDを入力
    ...
  }
}
```

### 5. 実行

```bash
# Claude AIVIS Aloudを起動
python claude_aivis_aloud.py
```

これで準備完了です！Claude Code CLIを使用すると、応答が自動的に音声で読み上げられます。

## 🎤 推奨：花音をインストール

より自然な音声を使いたい場合は、「花音」がおすすめです：

1. AIVIS Speechの「音声合成モデル追加」メニューを開く
2. 以下のURLを入力：
   ```
   https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6
   ```
3. インストール完了後、`python examples/list_speakers.py`で花音のIDを確認
4. `config.json`を更新

## ❓ うまくいかない場合

### AIVIS Speech Engineが見つからない

```
エラー: AIVIS Speech Engineに接続できません
```

**解決方法**: AIVIS Speechアプリが起動していることを確認してください。

### 話者が見つからない

```
話者が見つかりません
```

**解決方法**: 
1. AIVIS Speechを再起動
2. 初回起動時のモデルダウンロードが完了するまで待つ

### 音声が聞こえない

**解決方法**:
1. システムの音量を確認
2. AIVIS Speechの音量設定を確認
3. `config.json`の`normal_volume`が1.0になっているか確認

## 📚 詳細情報

- [話者カスタマイズガイド](docs/VOICE_CUSTOMIZATION.md)
- [花音のインストール手順](examples/install_kanon.md)
- [トラブルシューティング](README.md#トラブルシューティング)

## 💬 サポート

問題が解決しない場合は、[GitHub Issues](https://github.com/xxGodLiuxx/Claude_AIVIS_Aloud/issues)でお問い合わせください。

---

Happy Coding with Voice! 🎵