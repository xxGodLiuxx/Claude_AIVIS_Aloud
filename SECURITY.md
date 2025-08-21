# Security Policy / セキュリティポリシー

## Reporting Security Vulnerabilities / 脆弱性の報告

**DO NOT** report security vulnerabilities through public GitHub issues.  
**セキュリティ脆弱性を公開のGitHub Issuesで報告しないでください。**

Instead, please send a report to:  
代わりに、以下の方法で報告してください：

1. Open a **private security advisory** on GitHub  
   GitHubで**プライベートセキュリティアドバイザリ**を開く
   
2. Include the following information / 以下の情報を含めてください:
   - Type of issue / 問題の種類
   - Affected files / 影響を受けるファイル
   - Impact assessment / 影響評価
   - Steps to reproduce / 再現手順
   - Possible fix / 可能な修正案

## Security Considerations / セキュリティ上の考慮事項

### File System Access / ファイルシステムアクセス

This tool monitors JSON files in the file system:  
このツールはファイルシステム内のJSONファイルを監視します：

- **Risk**: Potential access to sensitive files / **リスク**: 機密ファイルへのアクセス可能性
- **Mitigation**: Restricted to Claude Code directories / **対策**: Claude Codeディレクトリに制限
- **User Action**: Review file permissions / **ユーザー対応**: ファイル権限の確認

### Audio Output / 音声出力

- **Risk**: Sensitive information read aloud / **リスク**: 機密情報の音声読み上げ
- **Mitigation**: User awareness and volume control / **対策**: ユーザー認識と音量制御
- **User Action**: Use in private environments / **ユーザー対応**: プライベート環境での使用

### Network Communication / ネットワーク通信

Communication with AIVIS Speech Engine:  
AIVIS Speech Engineとの通信：

- **Port**: localhost:50021 (local only) / **ポート**: localhost:50021（ローカルのみ）
- **Risk**: Minimal (local communication) / **リスク**: 最小（ローカル通信）
- **Mitigation**: No external network access / **対策**: 外部ネットワークアクセスなし

## Known Security Limitations / 既知のセキュリティ制限

1. **JSON File Monitoring** / JSONファイル監視
   - Monitors all `.jsonl` files in specified directories
   - 指定ディレクトリ内のすべての`.jsonl`ファイルを監視
   
2. **No Encryption** / 暗号化なし
   - Text processed in plain text
   - テキストは平文で処理
   
3. **No Authentication** / 認証なし
   - No user authentication required
   - ユーザー認証不要

## Best Practices / ベストプラクティス

### For Users / ユーザー向け

1. **Environment** / 環境
   - Use in secure, private environments / 安全でプライベートな環境で使用
   - Be aware of who can hear the audio / 音声を聞ける人を意識
   
2. **Configuration** / 設定
   - Review `config.json` settings / `config.json`設定を確認
   - Limit file monitoring paths / ファイル監視パスを制限
   
3. **Updates** / 更新
   - Keep AIVIS Speech Engine updated / AIVIS Speech Engineを最新に保つ
   - Update this tool regularly / このツールを定期的に更新

### For Developers / 開発者向け

1. **Code Review** / コードレビュー
   - Review file access patterns / ファイルアクセスパターンを確認
   - Validate input data / 入力データの検証
   
2. **Dependencies** / 依存関係
   - Keep dependencies updated / 依存関係を最新に保つ
   - Review security advisories / セキュリティアドバイザリを確認
   
3. **Testing** / テスト
   - Test with restricted permissions / 制限された権限でテスト
   - Verify no unintended file access / 意図しないファイルアクセスがないことを確認

## Supported Versions / サポートバージョン

| Version | Supported | 
| ------- | --------- |
| 1.1.x   | ✅ Yes    |
| 1.0.x   | ✅ Yes    |
| < 1.0   | ❌ No     |

## Security Updates / セキュリティ更新

Security updates will be released as:  
セキュリティ更新は以下として公開されます：

- **Critical**: Immediate patch release / **重大**: 即座のパッチリリース
- **High**: Within 7 days / **高**: 7日以内
- **Medium**: Within 30 days / **中**: 30日以内
- **Low**: Next regular release / **低**: 次の定期リリース

## Disclaimer / 免責事項

This tool is provided "as is" without warranty. Users are responsible for:  
このツールは保証なしで「現状のまま」提供されます。ユーザーは以下に責任を負います：

- Evaluating security risks / セキュリティリスクの評価
- Implementing appropriate safeguards / 適切な保護措置の実装
- Compliance with regulations / 規制への準拠

## Contact / 連絡先

For security concerns, please use GitHub's security advisory feature.  
セキュリティに関する懸念事項は、GitHubのセキュリティアドバイザリ機能を使用してください。

---

Last updated: 2025-08-21  
最終更新: 2025年8月21日