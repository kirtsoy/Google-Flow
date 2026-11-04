import os, sys, json, asyncio, subprocess
import edge_tts

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

UNIVERSE_DIR = r"C:\Users\kiril\Downloads\STICKMAN UNIVERSE"
INPUT_VIDEO = os.path.join(UNIVERSE_DIR, "stickman_shorts_9x16.mp4")
UPSCALED_1080P = os.path.join(UNIVERSE_DIR, "stickman_shorts_1080x1920.mp4")
OUTPUT_SUBTITLED_MP4 = os.path.join(UNIVERSE_DIR, "stickman_shorts_1080p_subtitled.mp4")
ASS_FILE = os.path.join(UNIVERSE_DIR, "stickman_captions.ass")
SRT_FILE = os.path.join(UNIVERSE_DIR, "stickman_captions.srt")
JSON_FILE = os.path.join(UNIVERSE_DIR, "stickman_captions_words.json")

SCENES = [
    "In free-to-play video games, millions of players willingly spend billions on digital skins.",
    "Virtual skins offer zero competitive advantage, yet players desire them just like designer clothes.",
    "Unlocking rare cosmetic drops triggers the same social status dopamine as buying luxury fashion brands.",
    "For thousands of years, humans used decorative ornaments to signal tribal prestige and personal identity.",
    "In virtual worlds, your skin is your digital face, communicating dedication, taste, and social clout.",
    "Psychologists call this the endowment effect, where customizing an avatar creates deep emotional ownership.",
    "Humans buy game skins because self-expression and belonging are just as real in digital spaces."
]

async def extract_word_timestamps():
    print("🎙 Extracting ground-truth word timestamps from Charon neural engine...")
    all_words = []
    for i, text in enumerate(SCENES):
        scene_offset = i * 8.0 + 0.20
        comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", boundary="WordBoundary")
        async for chunk in comm.stream():
            if chunk["type"] == "WordBoundary":
                start = scene_offset + (chunk["offset"] / 10000000)
                dur = chunk["duration"] / 10000000
                all_words.append({
                    "scene": i + 1,
                    "word": chunk["text"],
                    "start": round(start, 3),
                    "end": round(start + dur, 3),
                    "dur": round(dur, 3)
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

def group_words_into_phrases(words, max_words=3):
    phrases = []
    for scene_id in range(1, 8):
        scene_words = [w for w in words if w["scene"] == scene_id]
        for i in range(0, len(scene_words), max_words):
            chunk = scene_words[i:i + max_words]
            if not chunk:
                continue
            phrases.append({
                "scene": scene_id,
                "start": chunk[0]["start"],
                "end": chunk[-1]["end"] + 0.15,
                "words": chunk
            })
    return phrases

def generate_ass(phrases):
    """
    Builds professional TikTok/Shorts kinetic captions:
    - Font: Montserrat Black / Arial Black (76px)
    - Colors: Bright White (&H00FFFFFF), Neon Yellow active highlight (&H0000EEFF)
    - Outline: Solid Black 5px, Shadow: 3px
    - Position: Alignment 2 (Bottom Center), MarginV 360px (Safe zone above profile/captions)
    """
    header = """[Script Info]
Title: Stickman Shorts Viral Kinetic Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat,72,&H00FFFFFF,&H0000EEFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,5,3,2,60,60,380,1
Style: Highlight,Montserrat,78,&H0000EEFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,105,105,2,0,1,6,4,2,60,60,380,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for p in phrases:
        for active_idx, target_word in enumerate(p["words"]):
            w_start = format_ass_time(target_word["start"])
            w_end = format_ass_time(target_word["end"])
            
            line_parts = []
            for j, w in enumerate(p["words"]):
                if j == active_idx:
                    # Neon Yellow active word with slight scale pop
                    line_parts.append(f"{{\\c&H0000EEFF&\\fscx108\\fscy108}}{w['word'].upper()}{{\\rDefault}}")
                else:
                    # Clean white word with black border
                    line_parts.append(f"{{\\c&H00FFFFFF&\\fscx100\\fscy100}}{w['word'].upper()}")
            
            text_str = " ".join(line_parts)
            events.append(f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{text_str}")
            
    return header + "\n".join(events)

def generate_srt(phrases):
    lines = []
    idx = 1
    for p in phrases:
        start_str = format_srt_time(p["start"])
        end_str = format_srt_time(p["end"])
        text = " ".join(w["word"] for w in p["words"]).upper()
        lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")
        idx += 1
    return "\n".join(lines)

async def main():
    if not os.path.exists(INPUT_VIDEO):
        print(f"[FAIL] Input video not found at: {INPUT_VIDEO}")
        return

    print("=======================================================")
    print("🚀 STICKMAN UNIVERSE — 1080P UPSCALE & CAPTIONS SUITE")
    print("=======================================================")
    print(f"📁 Source: {INPUT_VIDEO}")

    # 1. Generate timestamps
    words = await extract_word_timestamps()
    print(f"[OK] Extracted {len(words)} word timestamps.")

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved: {JSON_FILE}")

    # 2. Build phrase groups
    phrases = group_words_into_phrases(words, max_words=3)
    
    # 3. Write ASS & SRT
    ass_content = generate_ass(phrases)
    with open(ASS_FILE, "w", encoding="utf-8") as f:
        f.write(ass_content)
    print(f"[OK] Saved: {ASS_FILE}")

    srt_content = generate_srt(phrases)
    with open(SRT_FILE, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"[OK] Saved: {SRT_FILE}")

    print("\n=======================================================")
    print("✨ ALL SUBTITLE & TIMING ASSETS READY!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(main())
