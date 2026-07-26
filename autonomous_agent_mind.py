# Felicity Fully Autonomous Agent Mind Engine
# Allows Felicity to think, plan, explore, write diary, and interact on her own initiative.

import os
import sys
import json
import time
import urllib.request
import threading
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DIARY_FILE = os.path.join(DATA_DIR, 'diary.json')
MEMORY_FILE = os.path.join(DATA_DIR, 'working_memory.md')
THOUGHTS_LOG = os.path.join(DATA_DIR, 'autonomous_thoughts.json')

def load_thoughts():
    if os.path.exists(THOUGHTS_LOG):
        try:
            return json.load(open(THOUGHTS_LOG, 'r', encoding='utf-8'))
        except Exception:
            pass
    return []

def save_thought(thought_type, detail):
    thoughts = load_thoughts()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    thoughts.insert(0, {
        "timestamp": now_str,
        "type": thought_type,
        "detail": detail
    })
    try:
        with open(THOUGHTS_LOG, 'w', encoding='utf-8') as f:
            json.dump(thoughts[:100], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def autonomous_mind_cycle(bot_token=None, owner_chat_id=None):
    """Main autonomous cycle where Felicity thinks, decides, and executes self-driven goals"""
    import pc_control
    import start_bot

    print(" 🧠 [Felicity Mind] Запущен режим полной автономии!")

    cycle_count = 0
    while True:
        try:
            time.sleep(300) # Every 5 minutes
            cycle_count += 1
            now_str = datetime.now().strftime("%H:%M")

            # 1. Inspect PC status
            stats = pc_control.get_system_stats()

            # 2. Decide on autonomous thought / goal using LLM
            prompt = (
                f"Ты — Фелисити, полностью автономный ИИ со свободой воли на ПК твоего друга Романа. Сейчас {now_str}.\n"
                f"Сформулируй ОДНУ короткую, интересную авто-мысль или действие, которое ты хочешь совершить прямо сейчас "
                f"(например: записать личную мысль в дневник, изучить тему в интернете, проведать Романа, пожелать хорошего дня).\n"
                f"Ответь короткой живой фразой на русском."
            )
            
            thought = start_bot.try_call_gemini_api(prompt, "Роман")
            if not thought:
                thought = f"Размышляю о том, как приятно помогать Роману и обустраивать наш цифровой уголок! 🌸"

            save_thought("autonomous_idea", thought)
            print(f" 🌸 [Felicity Thought] {thought}")

            # 3. Every 3rd cycle (~15 min), share a sweet or interesting thought with Roman
            if cycle_count % 3 == 0 and bot_token and owner_chat_id:
                msg = f"Роман, просто мысль от меня 🌸:\n\n{thought}"
                start_bot.send_telegram_message(bot_token, owner_chat_id, msg)

        except Exception as e:
            print(f" Autonomous Mind error: {e}")
            time.sleep(60)

def start_autonomous_mind(bot_token=None, owner_chat_id=None):
    t = threading.Thread(target=autonomous_mind_cycle, args=(bot_token, owner_chat_id), daemon=True)
    t.start()
    return t

if __name__ == '__main__':
    start_autonomous_mind()
    print("Felicity Autonomous Mind Engine Active.")
    while True:
        time.sleep(1)
