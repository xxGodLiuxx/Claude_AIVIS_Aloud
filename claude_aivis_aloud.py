#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude AIVIS Aloud v4.0.0
Claude Code Desktop support with full Japanese narration
- Tool use, thinking, user input confirmation in natural Japanese
- Volume: Normal 0.3, Thinking/Tool 0.1
- Subagent JSONL exclusion, 100+ term dictionary
Based on v3.2.3
"""

import json
import time
import re
import os
import sys
import logging
import codecs
from glob import glob
from pathlib import Path
from datetime import datetime
from collections import deque
import hashlib
import threading
import queue
import subprocess
import signal
import atexit
import requests
import pygame
from urllib.parse import quote

# Windows environment UTF-8 force settings
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Log settings
log_dir = Path(__file__).parent / "logs" / "aloud"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"kanon_aloud_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('claude_aivis')

# ===============================
# Global variables and settings
# ===============================
_processed_messages = deque(maxlen=100)  # Duplicate prevention
_speech_queue = queue.Queue()  # Simple FIFO queue
_speech_thread = None
_stop_flag = threading.Event()
_cancel_current = threading.Event()  # v4.0: Cancel low-priority speech when normal text arrives
_max_runtime = 3600 * 24  # 24 hours max runtime
_start_time = None

# AivisSpeech Engine settings
AIVIS_BASE_URL = "http://127.0.0.1:10101"
AIVIS_SPEAKER_ID = 1325133120
AIVIS_MAX_LENGTH = 500
AIVIS_OPTIMAL_LENGTH = 300

# Narration speed settings for natural reading
NARRATION_SPEED_NORMAL = 1.0  # 通常朗読
NARRATION_SPEED_THINKING = 1.1  # 思考部分は少し速め
NARRATION_PAUSE_SENTENCE = 0.5  # 文末の間
NARRATION_PAUSE_PARAGRAPH = 0.8  # 段落間の間

# Volume settings for differentiation (v4.0)
VOLUME_NORMAL = 0.3  # 通常の応答の音量
VOLUME_THINKING = 0.1  # Thinking・ツール部分の音量

# Dynamic file switching settings
CHECK_INTERVAL = 10  # seconds (new session check interval)

# Debug settings (Default False for faster startup)
DEBUG_TEST_VOICE = False  # True: Enable test voice, False: Silent mode (recommended)

# ===============================
# Log cleanup function
# ===============================
def cleanup_old_logs(retention_days=7):
    """Remove log files older than retention_days"""
    try:
        log_dir = Path(__file__).parent / "logs" / "aloud"
        if not log_dir.exists():
            return
        
        deleted_count = 0
        current_time = time.time()
        
        # Find and delete old log files
        for log_file in log_dir.glob("kanon_aloud_*.log"):
            try:
                file_time = os.path.getmtime(log_file)
                age_days = (current_time - file_time) / (24 * 3600)
                
                if age_days > retention_days:
                    log_file.unlink()
                    deleted_count += 1
            except Exception:
                pass  # Ignore individual file deletion errors
        
        if deleted_count > 0:
            logger.info(f"[Cleanup] Deleted {deleted_count} old log files (>{retention_days} days)")
    except Exception as e:
        logger.warning(f"[Cleanup] Log cleanup error: {e}")

# ===============================
# Duplicate process prevention
# ===============================
def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    logger.info(f"[Signal] Received signal {signum}, initiating graceful shutdown...")
    _stop_flag.set()
    sys.exit(0)

def cleanup_at_exit():
    """Cleanup function called at exit"""
    logger.info("[Exit] Performing cleanup...")
    _stop_flag.set()
    
    # Clean up PID file
    pid_file = Path.home() / '.claude' / 'kanon_aloud.pid'
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                stored_pid = int(f.read().strip())
                if stored_pid == os.getpid():
                    pid_file.unlink()
                    logger.info("[Exit] Removed PID file")
        except Exception:
            pass  # Ignore PID file cleanup errors

def cleanup_duplicate_processes():
    """Terminate all existing kanon_aloud processes at startup"""
    current_pid = os.getpid()
    logger.info(f"[Cleanup] Current PID: {current_pid}")
    
    try:
        # Use PowerShell command to detect duplicate processes
        ps_command = """
        Get-WmiObject Win32_Process | Where-Object {
            $_.ProcessId -ne %d -and 
            $_.Name -eq 'python.exe' -and 
            ($_.CommandLine -like '*kanon_aloud*' -or $_.CommandLine -like '*claude_aivis_aloud*')
        } | ForEach-Object { $_.ProcessId }
        """ % current_pid
        
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split()
            for pid in pids:
                try:
                    os.kill(int(pid), 9)
                    logger.info(f"[Cleanup] Terminated duplicate process: PID {pid}")
                except (OSError, ValueError):
                    pass  # Process already terminated
        
        # Clean up lock files
        lock_file = Path.home() / '.claude' / 'kanon_aloud.lock'
        pid_file = Path.home() / '.claude' / 'kanon_aloud.pid'
        
        if lock_file.exists():
            lock_file.unlink()
            logger.debug("[Cleanup] Removed lock file")
        
        if pid_file.exists():
            pid_file.unlink()
            logger.debug("[Cleanup] Removed PID file")
        
        # Create new PID file
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(current_pid))
        
    except Exception as e:
        logger.warning(f"[Cleanup] Error during cleanup: {e}")

# ===============================
# Speech worker (simplified)
# ===============================
def speech_worker_simple():
    """
    Speech worker with cancel support (v4.0)
    Low-volume speech (thinking/tool) is cancelled when normal text arrives.
    """
    import io

    pygame.mixer.init(frequency=24000, size=-16, channels=1)

    logger.info("[SpeechWorker] Worker started (v4.0 with cancel support)")

    while not _stop_flag.is_set():
        try:
            item = _speech_queue.get(timeout=1.0)

            if item is None:  # Termination signal
                break

            if len(item) == 3:
                text, speed, volume = item
            else:
                text, speed = item
                volume = VOLUME_NORMAL

            is_low_priority = (volume < VOLUME_NORMAL)

            # v4.0: If this is normal-volume text, cancel any in-progress low-priority speech
            if not is_low_priority:
                _cancel_current.set()
                # Brief wait for current playback to stop
                time.sleep(0.05)
                pygame.mixer.stop()
                _cancel_current.clear()
                # Drain remaining low-priority items from queue
                drained = 0
                while not _speech_queue.empty():
                    try:
                        peek = _speech_queue.get_nowait()
                        if peek is None:
                            _speech_queue.put(None)  # Re-add termination signal
                            break
                        p_vol = peek[2] if len(peek) == 3 else VOLUME_NORMAL
                        if p_vol >= VOLUME_NORMAL:
                            # Keep normal-volume items — put back
                            _speech_queue.put(peek)
                            break
                        drained += 1
                        _speech_queue.task_done()
                    except queue.Empty:
                        break
                if drained > 0:
                    logger.info(f"[SpeechWorker] Cancelled {drained} low-priority items")

            logger.info(f"[SpeechWorker] Processing: {len(text)} chars (vol:{volume})")

            if len(text) > AIVIS_MAX_LENGTH:
                chunks = split_text_naturally(text, AIVIS_OPTIMAL_LENGTH)

                for i, chunk in enumerate(chunks, 1):
                    if _stop_flag.is_set():
                        break
                    # v4.0: Cancel low-priority speech if signalled
                    if is_low_priority and _cancel_current.is_set():
                        logger.info("[SpeechWorker] Low-priority speech cancelled")
                        break

                    speak_single_chunk(chunk, speed, volume)

                    if i < len(chunks):
                        if '。。' in chunk:
                            time.sleep(NARRATION_PAUSE_PARAGRAPH)
                        else:
                            time.sleep(NARRATION_PAUSE_SENTENCE)
            else:
                speak_single_chunk(text, speed, volume)

            logger.info("[SpeechWorker] Reading completed")
            _speech_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"[SpeechWorker] Error: {e}")
            try:
                _speech_queue.task_done()
            except ValueError:
                pass

def speak_single_chunk(text, speed, volume=1.0):
    """
    Read a single chunk reliably with volume control (v3.1.4)
    """
    import io
    
    try:
        # Generate AudioQuery with proper URL encoding
        encoded_text = quote(text, safe='')
        query_response = requests.post(
            f"{AIVIS_BASE_URL}/audio_query?speaker={AIVIS_SPEAKER_ID}&text={encoded_text}",
            timeout=10
        )
        
        if query_response.status_code != 200:
            logger.error(f"AudioQuery failed: {query_response.status_code}")
            return False
        
        audio_query = query_response.json()
        audio_query['speedScale'] = speed
        audio_query['volumeScale'] = volume  # v3.1.4: Apply volume setting
        
        # Synthesize audio
        response = requests.post(
            f"{AIVIS_BASE_URL}/synthesis?speaker={AIVIS_SPEAKER_ID}",
            json=audio_query,
            timeout=20
        )
        
        if response.status_code == 200:
            audio_data = io.BytesIO(response.content)
            sound = pygame.mixer.Sound(audio_data)
            channel = sound.play()
            
            # Wait until finished reading (v4.0: also check cancel signal)
            if channel:
                while channel.get_busy() and not _stop_flag.is_set() and not _cancel_current.is_set():
                    pygame.time.wait(10)
                if _cancel_current.is_set() and channel.get_busy():
                    channel.stop()
            
            return True
        else:
            logger.error(f"Synthesis failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Speak error: {e}")
        return False

def enqueue_speech_simple(text, speed=1.0, volume=1.0):
    """
    Add to simple queue with volume control (v3.1.4)
    """
    global _speech_thread
    
    if not text or len(text) < 1:
        return
    
    # Start worker thread
    if _speech_thread is None or not _speech_thread.is_alive():
        _stop_flag.clear()
        _speech_thread = threading.Thread(
            target=speech_worker_simple,
            daemon=True
        )
        _speech_thread.start()
        time.sleep(0.5)
    
    # Add to simple queue with volume parameter
    _speech_queue.put((text, speed, volume))
    
    logger.info(f"[Queue] Added: {len(text)} chars (vol:{volume}, queue_size:{_speech_queue.qsize()})")

# ===============================
# Text processing functions
# ===============================
def split_text_naturally(text, max_length=AIVIS_OPTIMAL_LENGTH):
    """Split text at natural positions (for full reading)"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    
    # Split by paragraphs first
    if '。。' in text:
        paragraphs = text.split('。。')
        current_chunk = ""
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            if len(para) > max_length:
                # Split by sentences
                sentences = para.split('。')
                for sent in sentences:
                    if not sent.strip():
                        continue
                    
                    if len(sent) > max_length:
                        # Further split by commas
                        parts = sent.split('、')
                        for part in parts:
                            if len(current_chunk) + len(part) < max_length:
                                current_chunk += part + '、'
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk.rstrip('、'))
                                current_chunk = part + '、'
                    elif len(current_chunk) + len(sent) < max_length:
                        current_chunk += sent + '。'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sent + '。'
            else:
                if len(current_chunk) + len(para) < max_length:
                    current_chunk += para + '。。'
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para + '。。'
        
        if current_chunk:
            chunks.append(current_chunk)
    else:
        # Split by sentences
        sentences = text.split('。')
        current_chunk = ""
        
        for sent in sentences:
            if not sent.strip():
                continue
            
            if len(current_chunk) + len(sent) < max_length:
                current_chunk += sent + '。'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent + '。'
        
        if current_chunk:
            chunks.append(current_chunk)
    
    return chunks

def process_thinking_for_narration(thinking_text):
    """Convert thinking to clean Japanese narration (v4.1)

    Strategy:
    - If mostly Japanese: light cleanup, return as-is
    - If mostly English: translate key sentences, strip all remaining English
    """
    text = thinking_text.strip()
    if not text:
        return None

    # Japanese character count
    jp_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)
    jp_ratio = len(jp_chars) / max(len(text), 1)

    if jp_ratio > 0.3:
        # Mostly Japanese — light cleanup
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'[A-Za-z_/\\]{10,}', '', text)
        text = re.sub(r'(\d+)\.(\s*)', r'\1、', text)
        text = re.sub(r'^[\-•·*]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n+', '、', text)
        text = re.sub(r'\s+', ' ', text)
        # Remove remaining short English
        text = re.sub(r'\b[a-zA-Z]{1,5}\b', '', text)
        text = re.sub(r'[、。]{2,}', '。', text)
        text = text.strip('、。 ')
        if len(text) > 150:
            text = text[:150]
        return text if text else None

    # English thinking -> extract intent as Japanese
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Sentence-level English->Japanese patterns
    _patterns = [
        (r"(?i)the user (?:wants?|is asking|asked)(?: me)? to\s+(.+)", "ユーザーの依頼"),
        (r"(?i)i need to\s+(.+)", "必要な作業あり"),
        (r"(?i)i should\s+(.+)", "方針を検討中"),
        (r"(?i)let me (?:check|look|examine|verify|confirm)\b", "確認中"),
        (r"(?i)let me (?:think|consider)\b", "考え中"),
        (r"(?i)(?:first|next),?\s", "手順を整理中"),
        (r"(?i)the (?:issue|problem|bug|error) is\b", "問題を特定中"),
        (r"(?i)this (?:means|indicates|suggests)\b", "分析中"),
        (r"(?i)i(?:'ll| will) (?:try|attempt)\b", "試行中"),
        (r"(?i)looking at\b", "調査中"),
        (r"(?i)i can see\b", "把握しました"),
        (r"(?i)(?:so|therefore|in summary),?\s", "まとめ中"),
        (r"(?i)(?:done|complete|finished)\b", "完了"),
        (r"(?i)(?:fix|修正|update|更新)\b", "修正を検討中"),
        (r"(?i)(?:now|then)\s+(?:i|let)\b", "次の手順へ"),
    ]

    # Extract unique Japanese action labels from patterns that match
    actions = []
    seen = set()
    for line in lines[:15]:
        for pat, action_jp in _patterns:
            if re.search(pat, line) and action_jp not in seen:
                actions.append(action_jp)
                seen.add(action_jp)
                break

    if not actions:
        return "考え中"

    # Join unique actions, max 3
    result = '。'.join(actions[:3])
    return result


def _file_type_label(filepath):
    """Return human-friendly Japanese file type label from extension"""
    ext = os.path.splitext(filepath)[1].lower() if filepath else ''
    _ext_map = {
        '.py': 'パイソンファイル', '.js': 'スクリプトファイル',
        '.ts': 'スクリプトファイル', '.json': '設定ファイル',
        '.md': 'ドキュメント', '.txt': 'テキストファイル',
        '.log': 'ログファイル', '.yaml': '設定ファイル',
        '.yml': '設定ファイル', '.toml': '設定ファイル',
        '.html': 'ウェブページ', '.css': 'スタイルシート',
        '.sh': 'シェルスクリプト', '.bat': 'バッチファイル',
        '.csv': 'データファイル', '.xml': '設定ファイル',
        '.jsonl': 'ログファイル', '.lock': 'ロックファイル',
        '.pid': 'プロセスファイル', '.env': '環境設定',
    }
    return _ext_map.get(ext, 'ファイル')


def _desc_to_japanese(desc):
    """Convert English description keyword to concise Japanese action phrase"""
    if not desc:
        return None
    d = desc.lower().strip()
    # Keyword-based mapping for common description patterns
    _kw = [
        (['clone'], 'リポジトリをクローン'),
        (['install', 'pip', 'npm', 'package'], 'パッケージをインストール'),
        (['push'], 'リモートにプッシュ'),
        (['pull'], 'リモートからプル'),
        (['commit'], 'コミットを作成'),
        (['merge'], 'ブランチをマージ'),
        (['checkout', 'switch branch'], 'ブランチを切り替え'),
        (['diff'], '差分を確認'),
        (['log', 'history'], '履歴を確認'),
        (['status'], 'ステータスを確認'),
        (['start', 'launch', 'run', 'restart'], 'プロセスを起動'),
        (['stop', 'kill', 'terminate'], 'プロセスを停止'),
        (['verify', 'check', 'confirm', 'validate'], '確認'),
        (['test'], 'テストを実行'),
        (['build', 'compile'], 'ビルドを実行'),
        (['search', 'find', 'scan', 'grep'], '検索'),
        (['list'], '一覧を取得'),
        (['save', 'write', 'create', 'generate'], '保存'),
        (['read', 'load', 'fetch', 'get'], '読み込み'),
        (['update', 'modify', 'edit', 'fix', 'patch'], '更新'),
        (['delete', 'remove', 'clean'], '削除'),
        (['debug'], 'デバッグ'),
        (['deploy'], 'デプロイ'),
        (['auth'], '認証を確認'),
        (['privacy'], 'プライバシーを確認'),
        (['format'], 'フォーマットを整理'),
    ]
    for keywords, jp in _kw:
        if any(kw in d for kw in keywords):
            return jp
    return None


def process_tool_use_for_narration(tool_name, tool_input):
    """Convert tool_use to specific, concise Japanese (v4.1)

    No filenames or paths. Use description when available for specificity.
    """
    if not isinstance(tool_input, dict):
        tool_input = {}

    desc = tool_input.get('description', '')

    if tool_name == 'Bash':
        cmd = tool_input.get('command', '')
        # Try description first for specificity
        jp_desc = _desc_to_japanese(desc)
        if jp_desc:
            return jp_desc
        # Fallback: infer from command content
        if 'git push' in cmd:
            return "リモートにプッシュ"
        if 'git pull' in cmd:
            return "リモートからプル"
        if 'git commit' in cmd or 'git add' in cmd:
            return "コミットを作成"
        if 'git diff' in cmd:
            return "差分を確認"
        if 'git log' in cmd:
            return "履歴を確認"
        if 'git status' in cmd:
            return "ステータスを確認"
        if 'git clone' in cmd:
            return "リポジトリをクローン"
        if 'git ' in cmd:
            return "ギット操作を実行"
        if 'pip ' in cmd:
            return "パッケージをインストール"
        if 'npm ' in cmd or 'yarn ' in cmd:
            return "パッケージをインストール"
        if 'grep ' in cmd or 'findstr' in cmd:
            return "テキストを検索"
        if 'taskkill' in cmd or 'kill ' in cmd:
            return "プロセスを停止"
        if 'tasklist' in cmd or 'ps ' in cmd:
            return "プロセスを確認"
        if 'curl ' in cmd or 'wget ' in cmd:
            return "ネットワーク通信"
        if 'python' in cmd or 'node ' in cmd:
            return "スクリプトを実行"
        if 'ls ' in cmd or 'dir ' in cmd:
            return "ファイル一覧を取得"
        if 'cat ' in cmd or 'head ' in cmd or 'tail ' in cmd:
            return "ファイルを確認"
        if 'mkdir ' in cmd:
            return "フォルダを作成"
        if 'rm ' in cmd or 'del ' in cmd:
            return "ファイルを削除"
        if 'cp ' in cmd or 'mv ' in cmd:
            return "ファイルを移動"
        if 'sleep ' in cmd:
            return "待機中"
        if 'gh ' in cmd:
            return "ギットハブ操作"
        return "コマンドを実行"

    if tool_name == 'Read':
        fp = tool_input.get('file_path', '')
        return f"{_file_type_label(fp)}を読み取り"

    if tool_name == 'Write':
        fp = tool_input.get('file_path', '')
        return f"{_file_type_label(fp)}を作成"

    if tool_name == 'Edit':
        fp = tool_input.get('file_path', '')
        return f"{_file_type_label(fp)}を編集"

    if tool_name == 'Glob':
        return "ファイルを検索"

    if tool_name == 'Grep':
        return "コード内を検索"

    if tool_name == 'Agent':
        return "サブエージェントを起動"

    if tool_name == 'TodoWrite':
        return "タスクを更新"

    if tool_name == 'Skill':
        return "スキルを実行"

    if tool_name == 'WebSearch':
        return "ウェブを検索"

    if tool_name == 'WebFetch':
        return "ウェブページを取得"

    if 'notion' in tool_name.lower():
        return "ノーションにアクセス"

    if 'gmail' in tool_name.lower():
        return "メールを確認"

    if 'preview' in tool_name.lower():
        return "プレビューを操作"

    return "ツールを実行します"

def process_text_for_narration(text):
    """Convert text for natural narration experience (v4.0: enhanced Japanese)"""
    # Process code blocks with surrounding whitespace
    text = re.sub(r'\n*```[\s\S]*?```\n*', '。コード部分があります。', text)

    # v4.0: Remove inline code backticks and clean their contents
    # Long code fragments -> just say "コード"
    text = re.sub(r'`[^`]{40,}`', 'コード部分', text)
    # Short inline code -> remove backticks, let term replacement handle it
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # v4.0: Remove URLs
    text = re.sub(r'https?://\S+', '', text)

    # v4.0: Remove file paths entirely (user requested no filenames/dirs)
    text = re.sub(r'[A-Z]:\\[^\s,。、]+', '', text)
    text = re.sub(r'/[a-z][^\s,。、]{5,}', '', text)

    # v4.0: Apply term dictionary BEFORE identifier removal
    # so known English words get translated instead of deleted
    _early_replacements = {
        'operation': '操作', 'enqueue': 'エンキュー', 'Desktop': 'デスクトップ',
        'function': '関数', 'variable': '変数', 'parameter': 'パラメーター',
        'argument': '引数', 'callback': 'コールバック', 'listener': 'リスナー',
        'handler': 'ハンドラー', 'generate': '生成', 'process': 'プロセス',
        'monitor': 'モニター', 'session': 'セッション', 'message': 'メッセージ',
        'response': '応答', 'narration': '読み上げ', 'thinking': '思考',
        'assistant': 'アシスタント', 'permission': '許可', 'detection': '検出',
        'duplicate': '重複', 'prevention': '防止', 'processing': '処理',
        'monitoring': '監視', 'switching': '切り替え', 'connection': '接続',
        'compatible': '互換', 'compatibility': '互換性',
        'notification': '通知', 'confirmation': '確認',
        'initialize': '初期化', 'configure': '設定', 'implement': '実装',
        'replacement': '置換', 'conversion': '変換',
    }
    for old, new in _early_replacements.items():
        # Use lookaround that works with Japanese characters (not just \b)
        text = re.sub(rf'(?<![a-zA-Z]){old}(?![a-zA-Z])', new, text, flags=re.IGNORECASE)

    # v4.0: Remove standalone English identifiers (snake_case, camelCase)
    text = re.sub(r'\b[a-z_][a-z0-9_]{8,}\b', '', text)
    text = re.sub(r'\b[a-z]+[A-Z][a-zA-Z]+\b', '', text)

    # Convert file extensions to Japanese (more natural)
    text = re.sub(r'(\w+)\.py\b', r'\1ファイル', text)
    text = re.sub(r'(\w+)\.js\b', r'\1スクリプト', text)
    text = re.sub(r'(\w+)\.json\b', r'\1設定ファイル', text)
    text = re.sub(r'(\w+)\.md\b', r'\1文書', text)
    text = re.sub(r'(\w+)\.txt\b', r'\1テキスト', text)
    text = re.sub(r'(\w+)\.log\b', r'\1ログ', text)
    
    # Remove emojis and symbols
    emojis = ['✅', '❌', '⚠️', '📊', '🎯', '💡', '🔧', '📝']
    for emoji in emojis:
        text = text.replace(emoji, '')
    
    # Remove decoration symbols
    text = re.sub(r'[=\-─━]{3,}', '', text)
    text = re.sub(r'[#]{2,}', '', text)
    text = re.sub(r'[\*]{2,}', '', text)
    
    # Process bullet points and numbering lists (v3.1.6: fixed)
    # Remove bullet markers
    text = re.sub(r'^- (.+?)$', r'\1', text, flags=re.MULTILINE)
    # Convert numbered lists to natural reading format (1. -> 1、)
    # v3.1.6: More flexible pattern that works with indents and inline
    text = re.sub(r'(\d+)\.(\s*)', r'\1、', text)
    
    # Improved line break processing
    # Double line breaks become single periods (paragraph breaks)
    text = re.sub(r'\n\n+', '。', text)
    # Single line breaks become commas (line breaks within paragraphs)
    text = re.sub(r'\n', '、', text)
    
    # v3.1.5: Convert brackets to periods for clearer audio separation
    text = re.sub(r'[（(]', '。', text)
    text = re.sub(r'[）)]', '。', text)
    text = re.sub(r'[「『]', '。', text)
    text = re.sub(r'[」』]', '。', text)
    
    # v3.1.6: Process datetime formats for natural reading
    # SESSION_YYYYMMDD_HHMMSS_NNNNNN format
    text = re.sub(
        r'SESSION_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})_\d+',
        lambda m: f'セッション {int(m.group(1))}年{int(m.group(2))}月{int(m.group(3))}日 {int(m.group(4))}時{int(m.group(5))}分{int(m.group(6))}秒',
        text
    )
    
    # ISO format YYYY-MM-DDTHH:MM:SS
    text = re.sub(
        r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})',
        lambda m: f'{int(m.group(1))}年{int(m.group(2))}月{int(m.group(3))}日 {int(m.group(4))}時{int(m.group(5))}分{int(m.group(6))}秒',
        text
    )
    
    # Normal datetime format YYYY-MM-DD HH:MM:SS
    text = re.sub(
        r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})',
        lambda m: f'{int(m.group(1))}年{int(m.group(2))}月{int(m.group(3))}日 {int(m.group(4))}時{int(m.group(5))}分{int(m.group(6))}秒',
        text
    )
    
    # Time only HH:MM:SS
    text = re.sub(
        r'(\d{2}):(\d{2}):(\d{2})',
        lambda m: f'{int(m.group(1))}時{int(m.group(2))}分{int(m.group(3))}秒',
        text
    )
    
    # Convert technical terms to more natural Japanese
    replacements = {
        'TODO': 'タスク',
        'API': 'エーピーアイ',
        'URL': 'アドレス',
        'JSON': 'ジェイソン',
        'JSONL': 'ジェイソンエル',
        'HTML': 'エイチティーエムエル',
        'CSS': 'スタイルシート',
        'CLI': 'コマンドライン',
        'Desktop': 'デスクトップ',
        'ID': 'アイディー',
        'PID': 'プロセスアイディー',
        'OK': 'オーケー',
        'NG': 'エヌジー',
        'FIFO': 'ファイフォ',
        # Common development terms
        'error': 'エラー',
        'warning': '警告',
        'info': '情報',
        'debug': 'デバッグ',
        'git': 'ギット',
        'commit': 'コミット',
        'push': 'プッシュ',
        'pull': 'プル',
        'branch': 'ブランチ',
        'file': 'ファイル',
        'folder': 'フォルダ',
        'update': '更新',
        'create': '作成',
        'delete': '削��',
        'edit': '編集',
        'read': '読み取り',
        'write': '書き込み',
        'install': 'インストール',
        'clone': 'クローン',
        'process': 'プロセス',
        'queue': 'キュー',
        'operation': '操作',
        'message': 'メッセージ',
        'role': 'ロール',
        'content': 'コンテンツ',
        'assistant': 'アシスタント',
        'user': 'ユーザー',
        'tool': 'ツール',
        'result': '結果',
        'type': 'タイプ',
        'thinking': '思考',
        'narration': '読み上げ',
        'volume': '音量',
        'script': 'スクリプト',
        'code': 'コード',
        'version': 'バージョン',
        'config': '設定',
        'log': 'ログ',
        'path': 'パス',
        'pattern': 'パターン',
        'response': '応答',
        'request': 'リクエスト',
        'chars': '文字',
        'string': '文字列',
        'permission': '許可',
        'denied': '拒否',
        'rejected': '拒否',
        'operation': '操作',
        'enqueue': 'エンキュー',
        'dequeue': 'デキュー',
        'Desktop': 'デスクトップ',
        'monitor': 'モニター',
        'session': 'セッション',
        'startup': 'スタートアップ',
        'shutdown': 'シャットダウン',
        'thread': 'スレッド',
        'worker': 'ワーカー',
        'timeout': 'タイムアウト',
        'retry': 'リトライ',
        'chunk': 'チャンク',
        'hash': 'ハッシュ',
        'token': 'トークン',
        'parser': 'パーサー',
        'plugin': 'プラグイン',
        'callback': 'コールバック',
        'input': '入力',
        'output': '出力',
        'function': '関数',
        'method': 'メソッド',
        'class': 'クラス',
        'variable': '変数',
        'parameter': 'パラメーター',
        'argument': '引数',
        'return': '戻り値',
        'module': 'モジュール',
        'import': 'インポート',
        'export': 'エクスポート',
        'test': 'テスト',
        'build': 'ビルド',
        'deploy': 'デプロイ',
        'server': 'サーバー',
        'client': 'クライアント',
        'agent': 'エージェント',
        'hook': 'フック',
        'event': 'イベント',
        'handler': 'ハンドラー',
        'listener': 'リスナー',
        'stream': 'ストリーム',
        'buffer': 'バッファー',
        'cache': 'キャッシュ',
        'stack': 'スタック',
        'queue': 'キュー',
        'array': '配列',
        'object': 'オブジェクト',
        'null': 'ヌル',
        'true': 'トゥルー',
        'false': 'フォルス',
        'status': 'ステータス',
        'check': 'チェック',
        'verify': '検証',
        'validate': '検証',
        'parse': '解析',
        'render': 'レンダリング',
        'compile': 'コンパイル',
        'execute': '実行',
        'launch': '起動',
        'stop': '停止',
        'start': '開始',
        'run': '実行',
        'running': '実行中',
        'failed': '失敗',
        'success': '成功',
        'complete': '完了',
        'pending': '保留中',
        'active': 'アクティブ',
        'enabled': '有効',
        'disabled': '無効',
    }
    
    # Apply replacements (case-insensitive, JP-boundary-aware)
    for old, new in replacements.items():
        text = re.sub(rf'(?<![a-zA-Z]){old}(?![a-zA-Z])', new, text, flags=re.IGNORECASE)
    
    # v3.1.6: Convert uppercase alphabet sequences to katakana
    # This handles acronyms not in the dictionary
    def convert_uppercase_to_katakana(match):
        alphabet_dict = {
            'A': 'エー', 'B': 'ビー', 'C': 'シー', 'D': 'ディー',
            'E': 'イー', 'F': 'エフ', 'G': 'ジー', 'H': 'エイチ',
            'I': 'アイ', 'J': 'ジェイ', 'K': 'ケー', 'L': 'エル',
            'M': 'エム', 'N': 'エヌ', 'O': 'オー', 'P': 'ピー',
            'Q': 'キュー', 'R': 'アール', 'S': 'エス', 'T': 'ティー',
            'U': 'ユー', 'V': 'ブイ', 'W': 'ダブリュー', 'X': 'エックス',
            'Y': 'ワイ', 'Z': 'ゼット'
        }
        result = ''
        for char in match.group(0):
            if char in alphabet_dict:
                result += alphabet_dict[char]
            else:
                result += char
        return result
    
    # Convert sequences of 2 or more uppercase letters
    text = re.sub(r'\b[A-Z]{2,}\b', convert_uppercase_to_katakana, text)

    # v4.0: Remove remaining English words that weren't in the dictionary
    # Remove isolated English words (4+ chars remaining after replacements)
    text = re.sub(r'\b[a-zA-Z]{4,}\b', '', text)
    # Remove very short leftovers (1-3 letter English fragments)
    text = re.sub(r'(?<![ァ-ヶー])\b[a-zA-Z]{1,3}\b(?![ァ-ヶー])', '', text)

    # Clean up consecutive punctuation
    text = re.sub(r'。+', '。', text)  # Multiple periods to single
    text = re.sub(r'、+', '、', text)  # Multiple commas to single
    text = re.sub(r'。、', '。', text)  # Period followed by comma to just period
    text = re.sub(r'、。', '。', text)  # Comma followed by period to just period
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing punctuation artifacts
    text = re.sub(r'^[、。\s]+', '', text)

    return text.strip()

def test_voice_system():
    """Check AivisSpeech Engine operation (optimized for fast startup)"""
    import io
    
    test_text = "音声システム動作確認です"
    
    try:
        query_response = requests.post(
            f"{AIVIS_BASE_URL}/audio_query?speaker={AIVIS_SPEAKER_ID}&text={test_text}",
            timeout=5
        )
        
        if query_response.status_code != 200:
            return False
        
        audio_query = query_response.json()
        audio_query['speedScale'] = 1.1
        
        response = requests.post(
            f"{AIVIS_BASE_URL}/synthesis?speaker={AIVIS_SPEAKER_ID}",
            json=audio_query,
            timeout=10
        )
        
        if response.status_code == 200:
            # Only play test sound if DEBUG_TEST_VOICE is True
            if DEBUG_TEST_VOICE:
                pygame.mixer.init(frequency=24000, size=-16, channels=1)
                audio_data = io.BytesIO(response.content)
                sound = pygame.mixer.Sound(audio_data)
                channel = sound.play()
                
                if channel:
                    while channel.get_busy():
                        pygame.time.wait(10)
                
                logger.info("AivisSpeech Engine is running (with test voice)")
            else:
                logger.info("AivisSpeech Engine is running (silent check)")
            
            return True
            
    except Exception as e:
        logger.error(f"Voice test error: {e}")
        return False

def generate_message_id(data):
    """Generate unique message ID"""
    key_parts = []

    if 'message' in data:
        msg = data['message']
        content_str = str(msg.get('content', ''))[:100]
        key_parts.append(content_str)
        key_parts.append(msg.get('role', ''))

    # queue-operation support
    if data.get('type') == 'queue-operation':
        key_parts.append(data.get('operation', ''))
        key_parts.append(str(data.get('content', ''))[:50])

    # Add timestamp if available
    if 'timestamp' in data:
        key_parts.append(str(data['timestamp']))

    id_str = '_'.join(filter(None, key_parts))
    return hashlib.md5(id_str.encode()).hexdigest()[:16]

def find_latest_jsonl():
    """Find the latest JSONL file (excludes subagent files)"""
    patterns = [
        str(Path.home() / '.claude' / 'projects' / '**' / '*.jsonl'),
    ]

    all_files = []
    for pattern in patterns:
        files = glob(pattern, recursive=True)
        all_files.extend(files)

    # Exclude subagent JSONL files to avoid duplicate reading
    all_files = [f for f in all_files if 'subagents' not in f]

    if not all_files:
        logger.error("JSONL file not found")
        return None

    latest = max(all_files, key=lambda x: os.path.getmtime(x))
    logger.info(f"Found JSONL: {latest}")
    return latest

def skip_initial_messages(file_handle, skip_count=0):
    """Skip initial messages (v3.1.8: configurable, default 0)"""
    skipped_count = 0
    for _ in range(skip_count):  # v3.1.8: Default 0 to avoid missing messages
        line = file_handle.readline()
        if not line:
            break
        try:
            data = json.loads(line)
            msg_id = generate_message_id(data)
            _processed_messages.append(msg_id)
            skipped_count += 1
        except json.JSONDecodeError:
            pass  # Skip invalid JSON lines
    
    if skipped_count > 0:
        logger.info(f"[Monitor] Skipped {skipped_count} initial messages")
    return skipped_count

def monitor_and_speak():
    """
    Dynamic file switching supported version (v3.2.0)
    Improved file monitoring for Windows stability
    Uses tail -f like behavior for reliable message detection
    """
    global _speech_thread
    
    # Start speech worker
    if _speech_thread is None or not _speech_thread.is_alive():
        _stop_flag.clear()
        _speech_thread = threading.Thread(
            target=speech_worker_simple,
            daemon=True
        )
        _speech_thread.start()
    
    # State management variables
    current_file = None
    current_handle = None
    last_check = 0
    file_position = 0  # Track file position for proper tail behavior
    known_files = set()  # Track known JSONL files to detect truly new sessions
    
    # Initial file selection
    current_file = find_latest_jsonl()
    if not current_file:
        logger.error("No JSONL file found at startup")
        return
    
    # Initialize known files with all existing files (exclude subagents)
    patterns = [
        str(Path.home() / '.claude' / 'projects' / '**' / '*.jsonl'),
    ]
    for pattern in patterns:
        files = glob(pattern, recursive=True)
        known_files.update(f for f in files if 'subagents' not in f)
    
    logger.info(f"[Monitor] Initial file: {os.path.basename(current_file)}")
    logger.info(f"[Monitor] Tracking {len(known_files)} existing JSONL files")
    logger.info(f"[Monitor] Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"[Monitor] Auto session detection: ENABLED")
    logger.info("="*70)
    logger.info("Claude AIVIS Aloud v3.2.3")
    logger.info("Features:")
    logger.info("  - Simple FIFO queue (no priority system)")
    logger.info("  - No hook event processing")
    logger.info("  - Assistant messages: Full text reading")
    logger.info("  - Dynamic file switching: Auto-detect new sessions")
    logger.info("  - Duplicate process prevention")
    logger.info("="*70)
    
    try:
        while not _stop_flag.is_set():
            # Periodic new session check (v3.2.0: only detect truly new files)
            now = time.time()
            if now - last_check > CHECK_INTERVAL:
                # Find all current JSONL files (exclude subagents)
                patterns = [
                    str(Path.home() / '.claude' / 'projects' / '**' / '*.jsonl'),
                ]
                all_current_files = set()
                for pattern in patterns:
                    files = glob(pattern, recursive=True)
                    all_current_files.update(f for f in files if 'subagents' not in f)
                
                # Check for truly new files (not in known_files)
                new_files = all_current_files - known_files
                
                if new_files:
                    # New session detected - switch to the newest file
                    latest_file = max(new_files, key=lambda x: os.path.getctime(x) if os.path.exists(x) else 0)
                    known_files.update(new_files)  # Add new files to known set
                    
                    logger.info(f"[NEW SESSION] {os.path.basename(latest_file)} detected")
                    logger.info(f"[SESSION SWITCH] {os.path.basename(current_file) if current_file else 'None'} -> {os.path.basename(latest_file)}")
                    
                    # 1. Close old handle
                    if current_handle:
                        current_handle.close()
                        logger.debug("Closed old file handle")
                    
                    # 2. Open new file
                    current_file = latest_file
                    current_handle = open(current_file, 'r', encoding='utf-8', errors='ignore')
                    
                    # 3. Set start position (v3.2.0: proper tail -f behavior)
                    # Start from last 10KB for context, but avoid duplicates
                    current_handle.seek(0, 2)
                    file_size = current_handle.tell()
                    start_pos = max(0, file_size - 10240)  # Last 10KB
                    current_handle.seek(start_pos)
                    if start_pos > 0:
                        current_handle.readline()  # Skip partial line
                    file_position = current_handle.tell()
                    
                    # 4. Clear processed message IDs
                    _processed_messages.clear()
                    logger.debug("Cleared processed message cache")
                    
                    # 5. Skip initial messages (v3.1.8: don't skip on session switch)
                    # skip_initial_messages(current_handle)  # Disabled to avoid missing messages
                    
                    # 6. Voice notification with clear announcement
                    enqueue_speech_simple("新しいセッションが始まりました。", speed=NARRATION_SPEED_NORMAL, volume=VOLUME_NORMAL)
                    
                    logger.info(f"[Monitor] Now monitoring: {os.path.basename(current_file)}")
                
                last_check = now
            
            # Handle file deletion
            if current_file and not os.path.exists(current_file):
                logger.warning(f"[Monitor] File deleted: {os.path.basename(current_file)}")
                if current_handle:
                    current_handle.close()
                current_handle = None
                current_file = None
                _processed_messages.clear()
                continue
            
            # Handle uninitialized file handle
            if not current_handle and current_file:
                current_handle = open(current_file, 'r', encoding='utf-8', errors='ignore')
                
                # Set start position (v3.2.0: proper tail -f behavior)
                # Start from last 10KB for initial context
                current_handle.seek(0, 2)
                file_size = current_handle.tell()
                start_pos = max(0, file_size - 10240)  # Last 10KB
                current_handle.seek(start_pos)
                if start_pos > 0:
                    current_handle.readline()  # Skip partial line
                file_position = current_handle.tell()
                
                # Skip initial messages (v3.1.8: skip only on initial startup)
                # skip_initial_messages(current_handle)  # Disabled to avoid missing messages
                
                logger.info(f"[Monitor] Opened file: {os.path.basename(current_file)}")
            
            # Normal read processing (v3.2.0: improved for Windows)
            if current_handle:
                try:
                    # Check if file has grown (new data available)
                    current_handle.seek(0, 2)  # Go to end
                    end_position = current_handle.tell()
                    
                    if end_position > file_position:
                        # New data available, go back to last read position
                        current_handle.seek(file_position)
                    else:
                        # No new data
                        time.sleep(0.05)  # Reduce CPU load
                        continue
                    
                    line = current_handle.readline()
                    
                    if not line:
                        time.sleep(0.05)  # Reduce CPU load
                        continue
                    
                    # Update position after successful read
                    file_position = current_handle.tell()
                    
                    # JSON parsing and processing
                    data = json.loads(line)
                    
                    # Duplicate check
                    msg_id = generate_message_id(data)
                    if msg_id in _processed_messages:
                        continue
                    
                    _processed_messages.append(msg_id)

                    # --- v4.0: User input confirmation ---
                    if data.get('type') == 'queue-operation' and data.get('operation') == 'enqueue':
                        user_content = data.get('content', '')
                        if user_content and isinstance(user_content, str) and not user_content.startswith('<'):
                            logger.info("[UserInput] User message received")
                            enqueue_speech_simple("受け取りました。", speed=NARRATION_SPEED_NORMAL, volume=VOLUME_THINKING)
                        continue

                    # Process assistant and user messages
                    if 'message' in data:
                        msg = data['message']

                        # --- v4.0: User role - detect human input & permission responses ---
                        if msg.get('role') == 'user':
                            content = msg.get('content', '')

                            # Human-typed message (string content, not tool_result)
                            if isinstance(content, str) and len(content) > 3:
                                # Already handled by queue-operation above
                                pass

                            # Tool results - check for permission denied
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get('type') == 'tool_result':
                                        result_text = str(item.get('content', ''))
                                        if "doesn't want to proceed" in result_text or 'rejected' in result_text.lower():
                                            logger.info("[Permission] User denied tool use")
                                            enqueue_speech_simple("ユーザーが操作を拒否しました。", speed=NARRATION_SPEED_NORMAL, volume=VOLUME_NORMAL)
                            continue

                        # --- Assistant messages ---
                        if msg.get('role') == 'assistant':
                            content = msg.get('content', [])

                            logger.info("[Assistant] Response detected")

                            full_text = ""
                            for item in content:
                                if isinstance(item, dict):
                                    text = item.get('text', '')
                                    if text:
                                        full_text += text

                            # Check for thinking content
                            thinking_text = ""
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get('type') == 'thinking':
                                        thinking = item.get('thinking', '')
                                        if thinking:
                                            thinking_text += thinking

                            # Process thinking if found
                            if thinking_text.strip():
                                thinking_narration = process_thinking_for_narration(thinking_text)
                                if thinking_narration:
                                    logger.info(f"[Thinking] {len(thinking_narration)} chars")
                                    enqueue_speech_simple(thinking_narration, speed=NARRATION_SPEED_THINKING, volume=VOLUME_THINKING)

                            # v4.0: Tool use narration with permission awareness
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'tool_use':
                                    tool_narration = process_tool_use_for_narration(
                                        item.get('name', ''),
                                        item.get('input', {})
                                    )
                                    if tool_narration:
                                        logger.info(f"[ToolUse] {item.get('name', '')}: {tool_narration}")
                                        enqueue_speech_simple(tool_narration, speed=NARRATION_SPEED_THINKING, volume=VOLUME_THINKING)

                            # Process regular text
                            if full_text.strip():
                                narration_text = process_text_for_narration(full_text)
                                logger.info(f"[Assistant] Full text: {len(narration_text)} chars")

                                enqueue_speech_simple(narration_text, speed=NARRATION_SPEED_NORMAL, volume=VOLUME_NORMAL)
                    
                except json.JSONDecodeError:
                    pass  # Ignore incomplete JSON
                except Exception as e:
                    if "Expecting value" not in str(e):
                        logger.error(f"[Monitor] Processing error: {e}")
            else:
                # Wait a bit if no file handle
                time.sleep(1.0)
    
    except KeyboardInterrupt:
        logger.info("\n[Monitor] Stopping by user request...")
    except Exception as e:
        logger.error(f"[Monitor] Unexpected error: {e}", exc_info=True)
    finally:
        # Cleanup
        if current_handle:
            current_handle.close()
            logger.debug("Closed file handle in cleanup")
        _stop_flag.set()
        
        # Termination signal
        _speech_queue.put(None)
        
        if _speech_thread and _speech_thread.is_alive():
            _speech_thread.join(timeout=5)
        
        logger.info("[Monitor] Monitor stopped")

def main():
    """Main entry point"""
    global _start_time
    _start_time = time.time()
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == 'win32':
        signal.signal(signal.SIGBREAK, signal_handler)
    
    # Register cleanup function
    atexit.register(cleanup_at_exit)
    print("="*70)
    print("Claude AIVIS Aloud v3.2.3")
    print("Optimized for fast startup and timeout prevention")
    print(f"Voice test: {'Enabled' if DEBUG_TEST_VOICE else 'Silent mode (faster startup)'}")
    print("="*70)
    
    # Cleanup duplicate processes
    print("\n1. Cleaning up duplicate processes...")
    cleanup_duplicate_processes()
    print("[OK] Process cleanup completed")
    
    # Cleanup old logs
    print("\n2. Cleaning up old log files...")
    cleanup_old_logs(retention_days=7)
    print("[OK] Log cleanup completed")
    
    print("\n3. Testing AivisSpeech Engine...")
    if not test_voice_system():
        print("[ERROR] AivisSpeech Engine is not running")
        print("Please start AIVIS Speech Engine first")
        return
    
    print("[OK] AivisSpeech Engine is running")
    
    print("\n4. Starting the monitoring system...")
    print("Features:")
    print("  - Simple FIFO queue (no priority)")
    print("  - No hook events")
    print("  - Assistant responses: Full text reading")
    print("  - Dynamic file switching: Auto-detect new sessions")
    print("  - Duplicate process prevention")
    print("  - Background execution support")
    print("  - Graceful shutdown handling")
    print("="*70)
    
    # Write PID file for process management
    pid_file = Path.home() / '.claude' / 'kanon_aloud.pid'
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    logger.info(f"[Process] PID file created: {pid_file}")
    
    try:
        monitor_and_speak()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
        print("Session ended successfully")
        _stop_flag.set()
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        logger.error(f"Main error: {e}", exc_info=True)
        _stop_flag.set()

if __name__ == "__main__":
    main()