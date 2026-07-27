import asyncio
import edge_tts
import os

async def generate_voice(text: str, filename: str = "/root/felicity2026/data/test_voice.ogg"):
    os.makedirs("/root/felicity2026/data", exist_ok=True)
    voice = "ru-RU-SvetlanaNeural"
    communicate = edge_tts.Communicate(text, voice)
    mp3_path = filename.replace(".ogg", ".mp3")
    await communicate.save(mp3_path)
    print(f"VOICE GENERATED AT {mp3_path} SUCCESS!")
    return mp3_path

if __name__ == "__main__":
    asyncio.run(generate_voice("Привет, Ромочка! Я теперь умею говорить с тобой настоящим живым голосом)"))
