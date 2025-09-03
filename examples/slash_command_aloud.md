---
description: Claude AIVIS Aloud v3.2.3（全プロジェクト対応・自動認識）
allowed-tools: ["Bash"]
run_in_background: true
---

# Claude AIVIS Aloudを起動（全プロジェクト自動認識対応）
echo "[*] Starting Claude AIVIS Aloud v3.2.3..." && python /path/to/claude_aivis_aloud.py

# 使用方法:
# 1. /path/to/ を実際のファイルパスに置き換えてください
# 2. このファイルを ~/.claude/commands/aloud.md として保存してください  
# 3. Claude Code CLIで /aloud と入力すると音声読み上げが開始されます
# 4. 自動プロジェクト認識機能により、どのプロジェクトでも動作します
# 5. Claude Code CLI終了時に自動的に停止します