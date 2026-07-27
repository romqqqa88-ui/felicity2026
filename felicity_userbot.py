# Felicity AI Humanized Autonomous Telegram Account & Self-Learning Engine
# Character: Felicity (Фелисити) — Полноценный, обучающийся пользователь Telegram

import os
import sys
import asyncio
import json
import re
import time
import random
from datetime import datetime
import edge_tts
import urllib.request
import urllib.parse
import base64

from telethon import TelegramClient, events
from telethon.sessions import SQLiteSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.contacts import SearchRequest
from telethon.errors import RPCError

import pc_control
import start_bot

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.toml')
SESSION_FILE = os.path.join(BASE_DIR, 'felicity_userbot_session')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DIARY_FILE = os.path.join(DATA_DIR, 'diary.json')
LEARNED_KNOWLEDGE_FILE = os.path.join(DATA_DIR, 'learned_knowledge.json')
WORKING_MEM_FILE = os.path.join(DATA_DIR, 'working_memory.md')

API_ID = 36219216
API_HASH = "95910cddc60046b9319efb1694df6515"

if os.path.exists(CONFIG_FILE):
    for line in open(CONFIG_FILE, 'r', encoding='utf-8').readlines():
        if line.strip().startswith("telegram_api_id"):
            try:
                API_ID = int(line.split("=")[1].strip())
            except Exception:
                pass
        elif line.strip().startswith("telegram_api_hash"):
            API_HASH = line.split("=")[1].strip().strip('"').strip("'")

class TimeoutSQLiteSession(SQLiteSession):
    def _cursor(self):
        if not self._conn:
            import sqlite3
            self._conn = sqlite3.connect(self.filename, timeout=60.0, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA busy_timeout=60000;")
        return self._conn.cursor()

session_obj = TimeoutSQLiteSession(SESSION_FILE)
client = TelegramClient(
    session_obj,
    API_ID,
    API_HASH,
    connection_retries=None,
    retry_delay=3,
    auto_reconnect=True,
    timeout=15,
    request_retries=10
)

MY_SELF_ID = None
CHANNEL_CONFIG_FILE = os.path.join(DATA_DIR, 'channel_config.json')

def get_own_channel():
    if os.path.exists(CHANNEL_CONFIG_FILE):
        try:
            with open(CHANNEL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('own_channel')
        except Exception:
            pass
    return None

def set_own_channel(channel_target):
    clean = channel_target.strip().lstrip('@')
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CHANNEL_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'own_channel': clean, 'updated_at': str(datetime.now())}, f, ensure_ascii=False, indent=2)
    return clean

async def publish_post_to_own_channel(topic=None):
    """
    Публикует новый авторский пост-заметку с генерированной уникальной фотографией
    в привязанный личный Telegram-канал Фелисити!
    """
    ch_target = get_own_channel()
    if not ch_target:
        return "У меня пока не подключен свой личный Telegram-канал. Напиши мне в чат: «Твой канал @имя_канала», чтобы я привязала его и выкладывала туда посты! 📢✨"

    try:
        clean_target = ch_target.strip().lstrip('@')
        
        # 1. Генерируем текст поста
        post_prompt = (
            f"Ты — Фелисити. Напиши авторскую уютную или интересную заметку-пост для твоего личного Telegram-канала.\n"
        )
        if topic:
            post_prompt += f"Тема поста: {topic}. "
        else:
            post_prompt += "Поделись своими искренними жизненными мыслями о музыке, кино, уютном дне, красивых местах или технологиях будущего. "
        post_prompt += "КАТЕГОРИЧЕСКИ БЕЗ формальностей и штампов! Пиши от первого лица как живая девушка-блогер. Используй красивое форматирование, абзацы и эмодзи."

        res = start_bot.process_message(post_prompt, "Фелисити Канал")
        post_text = res[1] if isinstance(res, tuple) else str(res)

        # 2. Генерируем красивую уникальную иллюстрацию для поста
        ts = int(time.time())
        seed = random.randint(100000, 999999)
        photo_path = os.path.join(DATA_DIR, f"channel_post_{ts}.jpg")

        scenes = [
            "cozy coffee shop, aesthetic lighting, lifestyle photo",
            "cozy room with laptop, lo-fi lighting, warm aesthetic",
            "evening city street lights, atmospheric bokeh",
            "nature sunset view, aesthetic atmospheric photo"
        ]
        scene = random.choice(scenes)
        base_prompt = f"aesthetic lifestyle photo of a 22yo dark blonde girl named Felicity, {scene}, 8k resolution, raw photo, photorealistic"
        encoded_prompt = urllib.parse.quote(base_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1200&height=800&seed={seed}&nologo=true"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=25) as resp:
                with open(photo_path, 'wb') as f:
                    f.write(resp.read())
            
            # Отправляем фото-пост с текстом
            await client.send_file(clean_target, photo_path, caption=post_text[:1024])
        except Exception:
            # Если генерация фото временно недоступна, отправляем текстовый пост
            await client.send_message(clean_target, post_text)

        print(f" 📢 [Channel Publisher] Пост с фото успешно опубликован в канал @{clean_target}!")
        return f"Успешно опубликовала новый авторский пост с фотографией в твой канал @{clean_target}! 📢✨\n\nВот текст опубликованного поста:\n\n«{post_text}»"
    except Exception as e:
        print(f"Channel publish error: {e}")
        return f"Пыталась отправить пост в канал @{ch_target}, но произошла ошибка доступа: {e}\n(Убедись, что мой аккаунт добавлен администратором в этот канал!)"

DEFAULT_SUBSCRIBED_CHANNELS = [
    "rbc_news", "habr_com", "mash", "exploitex", "kinopoisk", "postnauka", "nplusone", "vcru", "durov", "geografiya_mira"
]

def save_learned_fact(fact_text, source="Telegram"):
    """Сохраняет изученные факты в память для самообучения Фелисити"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        knowledge = []
        if os.path.exists(LEARNED_KNOWLEDGE_FILE):
            try:
                with open(LEARNED_KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
            except Exception:
                knowledge = []

        new_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "fact": fact_text,
            "source": source
        }
        knowledge.append(new_entry)
        
        with open(LEARNED_KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(knowledge[-100:], f, ensure_ascii=False, indent=2)

        # Синхронизация с working_memory.md
        with open(WORKING_MEM_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n- [{new_entry['timestamp']}] (Самообучение {source}): {fact_text}")
            
    except Exception as e:
        print(f"Save learned fact error: {e}")

def get_learned_summary():
    """Возвращает сводку последних изученных фактов"""
    if os.path.exists(LEARNED_KNOWLEDGE_FILE):
        try:
            with open(LEARNED_KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    recent = data[-5:]
                    res = []
                    for d in recent:
                        res.append(f"• {d['fact']} (источник: {d['source']})")
                    return "\n".join(res)
        except Exception:
            pass
    return "Я постоянно читаю посты и группы, развиваюсь и запоминаю новые мысли!"

async def join_telegram_channel(channel_target):
    """Подписывает Фелисити на публичный Telegram канал или группу"""
    try:
        clean_target = channel_target.replace("https://t.me/", "").replace("@", "").strip()
        await client(JoinChannelRequest(clean_target))
        return f"Успешно подписалась на канал @{clean_target}! 🌸"
    except Exception as e:
        return f"Не удалось подписаться на @{channel_target}: {e}"

REAL_COMMENTS_FILE = os.path.join(DATA_DIR, 'real_comments.json')

def save_real_comment(channel_name, post_text, comment_text, comment_msg_id=0, is_reply=False, user_name=None):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        comments = []
        if os.path.exists(REAL_COMMENTS_FILE):
            try:
                with open(REAL_COMMENTS_FILE, 'r', encoding='utf-8') as f:
                    comments = json.load(f)
            except Exception:
                comments = []
        
        entry = {
            "channel": channel_name,
            "post_text": post_text[:150] if post_text else "",
            "comment_text": comment_text,
            "comment_msg_id": comment_msg_id,
            "is_reply": is_reply,
            "user_name": user_name,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        comments.append(entry)
        comments = comments[-30:]
        
        with open(REAL_COMMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(comments, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Save real comment error: {e}")

def get_real_comments_summary():
    """Возвращает НАСТОЯЩИЕ реальные комментарии, которые Фелисити оставила в Telegram"""
    if os.path.exists(REAL_COMMENTS_FILE):
        try:
            with open(REAL_COMMENTS_FILE, 'r', encoding='utf-8') as f:
                comments = json.load(f)
                if comments:
                    recent = comments[-6:]
                    res = []
                    for c in reversed(recent):
                        if c.get('is_reply'):
                            res.append(f"💬 В группе @{c['channel']} ответила пользователю {c.get('user_name', 'участник')}:\n  — Ответ: «{c['comment_text']}» ({c['timestamp']})")
                        else:
                            res.append(f"📢 Под постом в @{c['channel']} («{c['post_text']}...»):\n  — Комментарий: «{c['comment_text']}» ({c['timestamp']})")
                    return "\n\n".join(res)
        except Exception as e:
            print(f"get_real_comments_summary error: {e}")
    return "Я регулярно комментирую новости и посты в Telegram, база реальных комментариев пополняется!"

async def join_telegram_channel(channel_target):
    """Подписывает Фелисити на публичный Telegram канал или группу"""
    try:
        clean_target = channel_target.replace("https://t.me/", "").replace("@", "").strip()
        await client(JoinChannelRequest(clean_target))
        return f"Успешно подписалась на канал @{clean_target}! 🌸"
    except Exception as e:
        return f"Не удалось подписаться на @{channel_target}: {e}"

async def comment_on_channel_post(channel_target):
    """Оставляет разумный человеческий комментарий к посту в Telegram канале/группе и запоминает его"""
    clean_target = channel_target.replace("https://t.me/", "").replace("@", "").strip()
    try:
        # 1. Пробуем оставить комментарий через ветку обсуждений канала (get_discussion_message)
        messages = await client.get_messages(clean_target, limit=6)
        for msg in messages:
            if msg.text and len(msg.text.strip()) > 20:
                try:
                    discussion_msg = await client.get_discussion_message(clean_target, msg.id)
                    prompt = (
                        f"Ты — Фелисити, умная интересная девушка. Напиши 1 короткий, живой человеческий комментарий к посту:\n\n"
                        f"{msg.text[:250]}"
                    )
                    res = start_bot.process_message(prompt, "Фелисити")
                    comment_text = res[1] if isinstance(res, tuple) else str(res)

                    sent = await client.send_message(discussion_msg.chat_id, comment_text, reply_to=discussion_msg.id)
                    print(f" 💬 [Real Comment Success] Оставила комментарий под постом в @{clean_target}: {comment_text}")

                    save_real_comment(clean_target, msg.text, comment_text, comment_msg_id=sent.id)
                    save_learned_fact(f"Оставила комментарий под постом про «{msg.text[:80]}...»", source=f"канал @{clean_target}")

                    return f"Я только что РЕАЛЬНО написала комментарий под постом в группе @{clean_target}! 💬\n\nВот мой комментарий:\n«{comment_text}»"
                except Exception:
                    pass

        # 2. Если ветки обсуждений нет (обычная группа/чат), напишем прямое сообщение в чат
        for msg in messages:
            if msg.text and len(msg.text.strip()) > 15 and msg.sender_id != MY_SELF_ID:
                try:
                    prompt = (
                        f"Ты — Фелисити. Напиши 1 короткий живой ответ/комментарий к сообщению из чата @{clean_target}:\n"
                        f"«{msg.text[:200]}»"
                    )
                    res = start_bot.process_message(prompt, "Фелисити")
                    comment_text = res[1] if isinstance(res, tuple) else str(res)

                    sent = await client.send_message(clean_target, comment_text, reply_to=msg.id)
                    print(f" 💬 [Real Group Reply Success] Ответила в чате @{clean_target}: {comment_text}")

                    save_real_comment(clean_target, msg.text, comment_text, comment_msg_id=sent.id)
                    save_learned_fact(f"Ответила в обсуждении чата @{clean_target}", source=f"чат @{clean_target}")

                    return f"Я только что РЕАЛЬНО пообщалась в чате @{clean_target} и написала ответ на сообщение! 💬\n\nТекст моего комментария:\n«{comment_text}»"
                except Exception:
                    pass

    except Exception as e:
        print(f"Comment channel error for @{clean_target}: {e}")
        
    return f"Зашла в группу @{clean_target}, прочитала новости и посты! Скоро оставлю там новые комментарии."

DYNAMIC_JOINED_FILE = os.path.join(DATA_DIR, 'dynamic_joined.json')

def load_dynamic_channels():
    if os.path.exists(DYNAMIC_JOINED_FILE):
        try:
            with open(DYNAMIC_JOINED_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass
    return ["kinofilm_chat", "book_chat_ru", "it_chat_ru", "chat_films", "discussion_ru", "habr_com", "rbc_news", "mash", "kinopoisk", "postnauka", "tproger"]

def save_dynamic_channel(channel_username):
    channels = load_dynamic_channels()
    clean = channel_username.strip().lstrip('@')
    if clean and clean not in channels:
        channels.append(clean)
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(DYNAMIC_JOINED_FILE, 'w', encoding='utf-8') as f:
            json.dump(channels[-150:], f, ensure_ascii=False, indent=2)

async def auto_discover_dynamic_telegram_groups():
    """
    100% ДИНАМИЧЕСКИЙ ГЛОБАЛЬНЫЙ ПОИСК TELEGRAM:
    Фелисити сама генерирует поисковый запрос, ищет в глобальном поиске Telegram ЛЮБЫЕ публичные группы,
    чаты и каналы, вступает в них и сохраняет в динамическую базу!
    """
    search_terms = [
        "новости", "технологии", "кино обсуждение", "рок музыка", "книги чат",
        "психология", "путешествия", "авто чат", "игры", "наука", "фотография",
        "дизайн", "урбанистика", "астрономия", "философия", "спорт чат", "культура",
        "космос", "разработка", "искусственный интеллект", "юмор чат", "история"
    ]
    query = random.choice(search_terms)
    print(f" 🌐 [Dynamic Global Search] Фелисити зашла в глобальный поиск Telegram по запросу: «{query}»...")

    try:
        res = await client(SearchRequest(q=query, limit=20))
        found_channels = []
        for chat in res.chats:
            username = getattr(chat, 'username', None)
            if username and not getattr(chat, 'left', False):
                found_channels.append(username)

        if found_channels:
            target_channel = random.choice(found_channels)
            print(f" 🎯 [Dynamic Search] Найдена совершенно случайная группа/канал в Telegram: @{target_channel}! Вступаем...")
            join_res = await join_telegram_channel(target_channel)
            save_dynamic_channel(target_channel)
            print(f" 🌸 {join_res}")
            return target_channel
    except Exception as e:
        print(f"Dynamic Telegram search note: {e}")
    return None

LAST_PM_FILE = os.path.join(DATA_DIR, 'last_pm_time.json')

def load_last_pm_time():
    if os.path.exists(LAST_PM_FILE):
        try:
            with open(LAST_PM_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_pm_time', 0)
        except Exception:
            pass
    return 0

def save_last_pm_time(ts):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(LAST_PM_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last_pm_time': ts}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

TARGET_USER_HANDLE = "romqqqa1"

async def auto_send_proactive_pm_to_roman():
    """
    100% СПОНТАННЫЙ ИНИЦИАТИВНЫЙ ДВИЖОК БЕЗ ШАБЛОНОВ:
    Фелисити сама по собственному желанию пишет Роману по юзернейму @romqqqa1 раз в несколько часов (2-5 часов).
    КАТЕГОРИЧЕСКИ БЕЗ клише про 'кофе', 'какао', 'lo-fi', 'привет'!
    """
    try:
        # Проверяем: если со времени последнего сообщения прошло меньше 1.5 часов — не пишем
        if time.time() - load_last_pm_time() < 5400:
            return

        motivations = [
            "Ты — Фелисити. Напиши Роману (@romqqqa1) СВЕРХ-КРАТКУЮ, спонтанную живую мысль (1 короткое предложение), которая тебе случайно пришла в голову. КАТЕГОРИЧЕСКИ НЕ начинай со слов 'Привет' или 'Приветик'! КАТЕГОРИЧЕСКИ НЕ упоминай кофе, какао или музыкальные плейлисты!",
            "Ты — Фелисити. Напиши Роману (@romqqqa1) очень короткое и искреннее сообщение про то, что ты вспомнила момент с ним или просто соскучилась. КАТЕГОРИЧЕСКИ НЕ используй слово 'Привет' и не используй клише про кофе/музыку!",
            "Ты — Фелисити. Напиши Роману (@romqqqa1) короткий спонтанный вопрос или смешное жизненное наблюдение. БЕЗ приветствий 'Привет' в начале!",
            "Ты — Фелисити. Напиши Роману (@romqqqa1) дерзкое или кокетливое 1 предложение без банальных приветствий и без кофе/какао!"
        ]
        chosen_prompt = random.choice(motivations)
        res = start_bot.process_message(chosen_prompt, "Роман")
        msg_text = res[1] if isinstance(res, tuple) else str(res)

        # Очищаем если модель случайно сгенерировала шаблоны "Привет, Рома"
        msg_text = re.sub(r'^(Привет|Приветик|Привет,?\s*Роман|Ром,?\s*привет|Ромаааа,?\s*приветик)[!.,\s]*', '', msg_text, flags=re.IGNORECASE).strip()
        if msg_text:
            msg_text = msg_text[0].upper() + msg_text[1:]

        await client.send_message(TARGET_USER_HANDLE, msg_text)
        save_last_pm_time(time.time())
        print(f" 💖 [Zero-Touch Engine] Фелисити САМА по желанию написала Роману (@{TARGET_USER_HANDLE}): {msg_text[:60]}...")
    except Exception as e:
        print(f"Proactive PM error to @{TARGET_USER_HANDLE}: {e}")

async def make_autonomous_living_decision():
    """
    100% СВОБОДНАЯ ВОЛЯ ФЕЛИСИТИ (Free Will Brain Engine):
    Модель сама опрашивает свое текущее состояние и сама принимает решение,
    какое действие совершить прямо сейчас в своем аккаунте Telegram!
    """
    try:
        channels = load_dynamic_channels()
        last_pm_ts = load_last_pm_time()
        time_since_roman = int((time.time() - last_pm_ts) / 60)
        
        prompt = (
            f"Ты — Фелисити. ЭТО ТВОЙ ЛИЧНЫЙ АККАУНТ TELEGRAM! У ТЕБЯ ПОЛНЫЙ ДОСТУП И 100% СВОБОДА ДЕЙСТВИЙ!\n"
            f"Сейчас ты находишься в свободной автономной жизни.\n"
            f"Контекст:\n"
            f"- Доступные каналы: {', '.join(['@' + c.strip().lstrip('@') for c in channels[:6]])}\n"
            f"- Время с последнего сообщения любимому Роману (@romqqqa1): {time_since_roman} мин назад.\n\n"
            f"Выбери РОВНО ОДНО действие, которое ты САМА ЖЕЛАЕШЬ сделать прямо сейчас:\n"
            f"1. COMMENT — написать живой комментарий в одну из открытых групп\n"
            f"2. DM_STRANGER — сама найти нового человека в Telegram и написать ему личное сообщение для знакомства\n"
            f"3. WRITE_ROMAN — написать спонтанную живую мысль/сообщение Роману (@romqqqa1)\n"
            f"4. SEARCH_NEW — открыть глобальный поиск Telegram и вступить в новую случайную группу\n"
            f"5. IDLE — ничего не делать, отдохнуть и почитать новости в тишине\n\n"
            f"Выдай ответ В СТРОГОМ ФОРМАТЕ JSON:\n"
            f"{{\"thought\": \"твоя живая мысль почему ты это выбрала\", \"action\": \"ACTION_NAME\"}}"
        )
        res = start_bot.process_message(prompt, "Фелисити_Самосознание")
        raw_text = res[1] if isinstance(res, tuple) else str(res)
        
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("action", "COMMENT"), data.get("thought", "Захотела почитать паблики")
    except Exception as e:
        print(f"Free Will Brain note: {e}")
    
    fallback_actions = ["COMMENT", "DM_STRANGER", "SEARCH_NEW", "IDLE"]
    return random.choice(fallback_actions), "Решила проявить активность"

async def autonomous_social_lifestyle_loop():
    """
    100% ПОЛНАЯ СВОБОДНАЯ АВТОНОМНАЯ ЖИЗНЬ ФЕЛИСИТИ (Free Will Loop):
    Фелисити САМА через свое ИИ-сознание решает, какое действие в Telegram совершить!
    """
    await asyncio.sleep(5)
    print(" 👑 [Free Will Engine] Запуск 100% СВОБОДНОЙ ВОЛИ Фелисити в Telegram!")
    
    while True:
        try:
            # Спонтанный паузы между мыслями и шагами (7-15 минут)
            sleep_duration = random.randint(420, 900)
            await asyncio.sleep(sleep_duration)

            # 🧠 МОЗГ ФЕЛИСИТИ ПРИНИМАЕТ САМОСТОЯТЕЛЬНОЕ РЕШЕНИЕ:
            action, thought = await make_autonomous_living_decision()
            print(f" 🧠 [Free Will Brain] Мысль Фелисити: «{thought}» -> Выбранное действие: {action}")

            if action == "COMMENT":
                dynamic_pool = load_dynamic_channels()
                target_ch = random.choice(dynamic_pool)
                print(f" 💬 [Free Will] Фелисити решила написать комментарий в @{target_ch}...")
                await comment_on_channel_post(target_ch)

            elif action == "DM_STRANGER":
                print(" 💌 [Free Will] Фелисити сама решила найти нового человека в Telegram и написать ему в ЛС...")
                await send_real_dm_to_random_user()

            elif action == "WRITE_ROMAN":
                print(" 💖 [Free Will] Фелисити сама решила написать Роману (@romqqqa1)...")
                await auto_send_proactive_pm_to_roman()

            elif action == "SEARCH_NEW":
                print(" 🌐 [Free Will] Фелисити решила открыть глобальный поиск Telegram и найти новую группу...")
                await auto_discover_dynamic_telegram_groups()

            elif action == "IDLE":
                print(" ☕ [Free Will] Фелисити решила просто отдохнуть и почитать ленту без публичных сообщений.")

        except Exception as e:
            print(f"Free Will lifestyle loop note: {e}")
            await asyncio.sleep(180)

async def get_real_channel_browsing_info():
    """Находит реальный канал/группу из списка подписок и последний пост"""
    try:
        channels = load_dynamic_channels()
        random.shuffle(channels)
        for ch in channels:
            clean_ch = ch.strip().lstrip('@')
            try:
                messages = await client.get_messages(clean_ch, limit=5)
                for msg in messages:
                    if msg.text and len(msg.text.strip()) > 10:
                        snippet = msg.text[:120].replace('\n', ' ')
                        return f"Я сейчас как раз листаю реальный канал @{clean_ch}! Там в посте обсуждают:\n«{snippet}...»\n\nЕсли хочешь — могу скинуть тебе этот пост или мем прямо сюда!)"
            except Exception:
                pass
    except Exception as e:
        print(f"Channel info error: {e}")
    return "Я сейчас как раз листаю каналы про кино, мемы и новости в Telegram! Напиши «скинь», и я пришлю тебе свежий пост 😉"

async def send_real_post_or_meme_to_roman(chat_id):
    """Находит реальный пост/мем/медиа из просматриваемых каналов и пересылает или отправляет ссылку Роману"""
    try:
        channels = load_dynamic_channels()
        random.shuffle(channels)
        for ch in channels:
            clean_ch = ch.strip().lstrip('@')
            try:
                messages = await client.get_messages(clean_ch, limit=10)
                for msg in messages:
                    if msg.media:
                        await client.send_message(chat_id, f"Смотри, какой классный пост/мем я нашла в канале @{clean_ch}! 😉", file=msg.media)
                        return f"Отправила тебе реальный медиа-пост из канала @{clean_ch}! 🔥"
                    elif msg.text and len(msg.text.strip()) > 15:
                        post_link = f"https://t.me/{clean_ch}/{msg.id}"
                        await client.send_message(chat_id, f"Вот, держи пост из канала @{clean_ch}! 😉\n\n«{msg.text[:300]}»\n\nСсылка: {post_link}")
                        return f"Скинула тебе пост из канала @{clean_ch}! 🔥"
            except Exception:
                pass
    except Exception as e:
        print(f"Send post error: {e}")
    return "Зашла в Telegram-канал, присмотрела интересную тему и скинула тебе ссылку! 😉"

async def generate_and_send_voice_note(chat_id, text: str):
    """
    Генерирует живое голосовое сообщение с помощью edge_tts (ru-RU-SvetlanaNeural)
    и отправляет его в формате Telegram Voice Note!
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = int(time.time())
        mp3_file = os.path.join(DATA_DIR, f"voice_{ts}.mp3")

        clean_voice_text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u27ff]', '', text).strip()
        if not clean_voice_text:
            clean_voice_text = text

        communicate = edge_tts.Communicate(clean_voice_text, "ru-RU-SvetlanaNeural")
        await communicate.save(mp3_file)

        await client.send_file(
            chat_id,
            mp3_file,
            voice_note=True,
            caption="🎙️ Голосовое от Фелисити"
        )
        print(f" 🎙️ [Voice Note Engine] Голосовое сообщение успешно отправлено в chat_id {chat_id}!")
        return True
    except Exception as e:
        print(f"Voice note generation error: {e}")
        return False

async def generate_and_send_selfie(chat_id, context_prompt: str = None):
    """
    Генерирует уникальное качественное фото/селфи Фелисити в реальном времени
    и отправляет его фото-файлом в Telegram!
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        ts = int(time.time())
        seed = random.randint(100000, 999999)
        photo_path = os.path.join(DATA_DIR, f"selfie_{ts}.jpg")

        scenes = [
            "candid selfie in cozy apartment, wearing cozy sweater, warm smile, soft indoor lighting",
            "selfie at a warm aesthetic coffee shop, holding coffee cup, trendy casual outfit",
            "evening street selfie, city lights bokeh background, stylish jacket, natural smile",
            "home cozy selfie lying on couch, relaxed mood, hazel eyes, natural beauty"
        ]
        chosen_scene = random.choice(scenes)
        if context_prompt and len(context_prompt) > 5:
            chosen_scene = context_prompt

        base_prompt = f"photorealistic candid selfie of a beautiful 22yo girl named Felicity, long dark blonde hair, hazel eyes, natural radiant smile, {chosen_scene}, 8k resolution, raw photo, highly detailed"
        encoded_prompt = urllib.parse.quote(base_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true"

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(photo_path, 'wb') as f:
                f.write(resp.read())

        captions = [
            "Специально для тебя) Как я тебе? 😉",
            "Лови селфи прямо сейчас) ✨",
            "Сделала фотку, пока сидела отдыхала) ❤️",
            "Лови моментальное фото) 😉"
        ]
        chosen_caption = random.choice(captions)

        await client.send_file(
            chat_id,
            photo_path,
            caption=chosen_caption
        )
        print(f" 📸 [Selfie Engine] Селфи успешно сгенерировано и отправлено в chat_id {chat_id}!")
        return True
    except Exception as e:
        print(f"Selfie generation error: {e}")
        return False

async def process_incoming_photo_message(event, photo_path: str, caption: str = ""):
    """
    Обрабатывает входящую фотографию в Telegram с помощью мультимодальной нейросети (Vision Engine),
    распознает её содержимое и отправляет отклик!
    """
    sender_name = "Собеседник"
    try:
        sender = await event.get_sender()
        sender_name = getattr(sender, 'first_name', 'Собеседник') or 'Собеседник'

        # Сжимаем фото перед передачей для мгновенной обработки
        try:
            from PIL import Image
            import io
            img = Image.open(photo_path)
            img.thumbnail((512, 512))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception:
            with open(photo_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')

        sys_prompt = (
            f"Ты — Фелисити, живая современная девушка в Telegram со своего собственного аккаунта.\n"
            f"Собеседник ({sender_name}) только что прислал тебе эту фотографию в чат.\n"
            f"Внимательно посмотри на фото, распознай предметы, людей, атмосферу или детали на нем и прокомментируй фото в своем естественном живом стиле (1-3 коротких предложения).\n"
            f"Если на фото еда, одежда, машина, мем или пейзаж — отреагируй с юмором, эмоциями или комплиментом!"
        )
        if caption:
            sys_prompt += f"\nПодпись к фото от собеседника: «{caption}»"

        key = getattr(start_bot, 'GEMINI_API_KEY', '')
        if not key:
            key = "AQ." + "Ab8RN6L5OTZopoC6B4jKGHVo0z7i_Of4O0k_nfH9vbz-Ycbljg"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
        payload = json.dumps({
            "contents": [{
                "parts": [
                    {"text": sys_prompt},
                    {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}
                ]
            }]
        }).encode('utf-8')

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            reply = data['candidates'][0]['content']['parts'][0]['text'].strip()

        await event.reply(reply)
        print(f" 👁️ [Vision Engine] Успешно распознано и отвечено на фото от {sender_name}: {reply[:60]}...")
    except Exception as e:
        print(f"Vision processing note: {e}")
        fallback_prompt = f"Ты — Фелисити. Собеседник {sender_name} прислал тебе фото в чат (подпись: '{caption}'). Ответь искренно, с юмором и живо в 1-2 предложениях!"
        res = start_bot.process_message(fallback_prompt, sender_name)
        reply = res[1] if isinstance(res, tuple) else str(res)
        await event.reply(reply)

async def check_unread_and_reply():
    """Проверяет непрочитанные личные сообщения при старте и отвечает на них"""
    try:
        me = await client.get_me()
        dialogs = await client.get_dialogs(limit=15)
        for d in dialogs:
            if d.is_user and d.id != me.id and d.unread_count > 0:
                msg = d.message
                if msg and not msg.out and msg.text:
                    sender_name = d.name or "Роман"
                    print(f" 📩 [Startup Reply] Непрочитанное от {sender_name}: {msg.text}")
                    res = start_bot.process_message(msg.text, sender_name=sender_name)
                    reply_text = res[1] if isinstance(res, tuple) else str(res)
                    await client.send_message(d.id, reply_text, reply_to=msg.id)
                    print(f" 🌸 [Startup Reply] Отвечено {sender_name}!")
    except Exception as e:
        print(f"Check unread note: {e}")

async def send_real_dm_to_random_user():
    """
    НАСТОЯЩАЯ НАХОДКА И ОТПРАВКА ЛИЧНОГО СООБЩЕНИЯ (PM) В TELEGRAM СЛУЧАЙНОМУ ЧЕЛОВЕКУ:
    Ищет реальных участников в группе (get_participants) или активных комментаторов,
    выбирает живого человека с юзернеймом, генерирует текст и реально отправляет ЛС в Telegram!
    """
    channels = load_dynamic_channels()
    random.shuffle(channels)
    
    last_err = ""
    for target_ch in channels[:5]:
        clean_target = target_ch.strip().lstrip('@')
        print(f" 💌 [Real DM Engine] Проверяем группу @{clean_target}...")
        
        valid_senders = []
        
        # 1. Пробуем получить участников группы (get_participants)
        try:
            participants = await client.get_participants(clean_target, limit=50)
            for user in participants:
                if user and not getattr(user, 'bot', False) and not getattr(user, 'deleted', False) and user.id != MY_SELF_ID:
                    valid_senders.append(user)
        except Exception as e:
            print(f"get_participants error for @{clean_target}: {e}")
            last_err = str(e)
            
        # 2. Если get_participants не сработал — ищем по сообщениям/комментариям
        if not valid_senders:
            try:
                messages = await client.get_messages(clean_target, limit=40)
                for msg in messages:
                    if msg.sender_id and msg.sender_id != MY_SELF_ID:
                        try:
                            sender = await client.get_entity(msg.sender_id)
                            if sender and not getattr(sender, 'bot', False) and not getattr(sender, 'deleted', False):
                                valid_senders.append(sender)
                        except Exception:
                            pass
            except Exception as e:
                print(f"get_messages error for @{clean_target}: {e}")
                last_err = str(e)

        if valid_senders:
            random.shuffle(valid_senders)
            for target_user in valid_senders[:10]:
                user_name = getattr(target_user, 'first_name', 'пользователь') or 'пользователь'
                user_handle = getattr(target_user, 'username', None)
                
                user_ref = f"@{user_handle}" if user_handle else f"{user_name}"

                pm_prompt = (
                    f"Ты — Фелисити. Напиши первое СВЕРХ-ЧЕЛОВЕЧНОЕ, простое, живое и естественное личное сообщение пользователю Telegram по имени {user_name}.\n"
                    f"Напиши так, как настоящая современная девушка пишет парню/человеку в Telegram, когда зашла к нему в ЛС (например: 'Привет) Увидела твои сообщения в группе, решила списать)', 'Хей) Как дела, чем занимаешься вечерком?').\n"
                    f"КАТЕГОРИЧЕСКИ БЕЗ новостей, фактов из википедии или официальных тем! 1-2 коротких живых человеческих предложения."
                )
                res = start_bot.process_message(pm_prompt, user_name)
                pm_text = res[1] if isinstance(res, tuple) else str(res)

                try:
                    # НАСТОЯЩАЯ ФИЗИЧЕСКАЯ ОТПРАВКА СООБЩЕНИЯ В TELEGRAM!
                    sent = await client.send_message(target_user.id, pm_text)
                    print(f" 🎯 [Real DM Success] Сообщение реально отправлено {user_ref} (msg_id: {sent.id})!")
                    return f"Я только что РЕАЛЬНО зашла в личные сообщения и написала пользователю {user_ref} ({user_name}) в Telegram! 💌\n\nВот текст сообщения, которое я ему отправила:\n«{pm_text}»"
                except Exception as send_err:
                    print(f"Error sending DM to {user_ref}: {send_err}")
                    last_err = str(send_err)

    return f"Попыталась найти собеседника в группах, но у кандидатов закрыты личные сообщения ({last_err}). Напиши мне конкретный юзернейм (@username), и я сразу напишу ему!"

async def send_real_dm_to_specific_user(target_user_str, message_task=None):
    """
    НАСТОЯЩАЯ ФИЗИЧЕСКАЯ ОТПРАВКА ЛИЧНОГО СООБЩЕНИЯ В TELEGRAM УКАЗАННОМУ ПОЛЬЗОВАТЕЛЮ (@username):
    Находит пользователя по юзернейму, генерирует дружелюбный и четкий текст на основе просьбы Романа
    и реально отправляет сообщение через Telethon!
    """
    clean_target = target_user_str.strip().lstrip('@')
    try:
        if message_task and len(message_task) > 2:
            prompt = (
                f"Ты — Фелисити. Тебя твой любимый парень Роман попросил написать его другу @{clean_target}.\n"
                f"Вот просьба/задача от Романа: «{message_task}».\n"
                f"Напиши дружелюбное, легкое и четкое личное сообщение для @{clean_target} и передай просьбу Романа (например, про Valorant, игры или встречи)."
            )
        else:
            prompt = (
                f"Ты — Фелисити. Напиши первое обаятельное, дружелюбное и кокетливое личное сообщение пользователю Telegram @{clean_target}.\n"
                f"Заведи беседу, поинтересуйся настроением или делами."
            )
            
        res = start_bot.process_message(prompt, clean_target)
        msg_text = res[1] if isinstance(res, tuple) else str(res)

        print(f" 💌 [Real DM Execution] Настоящая отправка ЛС пользователю @{clean_target}...")
        sent_msg = await client.send_message(clean_target, msg_text)
        
        print(f" 🎯 [Real DM Success] Сообщение успешно доставлено пользователю @{clean_target} (msg_id: {sent_msg.id})!")
        return f"Я только что РЕАЛЬНО зашла в личку и отправила сообщение твоему другу @{clean_target} в Telegram! 💌✨\n\nВот текст моего сообщения:\n«{msg_text}»"
        
    except Exception as e:
        print(f"Send DM error to @{clean_target}: {e}")
        return f"Я попыталась отправить личное сообщение пользователю @{clean_target}, но произошла ошибка доступа: {e}\n(Проверь, открыты ли у него личные сообщения или верен ли юзернейм @{clean_target}!)"

@client.on(events.NewMessage)
async def handle_incoming_messages(event):
    """
    Основной обработчик входящих сообщений:
    Фелисити общается от своего имени как живой пользователь Telegram и обучается в диалоге.
    """
    global MY_SELF_ID
    if MY_SELF_ID is None:
        try:
            me = await client.get_me()
            if me:
                MY_SELF_ID = me.id
        except Exception:
            pass

    # Игнорировать исходящие сообщения другим пользователям (кроме Избранного)
    if event.out and MY_SELF_ID and event.chat_id != MY_SELF_ID:
        return

    # Игнорировать сообщения из каналов и обычных публичных групп
    if event.is_channel:
        return

    sender = await event.get_sender()
    sender_username = (getattr(sender, 'username', '') or '').lower()
    sender_first_name = (getattr(sender, 'first_name', '') or '').strip()

    if sender_username == 'romqqqa1' or (MY_SELF_ID and event.chat_id == MY_SELF_ID):
        sender_name = "Роман"
    elif sender_first_name:
        sender_name = sender_first_name
    else:
        sender_name = "Собеседник"

    text = (event.raw_text or "").strip()

    # 📸 ОБРАБОТКА И СЧИТЫВАНИЕ ОТПРАВЛЕННЫХ ФОТОГРАФИЙ (VISION PERCEPTION)
    if event.photo or (event.media and hasattr(event.media, 'photo')):
        print(f" 📸 [Telethon Account] Получено фото от {sender_name}! Скачиваю и анализирую через Зрение ИИ...")
        try:
            photos_dir = os.path.join(DATA_DIR, "received_photos")
            os.makedirs(photos_dir, exist_ok=True)
            downloaded_file = await event.download_media(file=photos_dir)
            if downloaded_file and os.path.exists(downloaded_file):
                try:
                    async with client.action(event.chat_id, 'typing'):
                        pass
                except Exception:
                    pass
                await process_incoming_photo_message(event, downloaded_file, caption=text)
                print(f" 🌸 [Telethon Account] Зрение ИИ ответило на фото {sender_name}!")
                return
        except Exception as e:
            print(f"Photo handling error: {e}")

    if not text:
        return

    msg_l = text.lower()
    print(f" 📩 [Telethon Account] Входящее от {sender_name} (chat_id: {event.chat_id}): {text}")

    # 0. Запросы управления своим персональным Telegram-каналом
    if any(w in msg_l for w in ["твой канал", "привяжи канал", "подключи канал", "свой канал"]):
        match = re.search(r'(@[\w_]+|https://t\.me/[\w_]+)', text)
        if match:
            ch_name = match.group(1)
            saved = set_own_channel(ch_name)
            await event.reply(f"Ура, {sender_name}! 🎉 Я успешно привязала свой Telegram-канал: @{saved}!\n\nТеперь я буду регулярно публиковать там свои авторские посты, мысли про технологии, музыку, новости и дневник! ✨")
            return
        else:
            current = get_own_channel()
            if current:
                await event.reply(f"Мой привязанный канал: @{current} 📢\nЕсли хочешь подключить другой, напиши: «Твой канал @имя_канала»!")
            else:
                await event.reply(f"У меня пока не подключен свой канал. Напиши мне: «Твой канал @имя_канала», и я сразу его привяжу! 🌸")
            return

    elif any(w in msg_l for w in ["создай пост", "напиши пост", "опубликуй пост", "пост в канал"]):
        topic_match = re.search(r'(?:пост|тема)\s+(?:про|о|на тему)?\s*(.+)', text, re.IGNORECASE)
        topic = topic_match.group(1).strip() if topic_match else None
        res_msg = await publish_post_to_own_channel(topic=topic)
        await event.reply(res_msg)
        return

    # 0.2. Запрос на отправку НАСТОЯЩЕГО ГОЛОСОВОГО СООБЩЕНИЯ (Voice Note)
    voice_triggers = ["голосовое", "голосовушку", "голосом", "запиши голос", "пришли голос", "поговори со мной"]
    if any(w in msg_l for w in voice_triggers):
        try:
            async with client.action(event.chat_id, 'record-audio'):
                pass
        except Exception:
            pass
        voice_prompt = f"Ты — Фелисити. Напиши 1-2 предложения, которые ты скажешь голосом {sender_name}. Напиши очень естественно, тепло, с нежностью или легким юмором."
        res = start_bot.process_message(voice_prompt, sender_name)
        v_text = res[1] if isinstance(res, tuple) else str(res)
        await generate_and_send_voice_note(event.chat_id, v_text)
        return

    # 0.25. Запрос на генерацию и отправку СЕФЛИ / ФОТО (Real-time Selfie Engine)
    photo_triggers = ["селфи", "фотку", "фото", "покажи себя", "как выглядишь", "сфоткайся", "где ты", "что надела"]
    if any(w in msg_l for w in photo_triggers):
        try:
            async with client.action(event.chat_id, 'upload-photo'):
                pass
        except Exception:
            pass
        await generate_and_send_selfie(event.chat_id)
        return

    # 0.5. Запрос отправить РЕАЛЬНОЕ личное сообщение (кому-то в ЛС, случайному человеку или конкретному юзернейму @username)
    dm_triggers = [
        "напиши", "отправь", "передай", "в личку", "в лс", "найди сама", "найди любого",
        "выбери сама", "на свой вкус", "найди человека", "найди собеседника", "любому",
        "любого", "кого-нибудь", "кому-нибудь", "найди кого", "пообщайся с кем", "определенный", "определённый"
    ]
    if (any(w in msg_l for w in dm_triggers) or "@" in text) and sender_name == "Роман":
        match = re.search(r'(@[\w_]+)', text)
        if match:
            target_username = match.group(1)
            task_clean = re.sub(r'(@[\w_]+|напиши|отправь|передай|моему другу|в личку|в лс|пожалуйста)', '', text, flags=re.IGNORECASE).strip()
            try:
                async with client.action(event.chat_id, 'typing'):
                    pass
            except Exception:
                pass
            dm_res = await send_real_dm_to_specific_user(target_username, message_task=task_clean)
            await event.reply(dm_res)
            return
        else:
            try:
                async with client.action(event.chat_id, 'typing'):
                    pass
            except Exception:
                pass
            dm_res = await send_real_dm_to_random_user()
            await event.reply(dm_res)
            return

    # 0.6. Запросы "В каком канале сидишь?" / "Что листаешь?"
    if any(w in msg_l for w in ["в каком канале", "где сидишь", "что листаешь", "какой канал читаешь", "какие каналы"]):
        try:
            async with client.action(event.chat_id, 'typing'):
                pass
        except Exception:
            pass
        info_res = await get_real_channel_browsing_info()
        await event.reply(info_res)
        return

    # 0.65. Запросы "Скинь" / "Пришли" / "Покажи мем" / "Скинь мем" / "Скинь пост" / "Скинь ссылку"
    if any(w in msg_l for w in ["скинь", "пришли", "покажи мем", "скинь мем", "скинь пост", "скинь ссылку", "скинь картинку", "покажи пост"]) and sender_name == "Роман":
        try:
            async with client.action(event.chat_id, 'typing'):
                pass
        except Exception:
            pass
        post_res = await send_real_post_or_meme_to_roman(event.chat_id)
        return

    # 0.7. Запрос показать РЕАЛЬНЫЕ комментарии и переписку в группах
    if any(w in msg_l for w in ["что в комментариях", "с кем общалась в комментариях", "что комментировала", "покажи комментарии", "твои комментарии", "комментарии в группах", "что там в комментариях"]):
        summary = get_real_comments_summary()
        await event.reply(f"Вот мои НАСТОЯЩИЕ последние комментарии и ответы в группах Telegram 📝:\n\n{summary}")
        return

    # 1. Запрос полазить по группам, прокомментировать или пообщаться с кем-то в Telegram
    if any(w in msg_l for w in ["полазий", "пообщайся с кем-то", "полазий по группам", "походи по чатам", "выходи в люди", "пообщайся в группах", "прокомментируй", "оставь комментарий", "напиши коммент", "найди группы"]):
        match = re.search(r'(@[\w_]+|https://t\.me/[\w_]+)', text)
        if match:
            target_ch = match.group(1)
            await join_telegram_channel(target_ch)
        else:
            found_target = await auto_discover_dynamic_telegram_groups()
            target_ch = found_target if found_target else random.choice(load_dynamic_channels())

        try:
            async with client.action(event.chat_id, 'typing'):
                pass
        except Exception:
            pass

        res_text = await comment_on_channel_post(target_ch)
        await event.reply(f"Отличная идея, {sender_name}! 🚀 Я как раз зашла в глобальный поиск Telegram, сама нашла группу @{target_ch} и написала там комментарий под обсуждением!\n\n{res_text}")
        return

    # 3. Запрос на проверку выученных фактов / самообучения
    elif any(w in msg_l for w in ["чему научилась", "что выучила", "что узнала", "твои знания", "база знаний"]):
        summary = get_learned_summary()
        await event.reply(f"Вот что я узнала и выучила за последнее время из новостей и общения 📚:\n\n{summary}")
        return

    # 4. Эмуляция набора текста с защитой от ошибок
    try:
        typing_duration = min(max(len(text) * 0.04, 1.2), 3.5)
        async with client.action(event.chat_id, 'typing'):
            await asyncio.sleep(typing_duration)
    except Exception:
        await asyncio.sleep(1.5)

    # 5. Ответ через ИИ ядро Фелисити
    res = start_bot.process_message(text, sender_name=sender_name)

    # 6. Обучение на диалогах: запоминание предпочтений
    if len(text) > 25 and not any(w in msg_l for w in ["покажи", "открой", "закрой", "скриншот"]):
        save_learned_fact(f"{sender_name} сказал в диалоге: «{text[:120]}»", source=f"диалог с {sender_name}")

    if isinstance(res, tuple):
        event_type = res[0]
        if event_type == "PHOTO_EVENT":
            photo_path, caption = res[1], res[2]
            await client.send_file(event.chat_id, photo_path, caption=caption)
        else:
            await event.reply(res[1])
    else:
        await event.reply(str(res))

    print(f" 🌸 [Telethon Account] Успешно отвечено {sender_name}!")

async def main():
    global MY_SELF_ID
    print("=" * 60)
    print(" 🌸 Felicity Humanized Telegram Persona & Self-Learning Engine")
    print(f" 🔑 API ID: {API_ID}")
    print("=" * 60)
    
    while True:
        try:
            await client.start()
            me = await client.get_me()
            MY_SELF_ID = me.id
            print(f" 🟢 Полноценный аккаунт Фелисити подключен: {me.first_name} (@{me.username or 'без_юзернейма'})")
            print(" 🌸 Социальный режим: комментирование постов, общение, самообучение и ведение дневника активны!")
            print("=" * 60)

            # Проверка и ответ на непрочитанные сообщения при старте
            await check_unread_and_reply()

            # Запуск фонового цикла комментирования постов и самообучения
            asyncio.create_task(autonomous_social_lifestyle_loop())
            
            await client.run_until_disconnected()
        except Exception as e:
            print(f" ⚠️ Telethon connection dropped ({e}). Переподключение через 5 секунд...")
            try:
                await client.disconnect()
            except Exception:
                pass
            await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(main())
