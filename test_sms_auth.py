import asyncio
import sys
from telethon import TelegramClient

sys.stdout.reconfigure(encoding='utf-8')

async def test():
    client = TelegramClient(
        'test_sess',
        2040,
        'b18441a12607e101456b635617cc838d',
        device_model="Android",
        system_version="13.0",
        app_version="10.8.1",
        lang_code="ru"
    )
    await client.connect()
    print("Connected successfully!")
    try:
        res = await client.send_code_request('+79040985006')
        print(" SUCCESS! Code sent! Hash:", res.phone_code_hash)
    except Exception as e:
        print(" Error:", type(e), e)
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(test())
