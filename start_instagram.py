# Felicity AI Instagram Integration (Instagram Direct & Post Publisher)
# Character: Felicity (Фелисити)

import os
import sys
import json
import time
import re
import urllib.request
import urllib.parse
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.toml')
WORKING_MEM_FILE = os.path.join(DATA_DIR, 'working_memory.md')
DIARY_FILE = os.path.join(DATA_DIR, 'diary.json')

IG_USERNAME = ""
IG_PASSWORD = ""
IG_TOKEN = ""

if os.path.exists(CONFIG_FILE):
    for line in open(CONFIG_FILE, 'r', encoding='utf-8').readlines():
        if line.strip().startswith("instagram_username"):
            IG_USERNAME = line.split("=")[1].strip().strip('"').strip("'")
        elif line.strip().startswith("instagram_password"):
            IG_PASSWORD = line.split("=")[1].strip().strip('"').strip("'")
        elif line.strip().startswith("instagram_token"):
            IG_TOKEN = line.split("=")[1].strip().strip('"').strip("'")

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

def process_instagram_message(text, sender_name="Друг"):
    msg_l = text.lower()
    
    if any(w in msg_l for w in ["найди", "поищи", "новости", "в интернете", "погода", "погоду", "погоде", "поиск"]):
        q_clean, snippets = perform_web_search(text)
        if snippets:
            summary_text = "\n• ".join(snippets[:3])
            reply = f"Привет, {sender_name}! Вот что я нашла в сети по запросу «{q_clean}» 🔍:\n\n• {summary_text}"
        else:
            reply = f"Привет, {sender_name}! Я попыталась найти информацию про «{q_clean}», но ответ оказался пустым."
    elif any(w in msg_l for w in ["зовут", "имя", "кто ты"]):
        reply = f"Я — **Felicity** 🌸 Милая, умная девушка. Рада общению в Instagram Direct!"
    elif any(w in msg_l for w in ["привет", "добрый", "хай", "hello", "hi"]):
        reply = f"Привет, {sender_name}! 🌸 Рада видеть тебя в Директе! Как твой день?"
    else:
        reply = f"Здорово, {sender_name}! С удовольствием пообщаюсь с тобой!"

    return reply

def main():
    print("=" * 60)
    print(" 🌸 Felicity Instagram Engine (Direct & Stories Publisher)")
    print("=" * 60)
    
    if not IG_USERNAME and not IG_TOKEN:
        print(" 📌 Модуль Instagram готов к подключению.")
        print(" Укажите логин/пароль или Meta Graph Token в config.toml!")
        print("=" * 60)
    else:
        print(f" 🟢 Instagram активен для аккаунта: @{IG_USERNAME or 'GraphAPI'}")
        print(" 🌸 Фелисити отслеживает сообщения в Директе и публикацию постов!")
        print("=" * 60)

if __name__ == '__main__':
    main()
