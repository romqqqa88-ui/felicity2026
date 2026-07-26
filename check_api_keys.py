import asyncio
from telethon import TelegramClient

keys = [
    (611335, "d524b5078213285e6834b6890f6b3b55", "Android", "10.8.1 (4521)"),
    (21724, "3e0cb5efcd52300aec5994fdfc5bdc16", "Desktop", "4.16.30"),
    (2040, "b18441a12607e101456b635617cc838d", "Samsung SM-S901B", "Android 13")
]

async def check():
    for api_id, api_hash, device, app_v in keys:
        print(f"Testing api_id={api_id}...")
        client = TelegramClient(
            f'test_{api_id}',
            api_id,
            api_hash,
            device_model=device,
            system_version="13.0",
            app_version=app_v,
            lang_code="ru"
        )
        try:
            await client.connect()
            qr = await client.qr_login()
            print(f" SUCCESS for api_id={api_id}! QR URL generated: {qr.url[:30]}...")
            await client.disconnect()
            return api_id, api_hash, device, app_v
        except Exception as e:
            print(f" Failed for api_id={api_id}: {e}")
            try:
                await client.disconnect()
            except Exception:
                pass

if __name__ == '__main__':
    asyncio.run(check())
