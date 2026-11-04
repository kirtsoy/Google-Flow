import os, sys, json, subprocess
from faster_whisper import WhisperModel

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

EP_DIR = r"C:\Users\kiril\Downloads\STICKMAN UNIVERSE\EPISODES\05_The_Crab_Mentality"
AUDIO_DIR = os.path.join(EP_DIR, "audio")
VIDEO_DIR = os.path.join(EP_DIR, "video")
SUB_DIR = os.path.join(EP_DIR, "subtitles")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(SUB_DIR, exist_ok=True)

FULL_AUDIO_PATH = os.path.join(AUDIO_DIR, "full_video_audio.wav")

COLOR_RED = r"&H002A2AFF&"     # Danger / Traps / Negative / Bucket
COLOR_GREEN = r"&H0032CD32&"   # Growth / Action / Elevation
COLOR_CYAN = r"&H00FFFF00&"    # Science / Psychology / Brain / Biology
COLOR_GOLD = r"&H0000D7FF&"    # Punch / Climax / Impact
COLOR_WHITE = r"&H00FFFFFF&"   # Default clean white

SEMANTIC_COLORS = {
    # Red (Crab / Bucket / Stagnation / Panic / Trap)
    "CRAB": COLOR_RED, "BUCKET": COLOR_RED, "STAGNATION": COLOR_RED,
    "PANIC": COLOR_RED, "DOWN": COLOR_RED, "TRAPPED": COLOR_RED,
    "EXCUSES": COLOR_RED, "FRAGILE": COLOR_RED, "MOCKING": COLOR_RED,
    # Green (Growth / Level Up / Elevation / Escape)
    "LEVEL": COLOR_GREEN, "GROWTH": COLOR_GREEN, "ELEVATION": COLOR_GREEN,
    "ESCAPE": COLOR_GREEN, "BREAK": COLOR_GREEN, "UP": COLOR_GREEN,
    # Cyan (Psychology / Biology / Mirror)
    "BIOLOGY": COLOR_CYAN, "PSYCHOLOGICALLY": COLOR_CYAN, "MIRROR": COLOR_CYAN,
    "EGO": COLOR_CYAN, "CIRCLE": COLOR_CYAN, "ADDICTED": COLOR_CYAN,
    # Gold (Punch / Climax)
    "AMBITION": COLOR_GOLD, "SECOND": COLOR_GOLD, "BORING": COLOR_GOLD,
    "PAINFUL": COLOR_GOLD, "RESCUE": COLOR_GOLD, "TRUE": COLOR_GOLD,
    "COMFORT": COLOR_GOLD
}

def clean_word_for_lookup(w):
    clean = w.upper().replace(",", "").replace(".", "").replace("?", "").replace("!", "").replace(":", "").replace(";", "")
    return clean.strip()

def get_word_color(word_str):
    clean = clean_word_for_lookup(word_str)
    return SEMANTIC_COLORS.get(clean, COLOR_WHITE)

def format_ass_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"

def format_srt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    if ms >= 1000:
        ms = 999
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def get_audio_duration(path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path]
    return float(subprocess.check_output(cmd).decode().strip())

def transcribe_and_align_whisper(audio_path):
    print("🎙 Transcribing audio directly with faster-whisper (word-level ground truth)...")
    model = WhisperModel('base.en', device='cpu', compute_type='int8')
    segments, info = model.transcribe(audio_path, word_timestamps=True)

    raw_words = []
    for seg in segments:
        for w in seg.words:
            txt = w.word.strip()
            if not txt:
                continue
            if txt.startswith('-') and raw_words:
                raw_words[-1]['word'] += txt
                raw_words[-1]['end'] = float(w.end)
            else:
                raw_words.append({
                    'word': txt,
                    'start': float(w.start),
                    'end': float(w.end)
                })

    chunks = []
    current_chunk = []

    for i, w in enumerate(raw_words):
        current_chunk.append(w)
        is_last = (i == len(raw_words) - 1)
        
        pause_gap = 0.0
        if not is_last:
            pause_gap = raw_words[i+1]['start'] - w['end']
        
        ends_sentence = any(w['word'].endswith(p) for p in ['.', '?', '!'])
        chunk_dur = current_chunk[-1]['end'] - current_chunk[0]['start']
        ends_comma = any(w['word'].endswith(p) for p in [',', ';', ':'])
        
        should_break = False
        if is_last:
            should_break = True
        elif ends_sentence:
            should_break = True
        elif pause_gap >= 0.40:
            should_break = True
        elif len(current_chunk) >= 3:
            should_break = True
        elif ends_comma and (len(current_chunk) >= 2 or chunk_dur >= 0.50):
            should_break = True

        if should_break:
            chunks.append(current_chunk)
            current_chunk = []

    refined_chunks = []
    idx = 0
    while idx < len(chunks):
        ch = chunks[idx]
        if len(ch) == 1 and (ch[0]['end'] - ch[0]['start'] < 0.35) and idx + 1 < len(chunks):
            next_ch = chunks[idx+1]
            gap = next_ch[0]['start'] - ch[-1]['end']
            if gap < 0.25 and len(next_ch) < 3:
                combined = ch + next_ch
                refined_chunks.append(combined)
                idx += 2
                continue
        refined_chunks.append(ch)
        idx += 1

    return raw_words, refined_chunks

def generate_srt(chunks):
    lines = []
    for idx, chunk in enumerate(chunks, 1):
        s_str = format_srt_time(chunk[0]["start"])
        e_str = format_srt_time(chunk[-1]["end"])
        text = " ".join(w["word"] for w in chunk).upper()
        lines.append(f"{idx}\n{s_str} --> {e_str}\n{text}\n")
    return "\n".join(lines)

def generate_ass(chunks):
    header = """[Script Info]
Title: Stickman Universe Clean Montserrat Kinetic Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: StickmanWords,Montserrat,84,&H00FFFFFF,&H0000D7FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5.0,0.0,2,50,50,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    for c_idx, chunk in enumerate(chunks):
        chunk_start = chunk[0]["start"]
        last_word_end = chunk[-1]["end"]

        if c_idx + 1 < len(chunks):
            next_chunk_start = chunks[c_idx + 1][0]["start"]
            gap_to_next = next_chunk_start - last_word_end
            if gap_to_next < 0.45:
                chunk_display_end = next_chunk_start
            else:
                chunk_display_end = min(last_word_end + 0.35, next_chunk_start - 0.10)
        else:
            chunk_display_end = last_word_end + 0.50

        if chunk_display_end <= chunk_start:
            chunk_display_end = chunk_start + 0.30

        k = len(chunk)
        for w_idx, active_word in enumerate(chunk):
            if w_idx == 0:
                w_ev_start = chunk_start
            else:
                w_ev_start = active_word["start"]

            if w_idx < k - 1:
                w_ev_end = chunk[w_idx + 1]["start"]
            else:
                w_ev_end = chunk_display_end

            if w_ev_end <= w_ev_start:
                w_ev_end = w_ev_start + 0.10

            w_start_str = format_ass_time(w_ev_start)
            w_end_str = format_ass_time(w_ev_end)

            parts = []
            for other_w in chunk:
                raw_txt = other_w["word"].upper()
                if other_w == active_word:
                    color = get_word_color(other_w["word"])
                    if color == COLOR_WHITE:
                        color = COLOR_GOLD
                    parts.append(f"{{\\c{color}\\fscx108\\fscy108}}{raw_txt}{{\\rStickmanWords}}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF&}}{raw_txt}{{\\rStickmanWords}}")

            dialogue_text = " ".join(parts)
            events.append(f"Dialogue: 2,{w_start_str},{w_end_str},StickmanWords,,0,0,0,,{dialogue_text}")

    return header + "\n".join(events)

def main():
    print("=======================================================")
    print("🎬 GENERATING EPISODE 05 KINETIC ASSETS")
    print("=======================================================")

    if not os.path.exists(FULL_AUDIO_PATH):
        raw_vid = None
        for cand in ["stickman_shorts_9x16.mp4", "the doing trap final.mp4", "raw_flow_720p.mp4"]:
            p = os.path.join(EP_DIR, cand)
            if os.path.exists(p):
                raw_vid = p
                break
            p_sub = os.path.join(VIDEO_DIR, cand)
            if os.path.exists(p_sub):
                raw_vid = p_sub
                break
        if raw_vid:
            print(f"🎵 Extracting full audio from {raw_vid}...")
            subprocess.run(["ffmpeg", "-y", "-i", raw_vid, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", FULL_AUDIO_PATH], check=True)
        else:
            print("[INFO] No raw video export found yet. Will transcribe individual scene audios once full export is staged.")
            return

    total_duration = get_audio_duration(FULL_AUDIO_PATH)
    print(f"🎵 Video Audio Duration: {total_duration:.2f}s")

    raw_words, chunks = transcribe_and_align_whisper(FULL_AUDIO_PATH)
    print(f"✅ Extracted {len(raw_words)} true words, built {len(chunks)} continuous kinetic chunks.")

    words_json_path = os.path.join(SUB_DIR, "stickman_captions_words.json")
    with open(words_json_path, "w", encoding="utf-8") as f:
        json.dump(raw_words, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved word timestamps: {words_json_path}")

    srt_content = generate_srt(chunks)
    srt_path = os.path.join(SUB_DIR, "stickman_captions.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"✅ Saved SRT captions: {srt_path}")

    ass_content = generate_ass(chunks)
    ass_path = os.path.join(SUB_DIR, "stickman_captions.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    print(f"✅ Saved ASS clean captions: {ass_path}")

    bat_content = f"""@echo off
setlocal
title Process Stickman Episode 05
cd /d "%~dp0"

echo ========================================================
echo   STICKMAN UNIVERSE -- EPISODE 05 PROCESSING PIPELINE
echo ========================================================
echo.

python "c:\\KIRTSOY_CORE\\AI_PROGRAMS\\Google Flow\\universal_episode_processor.py" "%~dp0"

echo.
pause
"""
    bat_path = os.path.join(EP_DIR, "PROCESS_EPISODE_05.bat")
    with open(bat_path, "wb") as f:
        f.write(bat_content.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    print(f"✅ Updated 1-tap launcher: {bat_path}")

    print("\n🎉 ALL EPISODE 05 PRE-FLIGHT ASSETS READY!")

if __name__ == "__main__":
    main()
