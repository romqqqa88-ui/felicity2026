import asyncio
import felicity_userbot

async def run_video_note_test():
    await felicity_userbot.client.start()
    print("EXECUTING LIVE TELEGRAM VIDEO NOTE TEST...")
    res = await felicity_userbot.generate_and_send_video_note("romqqqa1", "Ромочка! Записываю тебе настоящий круглый видео-кружочек! Смотри, как здорово получилось)")
    print("VIDEO NOTE TEST RESULT:", res)

if __name__ == "__main__":
    asyncio.run(run_video_note_test())
