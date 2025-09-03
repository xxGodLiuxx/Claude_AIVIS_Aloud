#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude AIVIS Aloud v1.3.0
Real-time processing optimized version
Volume: Normal 1.0, Thinking 0.5
Based on v1.2.0 with improved real-time response and fixed message detection
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
logger = logging.getLogger('kanon')

# ===============================
# Global variables and settings
# ===============================
_processed_messages = deque(maxlen=100)  # Duplicate prevention
_speech_queue = queue.Queue()  # Simple FIFO queue
_speech_thread = None
_stop_flag = threading.Event()

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

# Volume settings for differentiation (v3.1.4)
VOLUME_NORMAL = 1.0  # 通常の応答の音量
VOLUME_THINKING = 0.5  # Thinking部分の音量（より控えめ）

# Dynamic file switching settings
CHECK_INTERVAL = 10  # seconds (new session check interval)

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
            except:
                pass
        
        if deleted_count > 0:
            logger.info(f"[Cleanup] Deleted {deleted_count} old log files (>{retention_days} days)")
    except Exception as e:
        logger.warning(f"[Cleanup] Log cleanup error: {e}")

# ===============================
# Duplicate process prevention
# ===============================
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
            $_.CommandLine -like '*kanon_aloud*'
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
                except:
                    pass
        
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
    Simple speech worker: Process messages in order (FIFO)
    """
    import requests
    import pygame
    import io
    
    pygame.mixer.init(frequency=24000, size=-16, channels=1)
    
    logger.info("[SpeechWorker] Simple worker started (v1.3.0)")
    
    while not _stop_flag.is_set():
        try:
            # Get from simple queue
            item = _speech_queue.get(timeout=1.0)
            
            if item is None:  # Termination signal
                break
            
            # v3.1.4: Support volume parameter
            if len(item) == 3:
                text, speed, volume = item
            else:
                text, speed = item
                volume = VOLUME_NORMAL
            
            logger.info(f"[SpeechWorker] Processing: {len(text)} chars (volume: {volume})")
            
            # Read all messages (no priority distinction)
            if len(text) > AIVIS_MAX_LENGTH:
                chunks = split_text_naturally(text, AIVIS_OPTIMAL_LENGTH)
                logger.info(f"[SpeechWorker] Split into {len(chunks)} parts")
                
                for i, chunk in enumerate(chunks, 1):
                    if _stop_flag.is_set():
                        break
                    
                    logger.info(f"[SpeechWorker] Part {i}/{len(chunks)}: {len(chunk)} chars")
                    success = speak_single_chunk(chunk, speed, volume)
                    
                    if success and i < len(chunks):
                        # Natural pause based on content
                        if '。。' in chunk:
                            time.sleep(NARRATION_PAUSE_PARAGRAPH)
                        else:
                            time.sleep(NARRATION_PAUSE_SENTENCE)
            else:
                # Normal reading
                speak_single_chunk(text, speed, volume)
            
            logger.info(f"[SpeechWorker] Reading completed")
            
            _speech_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"[SpeechWorker] Error: {e}")
            try:
                _speech_queue.task_done()
            except:
                pass

def speak_single_chunk(text, speed, volume=1.0):
    """
    Read a single chunk reliably with volume control (v3.1.4)
    """
    import requests
    import pygame
    import io
    
    try:
        # Generate AudioQuery
        query_response = requests.post(
            f"{AIVIS_BASE_URL}/audio_query?speaker={AIVIS_SPEAKER_ID}&text={text}",
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
            
            # Wait until finished reading
            if channel:
                while channel.get_busy() and not _stop_flag.is_set():
                    pygame.time.wait(10)
            
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
    """Convert thinking text for full narration without prefix (v1.2.0: enhanced)"""
    # 思考内容を全文処理（要約なし、前置詞なし）
    text = thinking_text.strip()
    
    # v1.2.0: Convert numbered lists to natural reading format (1. -> 1、)
    # This must be done before line break processing
    text = re.sub(r'(\d+)\.(\s*)', r'\1、', text)
    
    # Remove bullet markers for cleaner reading
    text = re.sub(r'^- (.+?)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^• (.+?)$', r'\1', text, flags=re.MULTILINE)
    text = re.sub(r'^· (.+?)$', r'\1', text, flags=re.MULTILINE)
    
    # 基本的な変換処理
    text = re.sub(r'\n+', '、', text)
    text = re.sub(r'\s+', ' ', text)
    
    # 文字化けや不要な文字を除去（ただし数字は保持）
    text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF、。！？0-9]', '', text)
    
    # 空の場合はNoneを返す
    if not text.strip():
        return None
    
    return text

def process_text_for_narration(text):
    """Convert text for natural narration experience (v3.1.5 enhanced)"""
    # Process code blocks with surrounding whitespace
    # This prevents awkward punctuation around code blocks
    text = re.sub(r'\n*```[\s\S]*?```\n*', '。コード部分があります。', text)
    
    # Convert file paths to Japanese (more natural patterns)
    # Simplify long paths
    text = re.sub(r'C:\\Users\\[^\\]+\\Documents\\[^\\]+\\[^\\]+\\([^\s\\]+)', 
                  r'プロジェクト内の\1', text)
    text = re.sub(r'C:\\Users\\[^\\]+\\([^\s]+)', 
                  r'ユーザーフォルダの\1', text)
    
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
        'HTML': 'エイチティーエムエル',
        'CSS': 'スタイルシート',
        'CLI': 'コマンドライン',
        'ID': 'アイディー',
        'OK': 'オーケー',
        'NG': 'エヌジー',
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
        'delete': '削除',
    }
    
    # Apply replacements
    for old, new in replacements.items():
        text = re.sub(rf'\b{old}\b', new, text, flags=re.IGNORECASE)
    
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
    
    # Clean up consecutive punctuation
    text = re.sub(r'。+', '。', text)  # Multiple periods to single
    text = re.sub(r'、+', '、', text)  # Multiple commas to single
    text = re.sub(r'。、', '。', text)  # Period followed by comma to just period
    text = re.sub(r'、。', '。', text)  # Comma followed by period to just period
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def test_voice_system():
    """Check AivisSpeech Engine operation"""
    import requests
    import pygame
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
            pygame.mixer.init(frequency=24000, size=-16, channels=1)
            audio_data = io.BytesIO(response.content)
            sound = pygame.mixer.Sound(audio_data)
            channel = sound.play()
            
            if channel:
                while channel.get_busy():
                    pygame.time.wait(10)
            
            logger.info("AivisSpeech Engine is running")
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
    
    # Add timestamp if available
    if 'timestamp' in data:
        key_parts.append(str(data['timestamp']))
    
    id_str = '_'.join(filter(None, key_parts))
    return hashlib.md5(id_str.encode()).hexdigest()[:16]

def find_latest_jsonl():
    """Find the latest JSONL file"""
    patterns = [
        r"C:\Users\liuco\.claude\projects\**\*.jsonl",
        r"C:\Users\*\.claude\projects\**\*.jsonl"
    ]
    
    all_files = []
    for pattern in patterns:
        files = glob(pattern, recursive=True)
        all_files.extend(files)
    
    if not all_files:
        logger.error("JSONL file not found")
        return None
    
    latest = max(all_files, key=lambda x: os.path.getmtime(x))
    logger.info(f"Found JSONL: {latest}")
    return latest

def skip_initial_messages(file_handle, skip_count=0):
    """Skip initial messages (v1.3.0: configurable, default 0)"""
    skipped_count = 0
    for _ in range(skip_count):  # v1.3.0: Default 0 to avoid missing messages
        line = file_handle.readline()
        if not line:
            break
        try:
            data = json.loads(line)
            msg_id = generate_message_id(data)
            _processed_messages.append(msg_id)
            skipped_count += 1
        except:
            pass
    
    if skipped_count > 0:
        logger.info(f"[Monitor] Skipped {skipped_count} initial messages")
    return skipped_count

def monitor_and_speak():
    """
    Dynamic file switching supported version
    Simplified without hooks and priority
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
    
    # Initial file selection
    current_file = find_latest_jsonl()
    if not current_file:
        logger.error("No JSONL file found at startup")
        return
    
    logger.info(f"[Monitor] Initial file: {os.path.basename(current_file)}")
    logger.info(f"[Monitor] Check interval: {CHECK_INTERVAL} seconds")
    logger.info(f"[Monitor] Auto session detection: ENABLED")
    logger.info("="*70)
    logger.info("Claude AIVIS Aloud v1.3.0")
    logger.info("Features:")
    logger.info("  - Simple FIFO queue (no priority system)")
    logger.info("  - No hook event processing")
    logger.info("  - Assistant messages: Full text reading")
    logger.info("  - Dynamic file switching: Auto-detect new sessions")
    logger.info("  - Duplicate process prevention")
    logger.info("="*70)
    
    try:
        while not _stop_flag.is_set():
            # Periodic latest file check
            now = time.time()
            if now - last_check > CHECK_INTERVAL:
                latest_file = find_latest_jsonl()
                
                # File switching determination
                if latest_file and latest_file != current_file:
                    logger.info(f"[SESSION SWITCH] {os.path.basename(current_file)} -> {os.path.basename(latest_file)}")
                    
                    # 1. Close old handle
                    if current_handle:
                        current_handle.close()
                        logger.debug("Closed old file handle")
                    
                    # 2. Open new file
                    current_file = latest_file
                    current_handle = open(current_file, 'r', encoding='utf-8', errors='ignore')
                    
                    # 3. Set start position (v1.3.0: start from end for real-time)
                    current_handle.seek(0, 2)  # Move to end of file
                    
                    # 4. Clear processed message IDs
                    _processed_messages.clear()
                    logger.debug("Cleared processed message cache")
                    
                    # 5. Skip initial messages (v1.3.0: don't skip on session switch)
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
                
                # Set start position (v1.3.0: start from end for real-time)
                current_handle.seek(0, 2)  # Move to end of file
                
                # Skip initial messages (v1.3.0: disabled to avoid missing messages)
                # skip_initial_messages(current_handle)  # Disabled
                
                logger.info(f"[Monitor] Opened file: {os.path.basename(current_file)}")
            
            # Normal read processing
            if current_handle:
                try:
                    line = current_handle.readline()
                    
                    if not line:
                        time.sleep(0.05)  # Reduce CPU load
                        continue
                    
                    # JSON parsing and processing
                    data = json.loads(line)
                    
                    # Duplicate check
                    msg_id = generate_message_id(data)
                    if msg_id in _processed_messages:
                        continue
                    
                    _processed_messages.append(msg_id)
                    
                    # Process assistant messages and thinking
                    if 'message' in data:
                        msg = data['message']
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
                            
                            # Process thinking if found (v3.1.4: with reduced volume)
                            if thinking_text.strip():
                                thinking_narration = process_thinking_for_narration(thinking_text)
                                if thinking_narration:
                                    logger.info(f"[Thinking] Detected thinking: {len(thinking_narration)} chars (volume: {VOLUME_THINKING})")
                                    enqueue_speech_simple(thinking_narration, speed=NARRATION_SPEED_THINKING, volume=VOLUME_THINKING)
                            
                            # Process regular text (v3.1.4: with normal volume)
                            if full_text.strip():
                                # Convert full text for narration
                                narration_text = process_text_for_narration(full_text)
                                logger.info(f"[Assistant] Full text reading: {len(narration_text)} chars (volume: {VOLUME_NORMAL})")
                                
                                # Add to queue with normal narration speed and volume
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
    print("="*70)
    print("Claude AIVIS Aloud v1.3.0")
    print("Simplified version without hooks and priority")
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
    print("="*70)
    
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