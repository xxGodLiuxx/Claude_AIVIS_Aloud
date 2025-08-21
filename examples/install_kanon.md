# 話者「花音」のインストール例

このガイドでは、AivisHubから「花音」をインストールする具体的な手順を説明します。

## 花音について

- **モデル名**: 花音（かのん）
- **AivisHub URL**: https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6
- **ライセンス**: モデルページで確認（通常はACML等）
- **特徴**: クリアで聴き取りやすい女性ボイス

## インストール手順

### 方法1: AIVIS Speech GUIから（推奨）

1. **AIVIS Speechを起動**
   - Windowsの場合: スタートメニューから「AIVIS Speech」を起動
   - macOSの場合: アプリケーションフォルダから起動

2. **音声合成モデル追加メニューを開く**
   - メニューバーから「音声合成モデル」→「モデル追加」を選択

3. **花音をインストール**
   - 方法A: URLを直接入力
     ```
     https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6
     ```
   - 方法B: AivisHubブラウザから検索して選択

4. **インストール完了を確認**
   - 話者一覧に「花音」が追加されることを確認

### 方法2: ブラウザ経由でダウンロード

1. **AivisHubにアクセス**
   ```
   https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6
   ```

2. **「ダウンロード」ボタンをクリック**
   - `.aivmx`ファイルがダウンロードされます

3. **AIVIS Speechでインストール**
   - AIVIS Speechを起動
   - 「音声合成モデル追加」メニューを選択
   - ダウンロードした`.aivmx`ファイルを選択

## 花音の話者IDを確認

インストール後、以下のコマンドで花音のIDを確認します：

```bash
python examples/list_speakers.py
```

出力例：
```
【花音】
UUID: a670e6b8-0852-45b2-8704-1bc9862f2fe6

利用可能なスタイル:
  ✓ スタイル: ノーマル
    ID: 1234567890
    → config.jsonに設定: "speaker_id": 1234567890
    
  ✓ スタイル: ハッピー
    ID: 1234567891
    → config.jsonに設定: "speaker_id": 1234567891
```

## config.jsonの設定

確認したIDを`config.json`に設定します：

```json
{
  "voice": {
    "speaker_id": 1234567890,  // 花音 - ノーマル
    "speed": 1.0,
    "pitch": 0,
    "intonation": 1.0,
    "normal_volume": 1.0,
    "thinking_volume": 0.5
  }
}
```

## 動作確認

設定後、Claude AIVIS Aloudを起動して動作を確認：

```bash
python claude_aivis_aloud.py
```

## トラブルシューティング

### 花音が表示されない場合

1. **AIVIS Speechを再起動**
   - 完全に終了してから再起動

2. **モデルファイルの確認**
   ```
   Windows:
   C:\Users\[ユーザー名]\AppData\Roaming\AivisSpeech-Engine\Models\
   ```
   上記フォルダに花音のモデルファイルがあることを確認

3. **エンジンのリロード**
   - AIVIS Speech内で「エンジン再起動」を実行

### IDが異なる場合

実際のIDは環境によって異なる場合があります。必ず`list_speakers.py`で確認してください。

## 他の話者モデル

AivisHubには多くの話者モデルが公開されています：
- https://hub.aivis-project.com/

同様の手順で、お好みの話者をインストールできます。

---

最終更新: 2025年8月21日