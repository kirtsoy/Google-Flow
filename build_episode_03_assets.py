import os, sys, json, asyncio, subprocess
import edge_tts

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

EP_DIR = r"C:\Users\kiril\Downloads\STICKMAN UNIVERSE\EPISODES\03_The_Tetris_Effect"
RAW_VIDEO = os.path.join(EP_DIR, "stickman_shorts_9x16.mp4")
VIDEO_DIR = os.path.join(EP_DIR, "video")
SUB_DIR = os.path.join(EP_DIR, "subtitles")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(SUB_DIR, exist_ok=True)

SCENES = [
    "You turn off your computer after hours of gaming, close your eyes to sleep, yet the game keeps playing.",
    "Vivid neon blocks fall, spin, and click into slots on the backs of your eyelids.",
    "Psychologists call this the Tetris Effect, first documented when players dreamed of blocks for days.",
    "To our ancient ancestors, repetitive daily tasks were vital survival skills that demanded emergency rewiring.",
    "Your brain assumes these digital mechanics are critical for survival, aggressively optimizing neural pathways.",
    "From seeing real-world boxes as Minecraft blocks to hearing game audio cues, the loop lingers.",
    "The Tetris effect proves your brain is a learning machine, effortlessly rewiring itself to master new worlds."
]

SCENE_OFFSETS = [0.40, 8.435, 16.494, 24.520, 32.412, 40.388, 48.504]

async def extract_words():
    print("🎙 Extracting ground-truth word boundaries via Edge Neural TTS...")
    all_words = []
    for idx, (text, offset) in enumerate(zip(SCENES, SCENE_OFFSETS)):
        comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", boundary="WordBoundary")
        async for chunk in comm.stream():
            if chunk["type"] == "WordBoundary":
                w_start = offset + (chunk["offset"] / 10_000_000)
                w_dur = chunk["duration"] / 10_000_000
                all_words.append({
                    "scene": idx + 1,
                    "word": chunk["text"],
                    "start": round(w_start, 3),
                    "end": round(w_start + w_dur, 3),
                    "dur": round(w_dur, 3)
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
Title: Stickman Universe Rock-Solid Kinetic Captions
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,72,&H00FFFFFF,&H0000EEFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,3,2,60,60,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for p in phrases:
        words = p["words"]
        for active_idx in range(len(words)):
            # Monotonic contiguous timing: no overlaps!
            w_start = words[active_idx]["start"]
            if active_idx < len(words) - 1:
                w_end = words[active_idx + 1]["start"]
            else:
                w_end = words[active_idx]["end"]

            start_str = format_ass_time(w_start)
            end_str = format_ass_time(w_end)

            line_parts = []
            for j, w in enumerate(words):
                w_clean = w["word"].upper()
                if j == active_idx:
                    # Active word in bright gold-yellow, NO scaling
                    line_parts.append(f"{{\\c&H0000EEFF&}}{w_clean}{{\\rDefault}}")
                else:
                    line_parts.append(f"{{\\c&H00FFFFFF&}}{w_clean}")

            text_line = " ".join(line_parts)
            events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_line}")

    return header + "\n".join(events)

async def main():
    print("=======================================================")
    print("🎬 PRODUCING EPISODE 03: THE TETRIS EFFECT")
    print("=======================================================")

    # 1. Words & Subtitles
    words = await extract_words()
    print(f"✅ Extracted {len(words)} word timestamps.")

    json_path = os.path.join(SUB_DIR, "stickman_captions_words.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved: {json_path}")

    phrases = build_phrases(words, max_words=3)
    
    srt_path = os.path.join(SUB_DIR, "stickman_captions.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(generate_srt(phrases))
    print(f"✅ Saved: {srt_path}")

    ass_path = os.path.join(SUB_DIR, "stickman_captions.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(generate_ass(phrases))
    print(f"✅ Saved: {ass_path}")

    # 2. Stage raw 720p
    raw_720p = os.path.join(VIDEO_DIR, "raw_flow_720p.mp4")
    import shutil
    shutil.copy2(RAW_VIDEO, raw_720p)
    print(f"✅ Staged raw 720p copy: {raw_720p}")

    # 3. Clean 1080p Lanczos upscale (UNCUT, NO LOGO)
    raw_1080p = os.path.join(VIDEO_DIR, "raw_flow_1080p.mp4")
    print("🚀 Upscaling to 1080x1920 (Lanczos High Quality)...")
    cmd_1080 = [
        "ffmpeg", "-y", "-i", RAW_VIDEO,
        "-vf", "scale=1080:1920:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
        raw_1080p
    ]
    subprocess.run(cmd_1080, check=True)
    print(f"✅ Created clean 1080p: {raw_1080p}")

    # 4. Burn kinetic Montserrat-Bold subtitles onto 1080p
    subtitled_1080p = os.path.join(VIDEO_DIR, "stickman_shorts_1080p_subtitled.mp4")
    print("📝 Burning Montserrat-Bold subtitles into 1080p master...")
    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    cmd_sub = [
        "ffmpeg", "-y", "-i", raw_1080p,
        "-vf", f"ass='{escaped_ass}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-c:a", "copy",
        "-movflags", "+faststart",
        subtitled_1080p
    ]
    subprocess.run(cmd_sub, check=True)
    print(f"🎉 Created subtitled master: {subtitled_1080p}")
    print("\n=======================================================")
    print("🏆 ALL EPISODE 03 DELIVERABLES COMPLETED SUCCESSFULLY!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
