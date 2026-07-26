# Felicity AI Telegram Client (QR Code & Userbot Integration)
# Character: Felicity (Фелисити)

import os
import sys
import asyncio
import json
import re
import urllib.request
import urllib.parse
from telethon import TelegramClient, events
import qrcode

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.toml')
SESSION_FILE = os.path.join(BASE_DIR, 'felicity_tg_session')
QR_IMAGE_FILE = os.path.join(BASE_DIR, 'qr_login.png')

# Official Telegram Web credentials
API_ID = 2496
API_HASH = "8da85b0d5bfe62527e5b244c20f15d01"

if os.path.exists(CONFIG_FILE):
    for line in open(CONFIG_FILE, 'r', encoding='utf-8').readlines():
        if line.strip().startswith("telegram_api_id"):
            try:
                val = int(line.split("=")[1].strip())
                if val > 0:
                    API_ID = val
            except Exception:
                pass
        elif line.strip().startswith("telegram_api_hash"):
            val_str = line.split("=")[1].strip().strip('"').strip("'")
            if val_str:
                API_HASH = val_str

client = TelegramClient(
    SESSION_FILE,
    API_ID,
    API_HASH,
    device_model="Desktop",
    system_version="Windows 11",
    app_version="4.16.30",
    lang_code="ru"
)

def perform_web_search(user_query):
    query_clean = re.sub(r'([a-zа-я])([A-ZА-Я])', r'\1 \2', user_query)
    query_clean = re.sub(r'(найди|поищи|в интернете|новости|поиск|гугл|информация о|про|что-то|что|какая|какой)', '', query_clean, flags=re.IGNORECASE).strip()
    if not query_clean:
        query_clean = user_query

    snippets = []
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = urllib.parse.urlencode({'q': query_clean}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            rows = re.findall(r'<td[^>]*class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>', html, re.DOTALL)
            if not rows:
                rows = re.findall(r'<td[^>]*>\s*([А-Яа-яA-Za-z0-9\s\.,\-—–\:\%\+\°\«\»]+)\s*</td>', html)
            for r in rows:
                t = re.sub(r'<[^>]+>', '', r).strip()
                t = re.sub(r'\s+', ' ', t)
                if t and len(t) > 20 and not any(skip in t.lower() for skip in ['duckduckgo', 'javascript']):
                    snippets.append(t)
    except Exception:
        pass
    return query_clean, snippets

@client.on(events.NewMessage)
async def handle_new_message(event):
    if not event.is_private and not event.mentioned:
        return
    
    sender = await event.get_sender()
    sender_name = getattr(sender, 'first_name', 'Друг') or 'Друг'
    text = event.text or ''
    if not text.strip():
        return

    msg_l = text.lower()

    if any(w in msg_l for w in ["найди", "поищи", "новости", "в интернете", "погода", "погоду", "погоде", "поиск"]):
        q_clean, snippets = perform_web_search(text)
        if snippets:
            summary_text = "\n• ".join(snippets[:3])
            reply = f"{sender_name}, вот что я нашла в сети по запросу **«{q_clean}»** 🔍:\n\n• {summary_text}"
        else:
            reply = f"{sender_name}, я попыталась найти информацию про **«{q_clean}»**, но ответ оказался пустым."
    
    elif any(w in msg_l for w in ["зовут", "имя", "кто ты", "как тебя"]):
        reply = f"Меня зовут **Фелисити (Felicity)** 🌸 Я открытая, умная девушка. Рада нашему общению, {sender_name}! 😊"

    elif any(w in msg_l for w in ["привет", "здравствуй", "добрый", "хай", "hello", "hi"]):
        reply = f"Привет-привет, {sender_name}! ☕ Рада тебя видеть! Как твои дела?"

    elif any(w in msg_l for w in ["как дела", "как ты", "настроение"]):
        reply = f"У меня всё отлично, {sender_name}! Очень рада поболтать с тобой 🌸 А как твой день?"

    else:
        reply = f"{sender_name}, здорово! С удовольствием пообщаюсь с тобой на эту тему 😊"

    await asyncio.sleep(1.5)
    await event.reply(reply)

async def main():
    print("=" * 60)
    print(" 🌸 Starting Felicity Telegram Client...")
    print("=" * 60)
    
    await client.connect()
    if not await client.is_user_authorized():
        print(" 📱 Авторизация через QR-код Telegram (без ошибок с кодами)...")
        qr_login = await client.qr_login()
        
        # Save QR code image for user to double click and view
        img = qrcode.make(qr_login.url)
        img.save(QR_IMAGE_FILE)
        
        print("\n" + "=" * 60)
        print(" 📷 QR-код для входа сохранен в файл:")
        print(f" 📁 {QR_IMAGE_FILE}")
        print("=" * 60)
        print(" Откройте Telegram на телефоне:")
        print(" Настройки -> Устройства -> Подключить устройство")
        print(" И отсканируйте сохраненный файл qr_login.png или этот QR-код:")
        print("=" * 60 + "\n")
        
        # Also print ASCII QR in console
        qr_ascii = qrcode.QRCode()
        qr_ascii.add_data(qr_login.url)
        qr_ascii.print_ascii(invert=True)
        
        try:
            user = await qr_login.wait()
        except Exception as e:
            if "password" in str(e).lower():
                pwd = input(" 🔒 Введите пароль облачной защиты (2FA): ").strip()
                user = await client.sign_in(password=pwd)
            else:
                print(f" Ошибка авторизации: {e}")
                return

    me = await client.get_me()
    print("=" * 60)
    print(f" 🟢 Успешно вошли как: {me.first_name} (@{me.username or 'без юзернейма'})")
    print(" 🌸 Фелисити теперь ОНЛАЙН в Telegram и готова отвечать на сообщения!")
    print("=" * 60)
    
    # Remove QR file after success
    if os.path.exists(QR_IMAGE_FILE):
        try:
            os.remove(QR_IMAGE_FILE)
        except Exception:
            pass

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
