import asyncio
import felicity_userbot

async def run_selfie_test():
    await felicity_userbot.client.start()
    res = await felicity_userbot.generate_and_send_selfie("romqqqa1")
    print("SELFIE TEST RESULT:", res)

if __name__ == "__main__":
    asyncio.run(run_selfie_test())
