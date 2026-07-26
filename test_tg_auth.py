import asyncio
import os
import sys
import qrcode
from telethon import TelegramClient

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(BASE_DIR, 'felicity_tg_session')

# Web App Credentials
API_ID = 2496
API_HASH = "8da85b0d5bfe62527e5b244c20f15d01"

client = TelegramClient(
    SESSION_FILE,
    API_ID,
    API_HASH,
    device_model="Web Client",
    system_version="Windows 11",
    app_version="1.0.0",
    lang_code="ru"
)

async def main():
    await client.connect()
    print("Is authorized:", await client.is_user_authorized())
    if not await client.is_user_authorized():
        print("Testing QR login or Code request...")
        qr = await client.qr_login()
        print("QR URL:", qr.url)
        # Generate ASCII QR code
        qr_img = qrcode.QRCode()
        qr_img.add_data(qr.url)
        qr_img.print_ascii(invert=True)

if __name__ == '__main__':
    asyncio.run(main())
