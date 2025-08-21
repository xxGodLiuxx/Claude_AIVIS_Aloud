# AIVIS Project配慮チェックリスト

## ✅ ライセンス関連

1. **LGPL-3.0への準拠**
   - ✅ APIクライアントとして使用（エンジン自体の改変なし）
   - ✅ READMEでLGPL-3.0ライセンスに言及
   - ✅ AIVIS Speech Engineのライセンスへのリンク提供

2. **クレジット表記**
   - ✅ README.mdの「謝辞」セクションで明確にクレジット
   - ✅ README_EN.mdでも同様にクレジット
   - ✅ 公式GitHubへのリンク提供
   - ✅ 公式サイトへのリンク提供

## ✅ 技術的配慮

1. **API使用方法**
   - ✅ 公式API仕様に準拠（ポート50021使用）
   - ✅ 2段階API呼び出しの正しい実装
   - ✅ エンジンの変更・改造なし

2. **推奨事項の遵守**
   - ✅ 公式サイトからのダウンロードを推奨
   - ✅ GitHub版ではなく公式版の使用を明記
   - ✅ AivisHubからのモデル取得方法を説明

## ✅ ドキュメント内の配慮

1. **README.md**
   ```markdown
   特にAIVIS Projectチームには、日本語音声合成技術を
   オープンソースで提供していただいたことに心から感謝いたします。
   ```

2. **CONTRIBUTING.md**
   ```markdown
   ### AIVIS Project Respect / AIVIS Projectへの配慮
   - Do not modify AIVIS Engine code / AIVIS Engineのコードを変更しない
   - Follow AIVIS API specifications / AIVIS API仕様に準拠
   - Credit AIVIS Project appropriately / AIVIS Projectを適切にクレジット
   ```

3. **免責事項**
   - ✅ 「非公式ツール」であることを明記
   - ✅ AIVIS Project公式とは無関係であることを明記

## ✅ 商用利用

- ✅ AIVIS側：商用利用可能（クレジット不要）
- ✅ 本ツール：MITライセンスで公開（互換性あり）

## ✅ モデル利用ガイド

- ✅ AivisHubへのリンク提供
- ✅ 花音を例としたインストール手順
- ✅ 各モデルのライセンス確認を促す記述

## 判定：配慮は十分です ✅

### 理由：

1. **適切なクレジット表記**
   - 謝辞セクションで感謝を表明
   - 公式リンクを複数箇所に配置

2. **技術的な正確性**
   - API仕様に準拠
   - 公式推奨の使用方法を遵守

3. **法的配慮**
   - ライセンス互換性の確保
   - 非公式ツールであることの明示

4. **コミュニティへの貢献**
   - 使いやすいツールの提供
   - AIVIS Speechの普及に貢献

## 追加推奨事項（任意）

もしさらに配慮を示したい場合：

1. **AIVIS Projectへの寄付リンク追加**（もしあれば）
2. **AIVIS Projectのイベント・アップデート情報の共有**
3. **バグ発見時のAIVIS Projectへの報告**

---

最終確認日: 2025年8月21日