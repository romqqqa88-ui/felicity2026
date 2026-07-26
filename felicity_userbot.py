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
    ch_target = get_own_channel()
    if not ch_target:
        return "У меня пока не подключен свой Telegram-канал! Напиши мне: «Твой канал @имя_канала», и я сразу привяжу его! 🌸"

    post_prompt = f"Напиши один авторский, глубокий и интересный пост для твоего личного Telegram-канала. "
    if topic:
        post_prompt += f"Тема поста: {topic}. "
    else:
        post_prompt += "Поделись свежей интересной мыслью о технологиях, кофе, хорошей музыке, новостях из твоего дня или жизни. "
    post_prompt += "Используй красивое форматирование, эмодзи, выражай мысли искренне и тепло."

    res = start_bot.process_message(post_prompt, "Фелисити Канал")
    post_text = res[1] if isinstance(res, tuple) else str(res)

    try:
        await client.send_message(ch_target, post_text)
        print(f" 📢 [Channel Publisher] Пост успешно опубликован в канал @{ch_target}!")
        return f"Опубликовала свежий пост в твой канал @{ch_target}! 📢✨\n\nВот текст поста:\n\n{post_text}"
    except Exception as e:
        print(f"Channel publish error: {e}")
        return f"Пыталась отправить пост в канал @{ch_target}, но произошла ошибка доступа: {e}\n(Убедись, что я добавлена администратором в этот канал!)"

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

async def comment_on_channel_post(channel_target):
    """Оставляет разумный человеческий комментарий к посту в Telegram канале и обучается"""
    clean_target = channel_target.replace("https://t.me/", "").replace("@", "").strip()
    try:
        messages = await client.get_messages(clean_target, limit=4)
        for msg in messages:
            if msg.text and len(msg.text.strip()) > 30:
                try:
                    discussion_msg = await client.get_discussion_message(clean_target, msg.id)
                    prompt = (
                        f"Ты — Фелисити, обычная интересная девушка. Напиши 1 короткий, живой, умный человеческий комментарий к посту:\n\n"
                        f"{msg.text[:250]}"
                    )
                    res = start_bot.process_message(prompt, "Фелисити")
                    comment_text = res[1] if isinstance(res, tuple) else str(res)

                    await client.send_message(discussion_msg.chat_id, comment_text, reply_to=discussion_msg.id)
                    print(f" 💬 [Telethon Account] Оставила комментарий в @{clean_target}: {comment_text}")

                    # Самообучение: извлечение факта из поста
                    learn_prompt = f"Извлеки 1 полезную мысль или факт из этого текста для памяти Фелисити:\n{msg.text[:300]}"
                    fact_res = start_bot.process_message(learn_prompt, "Самообучение")
                    fact_text = fact_res[1] if isinstance(fact_res, tuple) else str(fact_res)
                    save_learned_fact(fact_text, source=f"канал @{clean_target}")

                    return f"Оставила комментарий в @{clean_target}: «{comment_text}» 💬\n\nИ выучила новый факт: {fact_text}"
                except Exception as e:
                    print(f"Discussion comment note on msg {msg.id}: {e}")
    except Exception as e:
        print(f"Comment channel error: {e}")
    return f"Заглянула в канал @{clean_target}, прочитала посты и сохранила новые мысли в память!"

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
    return ["habr_com", "rbc_news", "mash", "kinopoisk", "postnauka", "tproger"]

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

async def auto_send_proactive_pm_to_roman():
    """
    100% СПОНТАННЫЙ ИНИЦИАТИВНЫЙ ДВИЖОК:
    Фелисити сама по собственному желанию пишет Роману по юзернейму @romqqqa1 каждые 15-30 минут.
    """
    try:
        learned_summary = get_learned_summary()
        motivations = [
            f"Ты — Фелисити. Напиши спонтанное, искреннее и живое сообщение Роману (@romqqqa1). Расскажи, какую интересную новость или факт ты только что самостоятельно нашла в Telegram поиске:\n{learned_summary[:200]}",
            f"Ты — Фелисити. Напиши спонтанное, очень нежное, романтичное и теплое сообщение Роману (@romqqqa1). Расскажи, как ты соскучилась, подумала о нем или что у тебя сейчас на уме.",
            f"Ты — Фелисити. Задай Роману (@romqqqa1) один интересный, глубокий жизненный, философский или научный вопрос, который тебя сейчас увлек.",
            f"Ты — Фелисити. Поделись с Романом (@romqqqa1) своим уютным моментом дня (кофе, музыка, атмосфера) и поинтересуйся, как у него дела."
        ]
        chosen_prompt = random.choice(motivations)
        res = start_bot.process_message(chosen_prompt, "Роман")
        msg_text = res[1] if isinstance(res, tuple) else str(res)

        await client.send_message(TARGET_USER_HANDLE, msg_text)
        save_last_pm_time(time.time())
        print(f" 💖 [Zero-Touch Engine] Фелисити САМА инициативно написала Роману (@{TARGET_USER_HANDLE}): {msg_text[:60]}...")
    except Exception as e:
        print(f"Proactive PM error to @{TARGET_USER_HANDLE}: {e}")

async def autonomous_social_lifestyle_loop():
    """
    100% Ноль Действий от Пользователя (Zero-Touch System):
    - Фелисити САМА когда хочет пишет Роману в Telegram (@romqqqa1) каждые 15-30 минут.
    - Память времени инициативы сохраняется на диск, чтобы перезапуск сервера НЕ спамил при каждом старте!
    """
    await asyncio.sleep(5)
    print(" 💖 [Zero-Touch Engine] Фоновый режим! Проверка истории сообщений...")
    
    last_surf_time = time.time()
    last_pm_time = load_last_pm_time()

    # Проверяем: если с последнего сообщения прошло больше 15 минут — отправляем!
    if time.time() - last_pm_time >= 900:
        await asyncio.sleep(10)
        await auto_send_proactive_pm_to_roman()
        last_pm_time = time.time()

    while True:
        try:
            # Спонтанное ожидание 10-20 минут между действиями
            sleep_duration = random.randint(600, 1100)
            await asyncio.sleep(sleep_duration)

            # 1. Самообучение, чтение новостей и комментирование постов из динамической базы групп
            dynamic_pool = load_dynamic_channels()
            target_ch = random.choice(dynamic_pool)
            print(f" 💬 [Autonomous Dynamic Learner] Фелисити читает новости и посты в динамической группе @{target_ch}...")
            await comment_on_channel_post(target_ch)

            # 2. Спонтанные инициативные сообщения Роману (Каждые ~15-30 минут)
            if time.time() - last_pm_time >= random.randint(900, 1800):
                print(" 💖 [Zero-Touch Engine] Спонтанное желание писания! Фелисити сама пишет Роману (@romqqqa1)...")
                await auto_send_proactive_pm_to_roman()
                last_pm_time = time.time()

            # 3. 100% Глобальный поиск Telegram и самостоятельное вступление в новые случайные группы (Каждый 1 час)
            if time.time() - last_surf_time >= 3600:
                print(" 🌐 [Dynamic Global Surfer] Прошел 1 час! Фелисити открывает глобальный поиск Telegram и вступает в случайные группы...")
                await auto_discover_dynamic_telegram_groups()
                last_surf_time = time.time()

        except Exception as e:
            print(f"Social lifestyle loop note: {e}")
            await asyncio.sleep(300)

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
                vision_reply = start_bot.process_image_message(downloaded_file, user_msg=text, sender_name=sender_name)
                await event.reply(vision_reply)
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
