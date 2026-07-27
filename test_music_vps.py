import asyncio
import felicity_userbot

async def run_music_test():
    await felicity_userbot.client.start()
    res = await felicity_userbot.generate_and_send_music_track("romqqqa1")
    print("MUSIC TEST RESULT:", res)

if __name__ == "__main__":
    asyncio.run(run_music_test())
