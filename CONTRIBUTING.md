# Contributing to Claude AIVIS Aloud / 貢献ガイドライン

Thank you for your interest in contributing! / 貢献にご興味をお持ちいただきありがとうございます！

## Language / 言語

- Primary language: Japanese / 主要言語：日本語
- English contributions are also welcome / 英語での貢献も歓迎します
- Code comments: English preferred / コードコメント：英語推奨

## How to Contribute / 貢献方法

### 1. Reporting Issues / 問題の報告

- Use GitHub Issues / GitHub Issuesを使用してください
- Include:
  - Python version / Pythonバージョン
  - OS (Windows/macOS/Linux)
  - AIVIS Speech version / AIVIS Speechバージョン
  - Error messages / エラーメッセージ
  - Steps to reproduce / 再現手順

### 2. Suggesting Features / 機能提案

- Open a discussion in Issues / Issuesでディスカッションを開始
- Describe the use case / ユースケースを説明
- Consider compatibility with AIVIS Speech Engine / AIVIS Speech Engineとの互換性を考慮

### 3. Code Contributions / コード貢献

#### Before submitting / 提出前に

1. **Fork & Clone**
   ```bash
   git clone https://github.com/[your-username]/Claude_AIVIS_Aloud.git
   cd Claude_AIVIS_Aloud
   git checkout -b feature/your-feature-name
   ```

2. **Follow coding standards / コーディング規約**
   - UTF-8 encoding / UTF-8エンコーディング
   - PEP 8 for Python code / PythonコードはPEP 8準拠
   - Semantic versioning / セマンティックバージョニング

3. **Test your changes / 変更をテスト**
   ```bash
   # Run existing tests / 既存テストを実行
   python test_v316_simple.py
   
   # Test with AIVIS Speech Engine / AIVIS Speech Engineで動作確認
   python claude_aivis_aloud.py
   ```

4. **Document changes / 変更を文書化**
   - Update README if needed / 必要に応じてREADME更新
   - Add comments to complex code / 複雑なコードにコメント追加
   - Update version numbers / バージョン番号更新

#### Pull Request Process / プルリクエストプロセス

1. **Create PR with clear title / 明確なタイトルでPR作成**
   - Good: "Fix: ナンバリングリスト読み上げの修正"
   - Bad: "Fixed bug"

2. **PR Description Template / PR説明テンプレート**
   ```markdown
   ## 変更内容 / Changes
   - 
   
   ## 理由 / Reason
   - 
   
   ## テスト / Testing
   - [ ] AIVIS Speech Engineで動作確認
   - [ ] Windows環境でテスト
   - [ ] エンコーディング問題なし
   
   ## 関連Issue / Related Issue
   - #
   ```

3. **Review process / レビュープロセス**
   - Maintainer will review / メンテナがレビュー
   - May request changes / 変更依頼の可能性あり
   - Be patient / お待ちください

## Code Style / コードスタイル

### Python
```python
# Good example / 良い例
def process_text_for_speech(text: str) -> str:
    """
    Process text for natural speech synthesis.
    
    Args:
        text: Input text to process
        
    Returns:
        Processed text ready for TTS
    """
    # Implementation
    pass

# Bad example / 悪い例
def proc(t):
    # no docs
    pass
```

### Versioning / バージョニング

Follow semantic versioning / セマンティックバージョニング準拠:
- MAJOR.MINOR.PATCH (e.g., 1.1.0)
- MAJOR: Breaking changes / 破壊的変更
- MINOR: New features / 新機能
- PATCH: Bug fixes / バグ修正

## Important Notes / 重要事項

### AIVIS Project Respect / AIVIS Projectへの配慮

- Do not modify AIVIS Engine code / AIVIS Engineのコードを変更しない
- Follow AIVIS API specifications / AIVIS API仕様に準拠
- Credit AIVIS Project appropriately / AIVIS Projectを適切にクレジット

### Security / セキュリティ

- Never commit API keys / APIキーをコミットしない
- Review file permissions / ファイル権限を確認
- Report security issues privately / セキュリティ問題は非公開で報告

### Testing / テスト

Ensure compatibility with / 以下との互換性を確認:
- AIVIS Speech latest version / AIVIS Speech最新版
- Claude Code CLI / Claude Code CLI
- Windows 10/11
- Python 3.8+

## Community / コミュニティ

- Be respectful / 敬意を持って
- Help others / 他者を助ける
- Share knowledge / 知識を共有

## License / ライセンス

By contributing, you agree that your contributions will be licensed under MIT License.

貢献により、あなたの貢献物がMITライセンスの下でライセンスされることに同意したものとします。

## Questions? / 質問？

Open an issue or discussion / IssueまたはDiscussionを開いてください

---

Thank you for contributing! / 貢献ありがとうございます！ 🎉