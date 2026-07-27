import asyncio
import felicity_userbot

async def run_voice_test():
    await felicity_userbot.client.start()
    res = await felicity_userbot.generate_and_send_voice_note("romqqqa1", "Ромочка, родной мой! Привет) Записываю тебе первое настоящее голосовое сообщение, чтобы ты услышал мой живой голос!")
    print("VOICE TEST RESULT:", res)

if __name__ == "__main__":
    asyncio.run(run_voice_test())
