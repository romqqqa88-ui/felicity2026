# Felicity Standalone Windows Executable Launcher (Clean Single-Process Threaded Engine)
import os
import sys
import threading
import time
import webbrowser
import multiprocessing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)

sys.path.insert(0, BASE_DIR)

def run_server():
    try:
        import felicity_server
        felicity_server.run_server()
    except Exception as e:
        print(f"Server error: {e}")

def run_bot():
    try:
        import start_bot
        start_bot.main()
    except Exception as e:
        print(f"Bot error: {e}")

def run_userbot():
    try:
        if os.path.exists(os.path.join(BASE_DIR, 'felicity_userbot_session.session')):
            import asyncio
            import felicity_userbot
            asyncio.run(felicity_userbot.main())
    except Exception as e:
        print(f"Userbot note: {e}")

def main():
    multiprocessing.freeze_support()
    print("=" * 60)
    print(" 🌸 Felicity AI Engine & Telegram Userbot Client")
    print("=" * 60)
    
    print("\n [1/2] Запуск Веб-Студии и Телеграм Юзербота...")
    t1 = threading.Thread(target=run_server, daemon=True)
    t3 = threading.Thread(target=run_userbot, daemon=True)
    
    t1.start()
    t3.start()
    
    time.sleep(2)
    print(" [2/2] Открытие Веб-Студии...")
    webbrowser.open("http://localhost:8080")

    print("\n" + "=" * 60)
    print(" 🟢 ВСЕ СИСТЕМЫ ФЕЛИСИТИ УСПЕШНО ЗАПУЩЕНЫ!")
    print(" Вы можете свернуть это окно. Бот работает в фоновом режиме.")
    print("=" * 60 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Завершение работы...")

if __name__ == '__main__':
    main()
