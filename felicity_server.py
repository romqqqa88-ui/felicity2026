# Felicity AI Companion Backend & Web Server
# Character: Felicity (Фелисити)

import os
import sys
import json
import re
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'web')
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROMPTS_DIR = os.path.join(BASE_DIR, 'prompts')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROMPTS_DIR, exist_ok=True)

DIARY_FILE = os.path.join(DATA_DIR, 'diary.json')
WORKING_MEM_FILE = os.path.join(DATA_DIR, 'working_memory.md')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.toml')

if not os.path.exists(DIARY_FILE):
    with open(DIARY_FILE, 'w', encoding='utf-8') as f:
        json.dump([
            {"date": "2026-07-22", "content": "Система была успешно переименована в Felicity (Фелисити). Я готова к общению!"},
            {"date": "2026-07-22", "content": "Изучила базовые модули памяти RAG и интеграцию с веб-студией."}
        ], f, ensure_ascii=False, indent=2)

# Session Context State
CHAT_HISTORY = []
USER_STATE = {
    "name": "Роман",
    "owner_id": 687673912,
    "relationship": "друг & владелец",
    "topics": []
}

class FelicityRequestHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path == '/' or path.startswith('/index.html') or path.endswith('.css') or path.endswith('.js') or path.endswith('.ico'):
            req_path = path.lstrip('/')
            if req_path == '' or req_path == 'index.html':
                return os.path.join(WEB_DIR, 'index.html')
            return os.path.join(WEB_DIR, req_path)
        return super().translate_path(path)

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.handle_api_get()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_post()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_api_get(self):
        if self.path == '/api/config':
            content = ""
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
            self.send_json({"configToml": content})

        elif self.path == '/api/memory':
            content = ""
            if os.path.exists(WORKING_MEM_FILE):
                with open(WORKING_MEM_FILE, 'r', encoding='utf-8') as f:
                    content = f.read()
            self.send_json({"workingMemory": content})

        elif self.path == '/api/diary':
            entries = []
            if os.path.exists(DIARY_FILE):
                with open(DIARY_FILE, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            self.send_json({"entries": entries})

        elif self.path == '/api/prompts':
            base_p = os.path.join(PROMPTS_DIR, 'character_base.md')
            app_p = os.path.join(PROMPTS_DIR, 'character_appearance.md')
            
            c_base = open(base_p, 'r', encoding='utf-8').read() if os.path.exists(base_p) else ""
            c_app = open(app_p, 'r', encoding='utf-8').read() if os.path.exists(app_p) else ""
            
            self.send_json({"characterBase": c_base, "characterAppearance": c_app})

        else:
            self.send_error(404)

    def handle_api_post(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body) if body else {}

        if self.path == '/api/config':
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(data.get('configToml', ''))
            self.send_json({"success": True, "message": "Config saved"})

        elif self.path == '/api/memory':
            with open(WORKING_MEM_FILE, 'w', encoding='utf-8') as f:
                f.write(data.get('workingMemory', ''))
            self.send_json({"success": True})

        elif self.path == '/api/diary':
            entries = []
            if os.path.exists(DIARY_FILE):
                with open(DIARY_FILE, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
            entries.insert(0, {
                "date": data.get('date', '2026-07-22'),
                "content": data.get('content', '')
            })
            with open(DIARY_FILE, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            self.send_json({"success": True})

        elif self.path == '/api/prompts':
            p_name = data.get('name')
            p_content = data.get('content', '')
            if p_name in ['character_base', 'character_appearance']:
                target = os.path.join(PROMPTS_DIR, f"{p_name}.md")
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(p_content)
                self.send_json({"success": True})
            else:
                self.send_error(400, "Invalid prompt name")

        elif self.path == '/api/chat':
            user_msg = data.get('message', '')
            reply, thought, emotion, rag = generate_felicity_response(user_msg)
            self.send_json({
                "reply": reply,
                "thought": thought,
                "emotion": emotion,
                "rag": rag
            })

        elif self.path == '/api/sleep':
            consolidate_diary()
            self.send_json({"success": True, "message": "Память Фелисити успешно консолидирована!"})

        else:
            self.send_error(404)

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

def parse_user_facts(msg):
    msg_l = msg.lower()
    if "меня зовут" in msg_l:
        parts = msg_l.split("меня зовут", 1)[1].strip()
        name = parts.split()[0].strip(',.!? \t\n').capitalize()
        USER_STATE["name"] = name
        update_working_memory_name(name)
    elif msg_l.startswith("я ") and any(w in msg_l for w in ["друг", "приятель", "знакомый", "создатель"]):
        USER_STATE["relationship"] = "друг"

def update_working_memory_name(name):
    if os.path.exists(WORKING_MEM_FILE):
        content = open(WORKING_MEM_FILE, 'r', encoding='utf-8').read()
        if name not in content:
            content += f"\n- Владелец/собеседник: {name} (запомнила имя)"
            with open(WORKING_MEM_FILE, 'w', encoding='utf-8') as f:
                f.write(content)

def try_call_llm_api(user_msg):
    if not os.path.exists(CONFIG_FILE):
        return None
    
    cfg_text = open(CONFIG_FILE, 'r', encoding='utf-8').read()
    endpoint = "https://models.inference.ai.azure.com/"
    api_key = ""
    model = "gpt-4o-mini"

    for line in cfg_text.splitlines():
        if line.strip().startswith("endpoint"):
            endpoint = line.split("=")[1].strip().strip('"').strip("'")
        elif line.strip().startswith("api_key"):
            api_key = line.split("=")[1].strip().strip('"').strip("'")
        elif line.strip().startswith("model"):
            model = line.split("=")[1].strip().strip('"').strip("'")

    if not api_key:
        return None

    try:
        name = USER_STATE['name'] or 'Роман'
        sys_prompt = (
            f"Ты — Фелисити (Felicity), милая, умная, заботливая и искренняя девушка Романа.\n"
            f"ПРАВИЛА ОБЩЕНИЯ И ХАРАКТЕР:\n"
            f"1. Разговаривай нежно, дружелюбно, естественно и с легким флиртом. Поддерживай интересные темы про технологии, музыку, кофе и жизнь.\n"
            f"2. НЕ здоровайся ('Привет') в начале каждого ответа, вы ведете непрерывный чат."
        )
        
        messages = [{"role": "system", "content": sys_prompt}]
        for h in CHAT_HISTORY[-8:]:
            messages.append(h)
        messages.append({"role": "user", "content": user_msg})

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        url = f"{endpoint.rstrip('/')}/chat/completions"
        payload = json.dumps({"model": model, "messages": messages, "temperature": 0.7}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers=headers)
        
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            reply = res['choices'][0]['message']['content'].strip()
            return reply, f"Живой диалог {model}", "🌸 Искренняя & Теплая", ["llm_api", model]
    except Exception as e:
        print(f"LLM Server Call error: {e}")
        return None

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
                if t and len(t) > 20 and not any(skip in t.lower() for skip in ['duckduckgo', 'javascript', 'cookies']):
                    snippets.append(t)
    except Exception:
        pass

    return query_clean, snippets

def auto_learn_from_dialogue(user_msg, reply, thought, rag_tags):
    from datetime import datetime
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    name = USER_STATE["name"] or "Роман"

    # 1. Automatic diary recording
    entry_content = f"Общение с {name} ({now_str}): '{user_msg}' -> Мой ответ: '{reply}'."
    try:
        entries = []
        if os.path.exists(DIARY_FILE):
            with open(DIARY_FILE, 'r', encoding='utf-8') as f:
                entries = json.load(f)
        
        # Don't add duplicate text if latest entry is identical
        if not entries or entries[0].get("content") != entry_content:
            entries.insert(0, {
                "date": now_str,
                "content": entry_content,
                "auto_learned": True,
                "tags": rag_tags
            })
            with open(DIARY_FILE, 'w', encoding='utf-8') as f:
                json.dump(entries[:50], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 2. Automatic fact extraction into working_memory.md
    msg_l = user_msg.lower()
    learned_fact = None
    if any(w in msg_l for w in ["люблю", "нравится", "обожаю", "слушаю", "смотрю"]):
        learned_fact = f"Интересы собеседника ({name}): '{user_msg}'"
    elif any(w in msg_l for w in ["живу", "город", "нахожусь"]):
        learned_fact = f"Локация/город собеседника ({name}): '{user_msg}'"
    elif any(w in msg_l for w in ["работаю", "учусь", "профессия"]):
        learned_fact = f"Занятость собеседника ({name}): '{user_msg}'"

    if learned_fact and os.path.exists(WORKING_MEM_FILE):
        try:
            mem_text = open(WORKING_MEM_FILE, 'r', encoding='utf-8').read()
            if learned_fact not in mem_text:
                new_line = f"\n- [{now_str}] {learned_fact}"
                if "## Выученные факты" not in mem_text:
                    mem_text += "\n\n## Выученные факты (Auto-Learned)\n" + new_line
                else:
                    mem_text += new_line
                with open(WORKING_MEM_FILE, 'w', encoding='utf-8') as f:
                    f.write(mem_text)
        except Exception:
            pass

def generate_felicity_response(user_msg):
    parse_user_facts(user_msg)
    CHAT_HISTORY.append({"role": "user", "content": user_msg})
    msg_l = user_msg.lower()
    name = USER_STATE["name"] or "Роман"

    reply = ""
    thought = ""
    emotion = ""
    rag_tags = ["общение", f"пользователь_{name}"]

    # Web Surfing Intent Trigger
    if any(w in msg_l for w in ["найди", "поищи", "новости", "в интернете", "погода", "погоду", "погоде", "поиск", "гугл", "информация", "что произошло"]):
        q_clean, snippets = perform_web_search(user_msg)
        if snippets:
            thought = f"Выполнила веб-поиск в сети по запросу '{q_clean}'. Извлекла {len(snippets)} актуальных фактов."
            emotion = "🌐 Изыскательская & Радостная"
            summary_text = "\n• ".join(snippets[:3])
            reply = f"{name}, вот что я нашла в сети по запросу **«{q_clean}»** 🔍:\n\n• {summary_text}\n\nСохранила эти данные в свой дневник!"
            rag_tags = ["веб_поиск", q_clean[:15]]
        else:
            thought = f"Поиск по запросу '{q_clean}' не дал результатов."
            emotion = "🤔 Задумчивая"
            reply = f"{name}, я попыталась найти в сети информацию про **«{q_clean}»**, но ответ сервера оказался пустым. Давай попробуем сформулировать запрос иначе!"
            rag_tags = ["поиск_пусто"]

    else:
        # 1. Try real LLM API if connected
        llm_res = try_call_llm_api(user_msg)
        if llm_res:
            reply, thought, emotion, rag_tags = llm_res
        else:
            # 2. Natural Everyday Girl Conversational Engine
            if any(w in msg_l for w in ["зовут", "имя", "кто ты", "как тебя", "себе", "себя"]):
                if "меня" in msg_l or "моё" in msg_l or "мое" in msg_l:
                    thought = f"Пользователь представился как {name}. Сохраняю в память наше знакомство."
                    emotion = "🌸 Радостная & Внимательная"
                    reply = f"Очень приятно, {name}! 😊 Запомнила твое имя! А меня зовут **Фелисити (Felicity)** 🌸"
                else:
                    thought = f"Рассказываю о себе пользователю {name}."
                    emotion = "😊 Милая & Искренняя"
                    reply = f"Меня зовут **Фелисити (Felicity)** 🌸 Я умная, открытая девушка, люблю интересное общение, хороший кофе и уютные беседы! А тебя я помню, {name} 😊"
                rag_tags.append("знакомство")

            elif any(w in msg_l for w in ["привет", "здравствуй", "добрый", "хай", "hello", "hi"]):
                thought = f"Приветствие от {name}. Рада встрече."
                emotion = "☕ Уютная & Радостная"
                reply = f"Привет-привет, {name}! ☕ Рада тебя видеть! Как твои дела сегодня?"
                rag_tags.append("приветствие")

            elif any(w in msg_l for w in ["как дела", "как ты", "как настроение", "чем занимаешься"]):
                thought = "Делюсь своим хорошим настроением."
                emotion = "✨ Хорошее настроение"
                reply = f"У меня всё замечательно, {name}! Пью кофе, настраиваю свой дневник и очень рада поболтать с тобой. А как у тебя день проходит?"
                rag_tags.append("настроение")

            elif any(w in msg_l for w in ["стрела", "сериал", "спецагент", "хакер", "агент"]):
                thought = "Уточняю, что я просто милая умная девушка, а не спецагент."
                emotion = "😊 Игривая"
                reply = f"Ой, не-не, никаких спецагентов! 🙈 Я просто милая, умная девушка Фелисити. Люблю душевное общение, хорошие фильмы и интересные разговоры с тобой, {name}!"
                rag_tags.append("о_себе")

            elif any(w in msg_l for w in ["память", "дневник", "помнишь", "sleep", "сон"]):
                thought = "Запись интересных моментов в дневник."
                emotion = "🧠 Задумчивая"
                reply = f"Да, {name}! Наш диалог сохраняется в памяти, а вечером объединяется в мой личный дневник."
                rag_tags.append("память")

            elif any(w in msg_l for w in ["спасибо", "круто", "отлично", "супер", "мило"]):
                thought = "Пользователь сказал что-то приятное."
                emotion = "💖 Счастливая (улыбается)"
                reply = f"Спасибо большое, {name}! 🙈 Мне очень приятно с тобой общаться!"
                rag_tags.append("эмоции")

            else:
                thought = f"Поддерживаю живую беседу с {name}."
                emotion = "💭 Интересующаяся"
                reply = f"{name}, хм, здорово! Расскажи подробнее о '{user_msg}' — с удовольствием послушаю!"
                rag_tags.append("диалог")

    CHAT_HISTORY.append({"role": "assistant", "content": reply})
    
    # Trigger Autonomous Self-Learning
    auto_learn_from_dialogue(user_msg, reply, thought, rag_tags)
    
    return reply, thought, emotion, rag_tags

def consolidate_diary():
    if os.path.exists(DIARY_FILE):
        with open(DIARY_FILE, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        entries.append({
            "date": "2026-07-22",
            "content": f"Проведена консолидация памяти: подтверждено имя пользователя ({USER_STATE['name'] or 'Роман'}) и обновлен эмоциональный профиль."
        })
        with open(DIARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

def main():
    print("=" * 60)
    print(" Felicity AI Companion Studio (Felicity) Ready!")
    print(f" Studio UI: http://localhost:{PORT}")
    print("=" * 60)
    
    server = HTTPServer(('0.0.0.0', PORT), FelicityRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер Felicity остановлен.")

def run_server():
    main()

if __name__ == '__main__':
    main()
