# 話者カスタマイズガイド

このガイドでは、AIVIS Speech Engineの話者（音声）をカスタマイズする公式の手順を説明します。

## 📋 目次

1. [基本概念](#基本概念)
2. [現在の話者を確認](#現在の話者を確認)
3. [新しい話者モデルの追加](#新しい話者モデルの追加)
4. [話者IDの設定](#話者idの設定)
5. [音声パラメータの調整](#音声パラメータの調整)
6. [トラブルシューティング](#トラブルシューティング)

## 基本概念

### 話者IDについて

AIVIS Speech Engineでは、各話者（音声モデル）は以下の識別子を持ちます：

- **speaker_id**: 実際に使用する数値ID（例：1325133120）
- **local_id**: 0-31の範囲の整数
- **UUID**: モデル固有の識別子
- **styles**: 各話者内の異なる話し方（ノーマル、ハッピー、サッド等）

## 現在の話者を確認

### 方法1: Pythonスクリプトで確認

以下のスクリプトを実行して、利用可能な話者の一覧を取得します：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list_speakers.py - AIVIS Speech Engine話者一覧取得ツール
"""

import requests
import json

def list_available_speakers():
    """利用可能な話者を一覧表示"""
    
    # AIVIS Speech Engineのデフォルトポート
    engine_url = "http://localhost:10101"
    
    try:
        # 話者一覧を取得
        response = requests.get(f"{engine_url}/speakers")
        response.raise_for_status()
        
        speakers = response.json()
        
        print("=" * 60)
        print("利用可能な話者一覧")
        print("=" * 60)
        
        for speaker in speakers:
            print(f"\n話者名: {speaker['name']}")
            print(f"UUID: {speaker.get('speaker_uuid', 'N/A')}")
            
            # 各スタイルのIDを表示
            if 'styles' in speaker:
                print("利用可能なスタイル:")
                for style in speaker['styles']:
                    print(f"  - ID: {style['id']}")
                    print(f"    スタイル名: {style['name']}")
                    print(f"    ※ config.jsonのspeaker_idに {style['id']} を設定")
            print("-" * 40)
            
    except requests.exceptions.ConnectionError:
        print("エラー: AIVIS Speech Engineに接続できません")
        print("以下を確認してください：")
        print("1. AIVIS Speech Engineが起動している")
        print("2. ポート10101で動作している")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    list_available_speakers()
```

### 方法2: ブラウザで確認

1. AIVIS Speech Engineを起動
2. ブラウザで以下のURLにアクセス：
   ```
   http://localhost:10101/speakers
   ```
3. JSON形式で話者一覧が表示されます

### 方法3: AIVIS Speech GUIから確認

1. AIVIS Speechアプリケーションを起動
2. 「音声」タブまたは設定から話者一覧を確認
3. 各話者の横に表示されるIDをメモ

## 新しい話者モデルの追加

### ステップ1: モデルの入手

1. **AivisHub**にアクセス
   - URL: https://hub.aivis-project.com/
   - 無料・有料の様々な音声モデルが公開されています

2. お好みの話者モデルを探す
   - ライセンスを確認（ACML、ACML-NC、CC0等）
   - サンプル音声を聴いて選択

3. `.aivmx`ファイルをダウンロード

### ステップ2: モデルのインストール

#### 🎯 推奨方法: AivisHubからインストール

1. **AivisHubで話者を選択**
   - [AivisHub](https://hub.aivis-project.com/)にアクセス
   - お好みの話者を選択（例：[花音](https://hub.aivis-project.com/aivm-models/a670e6b8-0852-45b2-8704-1bc9862f2fe6)）
   - URLをコピー

2. **AIVIS Speechでインストール**
   - AIVIS Speechアプリを起動
   - 「音声合成モデル追加」メニューを選択
   - コピーしたURLを入力
   - 自動的にダウンロードとインストールが実行されます

#### 別の方法A: ファイルからインストール

1. AivisHubから`.aivmx`ファイルをダウンロード
2. AIVIS Speechの「音声合成モデル追加」メニューを選択
3. ダウンロードした`.aivmx`ファイルを選択
4. 自動的にインストールされます

#### 方法C: 手動インストール（上級者向け）

1. ダウンロードした`.aivmx`ファイルを以下のフォルダに配置：
   ```
   Windows:
   C:\Users\[ユーザー名]\AppData\Roaming\AivisSpeech-Engine\Models\
   
   macOS:
   ~/Library/Application Support/AivisSpeech-Engine/Models/
   ```

2. AIVIS Speechを再起動

#### 方法D: APIでインストール（開発者向け）

```python
import requests

# モデルファイルのパス
model_path = "path/to/model.aivmx"

# APIエンドポイント
url = "http://localhost:10101/aivm_models/install"

# ファイルをアップロード
with open(model_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)
    
if response.status_code == 200:
    print("モデルのインストールに成功しました")
else:
    print(f"エラー: {response.text}")
```

### ステップ3: インストール確認

前述の「現在の話者を確認」の方法で、新しい話者が追加されたことを確認します。

## 話者IDの設定

### config.jsonでの設定

1. `list_speakers.py`を実行して話者IDを確認
2. `config.json`を編集：

```json
{
  "voice": {
    "speaker_id": 1325133120,  // ← ここに確認したIDを設定
    "speed": 1.0,
    "pitch": 0,
    "intonation": 1.0,
    "normal_volume": 1.0,
    "thinking_volume": 0.5
  }
}
```

### 重要な注意点

- **speaker_id**は各スタイルごとに異なります
- 同じ話者でも「ノーマル」「ハッピー」などのスタイルで異なるIDになります
- 必ず`/speakers`エンドポイントで正確なIDを確認してください

## 音声パラメータの調整

### 基本パラメータ

| パラメータ | 説明 | 範囲 | デフォルト |
|-----------|------|------|------------|
| `speed` | 話速 | 0.5～2.0 | 1.0 |
| `pitch` | 音高 | -0.15～0.15 | 0 |
| `intonation` | 抑揚 | 0～2.0 | 1.0 |
| `volume` | 音量 | 0～2.0 | 1.0 |

### 設定例

```json
{
  "voice": {
    "speaker_id": 1325133120,
    "speed": 1.2,           // 少し速め
    "pitch": 0.05,          // 少し高め
    "intonation": 1.3,      // 抑揚を強め
    "normal_volume": 1.0,   // 通常の音量
    "thinking_volume": 0.5  // 思考時は控えめ
  }
}
```

## トラブルシューティング

### 話者が見つからない

**症状**: 設定したspeaker_idでエラーが発生

**解決方法**:
1. `list_speakers.py`で利用可能なIDを再確認
2. AIVIS Speech Engineが起動していることを確認
3. モデルが正しくインストールされているか確認

### 音声が再生されない

**症状**: エラーはないが音声が聞こえない

**解決方法**:
1. システムの音量設定を確認
2. AIVIS Speech Engineのログを確認
3. 別の話者IDで試す

### モデルのインストールに失敗

**症状**: .aivmxファイルが認識されない

**解決方法**:
1. ファイルが破損していないか確認
2. 正しいフォルダに配置されているか確認
3. AIVIS Speech Engineを完全に再起動

### エンジンに接続できない

**症状**: Connection refused エラー

**解決方法**:
1. AIVIS Speech Engineが起動しているか確認
2. ポート10101が使用されていないか確認：
   ```bash
   # Windows
   netstat -an | findstr :10101
   
   # Mac/Linux
   lsof -i :10101
   ```
3. ファイアウォール設定を確認

## 参考リンク

- [AIVIS Project公式サイト](https://aivis-project.com/)
- [AivisHub（モデル配布サイト）](https://hub.aivis-project.com/)
- [AIVIS Speech Engine GitHub](https://github.com/Aivis-Project/AivisSpeech-Engine)
- [API ドキュメント](https://aivis-project.github.io/AivisSpeech-Engine/api/)

## ライセンスについて

- 各音声モデルには個別のライセンスが設定されています
- 商用利用の際は、各モデルのライセンスを必ず確認してください
- AivisHubでダウンロード時にライセンス表示があります

---

最終更新: 2025年8月21日