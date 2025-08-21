# 話者IDカスタマイズガイド

## 概要

AIVIS Speech Engineは複数の話者（ボイス）をサポートしており、お好みの声質に変更することができます。

## 利用可能な話者の確認方法

### 方法1: Pythonスクリプトで確認

```python
import requests
import json

# AIVIS Speech Engineが起動していることを確認してください
engine_url = "http://localhost:50021"

try:
    response = requests.get(f"{engine_url}/speakers")
    speakers = response.json()
    
    print("利用可能な話者一覧:")
    print("-" * 50)
    
    for speaker in speakers:
        print(f"話者名: {speaker['name']}")
        for style in speaker['styles']:
            print(f"  スタイルID: {style['id']}")
            print(f"  スタイル名: {style['name']}")
        print()
        
except Exception as e:
    print(f"エラー: {e}")
    print("AIVIS Speech Engineが起動していることを確認してください")
```

### 方法2: ブラウザで確認

AIVIS Speech Engineが起動している状態で、以下のURLにアクセス：
```
http://localhost:50021/speakers
```

## 話者IDの変更方法

### 1. config.jsonを編集

`config.json`ファイルの`voice.speaker_id`を変更します：

```json
{
  "voice": {
    "speaker_id": 2001,  // ← この値を変更
    ...
  }
}
```

### 2. スクリプト内で直接指定

```python
# claude_aivis_aloud.py内で直接変更する場合
SPEAKER_ID = 2001  # お好みの話者IDに変更
```

## 標準的な話者ID

AIVIS Speech Engineのデフォルトインストールで利用可能な一般的な話者ID：

| ID範囲 | 説明 | 特徴 |
|--------|------|------|
| 2001-2010 | 女性ボイス | 明るく親しみやすい声質 |
| 2011-2020 | 女性ボイス | 落ち着いた声質 |
| 2021-2030 | 男性ボイス | 低めの声質 |
| 2031+ | その他 | 特殊なキャラクターボイス |

※実際のIDは、インストールされているモデルによって異なります

## 音声パラメータの調整

話者IDの他に、以下のパラメータで音声をカスタマイズできます：

### config.json での設定

```json
{
  "voice": {
    "speaker_id": 2001,
    "speed": 1.0,         // 話速（0.5-2.0）
    "pitch": 0,           // 音高（-0.15～0.15）
    "intonation": 1.0,    // 抑揚（0-2.0）
    "normal_volume": 1.0, // 通常音量（0-2.0）
    "thinking_volume": 0.5 // 思考モード音量（0-2.0）
  }
}
```

### パラメータ説明

- **speed**: 話す速度。1.0が標準、0.5で半分の速度、2.0で2倍速
- **pitch**: 声の高さ。0が標準、正の値で高く、負の値で低く
- **intonation**: 抑揚の強さ。1.0が標準、値が大きいほど抑揚が強い
- **volume**: 音量。1.0が標準、0.5で半分の音量

## トラブルシューティング

### 話者が見つからない場合

1. AIVIS Speech Engineが起動していることを確認
2. 正しいポート番号（デフォルト: 50021）を使用していることを確認
3. 話者IDが正しいことを確認（利用可能な話者の確認方法を参照）

### 音声が変わらない場合

1. config.jsonの変更を保存したか確認
2. スクリプトを再起動
3. AIVIS Speech Engineのログを確認

## カスタムモデルの追加

AIVIS Speech Engineは、AIVMX形式のカスタムモデルをサポートしています。

### カスタムモデルの入手先

- [AivisHub](https://aivis-hub.com/) - コミュニティ製モデル
- [AIVIS Project公式](https://aivis-project.com/) - 公式モデル

### インストール方法

1. .aivmxファイルをダウンロード
2. AIVIS Speech Engineのモデルフォルダに配置
3. エンジンを再起動
4. 新しい話者IDを確認して使用

## 注意事項

- 話者IDはモデルによって異なるため、必ず事前に確認してください
- 一部のモデルは商用利用に制限がある場合があります
- カスタムモデル使用時は、各モデルのライセンスを確認してください

## サポート

話者カスタマイズに関する質問は、GitHubのIssuesでお気軽にお問い合わせください。