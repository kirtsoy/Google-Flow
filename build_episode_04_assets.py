import os, sys, json, asyncio, subprocess
import edge_tts

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

EP_DIR = r"C:\Users\kiril\Downloads\STICKMAN UNIVERSE\EPISODES\04_The_Knowing_Doing_Trap"
AUDIO_DIR = os.path.join(EP_DIR, "audio")
VIDEO_DIR = os.path.join(EP_DIR, "video")
SUB_DIR = os.path.join(EP_DIR, "subtitles")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(SUB_DIR, exist_ok=True)

SCENES = [
    (1, "You have all the tutorials, blueprints, and motivation. So why is another year gone, and nothing changed?"),
    (2, "Your brain mistakes reading advice for real action, drowning you in cheap, unearned dopamine."),
    (3, "Every video triggers artificial dopamine, giving you the rush of winning without taking a single step."),
    (4, "To your ancient ancestors, expending precious calories on uncertain rewards meant certain starvation."),
    (5, "Your primitive brain views difficult new ambitions as life-threatening wastes of vital biological energy."),
    (6, "Progress never begins with more research. It starts the second you choose friction over safe comfort."),
    (7, "Because until you take action, you remain stuck in the exact same loop, where...")
]

# Exact measured scene start offsets in exported Google Flow video (8.0s per scene)
SCENE_OFFSETS = [0.40, 8.40, 16.44, 24.48, 32.52, 40.61, 48.65]
TOTAL_EPISODE_DURATION = 56.30

COLOR_RED = r"&H002A2AFF&"     # Danger / Traps / Negative
COLOR_GREEN = r"&H0032CD32&"   # Dopamine / Action / Progress
COLOR_CYAN = r"&H00FFFF00&"    # Tech / Brain / Science / Blueprints
COLOR_GOLD = r"&H0000D7FF&"    # Punch / Climax / Impact
COLOR_WHITE = r"&H00FFFFFF&"   # Default clean white

SEMANTIC_COLORS = {
    # Red (Danger / Traps)
    "TRAP": COLOR_RED, "DROWNING": COLOR_RED, "CHEAP": COLOR_RED,
    "UNEARNED": COLOR_RED, "STARVATION": COLOR_RED, "PANIC": COLOR_RED,
    "LOOP": COLOR_RED, "GONE": COLOR_RED, "NOTHING": COLOR_RED, "WASTES": COLOR_RED,
    # Green (Dopamine / Progress)
    "DOPAMINE": COLOR_GREEN, "WINNING": COLOR_GREEN, "PROGRESS": COLOR_GREEN,
    "REWARDS": COLOR_GREEN, "ACTION": COLOR_GREEN, "EXECUTION": COLOR_GREEN, "STEP": COLOR_GREEN,
    # Cyan (Brain / Tech / Science)
    "TUTORIALS": COLOR_CYAN, "BLUEPRINTS": COLOR_CYAN, "PSYCHOLOGISTS": COLOR_CYAN,
    "ENERGY": COLOR_CYAN, "BIOLOGICAL": COLOR_CYAN, "RESEARCH": COLOR_CYAN, "BRAIN": COLOR_CYAN,
    "CALORIES": COLOR_CYAN, "ANCESTORS": COLOR_CYAN, "ADVICE": COLOR_CYAN,
    # Gold (Punch / Climax)
    "WHY": COLOR_GOLD, "FRICTION": COLOR_GOLD, "MISTAKES": COLOR_GOLD,
    "PRIMITIVE": COLOR_GOLD, "COMFORT": COLOR_GOLD, "NEVER": COLOR_GOLD,
    "SECOND": COLOR_GOLD, "MOTIVATION": COLOR_GOLD, "RUSH": COLOR_GOLD
}

def get_word_color(word_clean):
    return SEMANTIC_COLORS.get(word_clean.upper(), COLOR_WHITE)

async def extract_words_for_episode():
    print("🎙 Extracting ground-truth word boundaries scaled to Adam audio...")
    all_words = []
    
    for idx, text in SCENES:
        scene_id = idx
        offset = SCENE_OFFSETS[scene_id - 1]
        wav_path = os.path.join(AUDIO_DIR, f"scene_{scene_id}_adam.wav")
        
        # Measure actual Adam wav duration
        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', wav_path]
        adam_dur = float(subprocess.check_output(probe_cmd).decode().strip())
        
        # Get raw edge-tts word timings
        comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", boundary="WordBoundary")
        raw_words = []
        async for chunk in comm.stream():
            if chunk["type"] == "WordBoundary":
                raw_words.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10_000_000,
                    "dur": chunk["duration"] / 10_000_000
                })
        
        if not raw_words:
            continue
            
        edge_total = raw_words[-1]["start"] + raw_words[-1]["dur"]
        scale_ratio = adam_dur / edge_total if edge_total > 0 else 1.0
        
        for w in raw_words:
            scaled_start = offset + (w["start"] * scale_ratio)
            scaled_dur = w["dur"] * scale_ratio
            all_words.append({
                "scene": scene_id,
                "word": w["word"],
                "start": round(scaled_start, 3),
                "end": round(scaled_start + scaled_dur, 3),
                "dur": round(scaled_dur, 3)
            })
            
    return all_words

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

def build_phrases(words, max_words=3):
    phrases = []
    for scene_id in range(1, 8):
        s_words = [w for w in words if w["scene"] == scene_id]
        for i in range(0, len(s_words), max_words):
            chunk = s_words[i:i + max_words]
            if chunk:
                phrases.append({
                    "scene": scene_id,
                    "start": chunk[0]["start"],
                    "end": chunk[-1]["end"],
                    "words": chunk
                })
    return phrases

def generate_srt(phrases):
    lines = []
    for idx, p in enumerate(phrases, 1):
        s_str = format_srt_time(p["start"])
        e_str = format_srt_time(p["end"])
        text = " ".join(w["word"] for w in p["words"]).upper()
        lines.append(f"{idx}\n{s_str} --> {e_str}\n{text}\n")
    return "\n".join(lines)

def generate_ass(phrases):
    header = """[Script Info]
Title: Stickman Universe Rock-Solid Montserrat Kinetic Captions with HUD Progress
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: StickmanWords,Montserrat,84,&H00FFFFFF,&H0000D7FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5.0,0.0,2,50,50,380,1
Style: TopProgressBarBG,Arial,10,&H40000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: TopProgressBarFill,Arial,10,&H0000D7FF,&H00000000,&H00FFFF00,&H00000000,0,0,0,0,100,100,0,0,1,1.0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []

    # 1. Top HUD Progress Bar (Layer 0 Background, Layer 1 Animated Fill)
    # Background rail: X=40 to X=1040 (width 1000px), Y=35 to Y=43 (height 8px)
    bg_start = format_ass_time(0.0)
    bg_end = format_ass_time(TOTAL_EPISODE_DURATION)
    events.append(f"Dialogue: 0,{bg_start},{bg_end},TopProgressBarBG,,0,0,0,,{{\\p1\\pos(40,35)}}m 0 0 l 1000 0 l 1000 8 l 0 8{{\\p0}}")
    
    # Smooth animated fill using ASS \t (transition) and \clip
    events.append(f"Dialogue: 1,{bg_start},{bg_end},TopProgressBarFill,,0,0,0,,{{\\p1\\pos(40,35)\\clip(40,35,40,43)\\t(0,{int(TOTAL_EPISODE_DURATION*1000)},\\clip(40,35,1040,43))}}m 0 0 l 1000 0 l 1000 8 l 0 8{{\\p0}}")

    # 2. Semantic Montserrat-Bold Kinetic Words
    for p_idx, phrase in enumerate(phrases):
        p_start = phrase["start"]
        p_end = phrase["end"]
        words_in_phrase = phrase["words"]
        
        for w_idx, active_word in enumerate(words_in_phrase):
            w_start = active_word["start"]
            w_end = active_word["end"]
            
            # Safe clamp
            if w_end <= w_start:
                w_end = w_start + 0.15
            
            w_start_str = format_ass_time(w_start)
            w_end_str = format_ass_time(w_end)
            
            parts = []
            for other_w in words_in_phrase:
                txt = other_w["word"].upper().replace(",", "").replace(".", "").replace("?", "").replace("!", "").replace(":", "")
                clean_txt = "".join(ch for ch in txt if ch.isalnum())
                
                if other_w == active_word:
                    # Highlight color from semantic matrix + subtle spring punch-in
                    color = get_word_color(clean_txt)
                    if color == COLOR_WHITE:
                        color = COLOR_GOLD  # Fallback highlight to gold for active word
                    parts.append(f"{{\\c{color}\\fscx106\\fscy106}}{other_w['word'].upper()}{{\\rStickmanWords}}")
                else:
                    parts.append(f"{{\\c&H00FFFFFF&}}{other_w['word'].upper()}{{\\rStickmanWords}}")
            
            dialogue_text = " ".join(parts)
            events.append(f"Dialogue: 2,{w_start_str},{w_end_str},StickmanWords,,0,0,0,,{dialogue_text}")

    return header + "\n".join(events)

def main():
    print("=======================================================")
    print("🎬 GENERATING EPISODE 04 KINETIC ASSETS & HUD")
    print("=======================================================")
    
    words = asyncio.run(extract_words_for_episode())
    words_json_path = os.path.join(SUB_DIR, "stickman_captions_words.json")
    with open(words_json_path, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved word timestamps: {words_json_path} ({len(words)} words)")
    
    phrases = build_phrases(words, max_words=3)
    
    srt_content = generate_srt(phrases)
    srt_path = os.path.join(SUB_DIR, "stickman_captions.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"✅ Saved SRT captions: {srt_path}")
    
    ass_content = generate_ass(phrases)
    ass_path = os.path.join(SUB_DIR, "stickman_captions.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    print(f"✅ Saved ASS kinetic captions with HUD Progress Bar: {ass_path}")

    # Generate 1-tap launcher
    bat_content = f"""@echo off
setlocal
title Process Stickman Episode 04
cd /d "%~dp0"

echo ========================================================
echo   STICKMAN UNIVERSE -- EPISODE 04 PROCESSING PIPELINE
echo ========================================================
echo.

python "c:\\KIRTSOY_CORE\\AI_PROGRAMS\\Google Flow\\universal_episode_processor.py" "%~dp0"

echo.
pause
"""
    bat_path = os.path.join(EP_DIR, "PROCESS_EPISODE_04.bat")
    with open(bat_path, "wb") as f:
        f.write(bat_content.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    print(f"✅ Created 1-tap launcher: {bat_path}")

    print("\n🎉 ALL EPISODE 04 PRE-FLIGHT ASSETS READY!")

if __name__ == "__main__":
    main()
