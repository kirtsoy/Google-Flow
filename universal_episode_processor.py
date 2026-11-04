import os, sys, json, subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

UNIVERSE_ROOT = r"C:\Users\kiril\Downloads\STICKMAN UNIVERSE"
EPISODES_DIR = os.path.join(UNIVERSE_ROOT, "EPISODES")

def get_latest_episode_dir():
    dirs = [os.path.join(EPISODES_DIR, d) for d in os.listdir(EPISODES_DIR) if os.path.isdir(os.path.join(EPISODES_DIR, d))]
    dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return dirs[0] if dirs else None

def upscale_lanczos_1080p(input_path, output_path):
    print("🚀 Upscaling to 1080x1920 (Lanczos High Quality + NLE-Friendly GOP)...")
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-vf", "scale=1080:1920:flags=lanczos",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-g", "24", "-keyint_min", "24",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Created 1080p master: {output_path}")
    return output_path

def burn_subtitles_1080p(video_path, ass_path, output_path):
    print("📝 Burning clean Montserrat-Bold kinetic subtitles (NLE-Friendly GOP)...")
    escaped_ass = ass_path.replace("\\", "/").replace(":", "\\:")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"ass='{escaped_ass}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-g", "24", "-keyint_min", "24",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Created subtitled 1080p master: {output_path}")
    return output_path

def process_episode(ep_dir):
    print("=======================================================")
    print(f"🎬 PROCESSING EPISODE: {os.path.basename(ep_dir)}")
    print("=======================================================")

    raw_video = None
    for candidate in ["stickman_shorts_9x16.mp4", "raw_flow_720p.mp4"]:
        p = os.path.join(ep_dir, candidate)
        if os.path.exists(p):
            raw_video = p
            break
        p_sub = os.path.join(ep_dir, "video", candidate)
        if os.path.exists(p_sub):
            raw_video = p_sub
            break

    if not raw_video:
        print(f"[WARN] No raw export found yet in {ep_dir}")
        print("👉 Please download or copy stickman_shorts_9x16.mp4 into the episode folder first.")
        return

    video_dir = os.path.join(ep_dir, "video")
    subtitles_dir = os.path.join(ep_dir, "subtitles")
    os.makedirs(video_dir, exist_ok=True)

    # 1. Standard 720p copy
    raw_720p = os.path.join(video_dir, "raw_flow_720p.mp4")
    if os.path.abspath(raw_video) != os.path.abspath(raw_720p):
        import shutil
        shutil.copy2(raw_video, raw_720p)
        print(f"✅ Staged raw 720p copy: {raw_720p}")

    # 2. Clean 1080p Lanczos upscale (UNCUT, NO LOGO)
    raw_1080p = os.path.join(video_dir, "raw_flow_1080p.mp4")
    upscale_lanczos_1080p(raw_video, raw_1080p)

    # 3. Subtitled 1080p Master (if .ass exists)
    ass_path = os.path.join(subtitles_dir, "stickman_captions.ass")
    if os.path.exists(ass_path):
        subtitled_1080p = os.path.join(video_dir, "stickman_shorts_1080p_subtitled.mp4")
        burn_subtitles_1080p(raw_1080p, ass_path, subtitled_1080p)

    print("\n🎉 EPISODE PROCESSING COMPLETED SUCCESSFULLY!")

def main():
    ep_dir = sys.argv[1] if len(sys.argv) > 1 else get_latest_episode_dir()
    if not ep_dir or not os.path.isdir(ep_dir):
        print(f"[ERROR] Episode directory not found: {ep_dir}")
        return
    process_episode(ep_dir)

if __name__ == "__main__":
    main()
