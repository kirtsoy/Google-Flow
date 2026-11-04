import asyncio
import os
import edge_tts

STORIES = {
    "ancient_humans": {
        "voice": "en-US-ChristopherNeural",
        "scenes": [
            {
                "id": 1,
                "text": "Thousands of years ago, survival was a daily test against the harsh prehistoric wilderness."
            },
            {
                "id": 2,
                "text": "Alone on the plains, one hunter struggled to find food without any help."
            },
            {
                "id": 3,
                "text": "A fierce predator appeared from the tall grass, easily overpowering the isolated solitary hunter."
            },
            {
                "id": 4,
                "text": "Early humans realized that solitary wanderers could never survive against constant wilderness hazards."
            },
            {
                "id": 5,
                "text": "In small bands, hunters shared tasks, gathered diverse foods, and protected each other continuously."
            },
            {
                "id": 6,
                "text": "Living together allowed them to pass down crucial survival skills across every single generation."
            },
            {
                "id": 7,
                "text": "Ancient humans stayed in groups because cooperation was their greatest weapon for collective survival."
            }
        ]
    },
    "warcraft_arthas": {
        "voice": "en-US-GuyNeural",
        "scenes": [
            {
                "id": 1,
                "text": "Prince Arthas was the golden hope of Lordaeron, sworn to protect his beloved people."
            },
            {
                "id": 2,
                "text": "A horrific plague of undeath swept across the kingdom, turning citizens into savage monsters."
            },
            {
                "id": 3,
                "text": "Desperate for victory, Arthas abandoned his mentors and pursued vengeance into the frozen North."
            },
            {
                "id": 4,
                "text": "In the icy wastes of Northrend, he discovered a cursed runeblade known as Frostmourne."
            },
            {
                "id": 5,
                "text": "The blade granted immense dark power, but claimed the young prince's immortal soul."
            },
            {
                "id": 6,
                "text": "Returning home in dark armor, the fallen prince slaughtered his father and claimed the throne."
            },
            {
                "id": 7,
                "text": "Ascending the Frozen Throne, Arthas merged with the Lich King, sealing his tragic doom."
            }
        ]
    }
}

async def generate():
    os.makedirs("audio", exist_ok=True)
    for story_key, data in STORIES.items():
        voice = data["voice"]
        print(f"Generating voiceover for {story_key} using {voice}...")
        for scene in data["scenes"]:
            out_file = f"audio/{story_key}_s{scene['id']}.mp3"
            comm = edge_tts.Communicate(scene["text"], voice)
            await comm.save(out_file)
            print(f"  [OK] Saved {out_file}")

if __name__ == "__main__":
    asyncio.run(generate())
