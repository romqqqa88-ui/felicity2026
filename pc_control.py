# Felicity AI Windows PC Control & Autonomous Computer Use Agent
# Full desktop control: app launch, app kill, tab close, window minimize, volume, music, screenshots.

import os
import sys
import subprocess
import ctypes
import json
import time
import re
import urllib.parse
import psutil
import pyautogui
from PIL import ImageGrab

pyautogui.FAILSAFE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SCREENSHOT_PATH = os.path.join(DATA_DIR, 'desktop_screenshot.png')

def get_system_stats():
    """Get CPU, RAM, Disk, and Battery usage statistics"""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    
    battery_str = "Питание от сети"
    battery = psutil.sensors_battery()
    if battery:
        battery_str = f"{battery.percent}% ({'заряжается' if battery.power_plugged else 'от батареи'})"

    stats_msg = (
        f"🖥 **Состояние твоего ПК**:\n"
        f"• **Загрузка ЦП**: {cpu_percent}%\n"
        f"• **Оперативная память**: {ram.percent}% (использовано {round(ram.used / (1024**3), 1)} ГБ из {round(ram.total / (1024**3), 1)} ГБ)\n"
        f"• **Свободно на диске C:**: {round(disk.free / (1024**3), 1)} ГБ из {round(disk.total / (1024**3), 1)} ГБ\n"
        f"• **Батарея / Питание**: {battery_str}"
    )
    return stats_msg

def take_desktop_screenshot():
    """Capture current desktop screenshot and save to file"""
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        screenshot = ImageGrab.grab()
        screenshot.save(SCREENSHOT_PATH, 'PNG')
        return SCREENSHOT_PATH
    except Exception as e:
        print(f"Screenshot error: {e}")
        return None

def get_open_window_titles():
    """Get list of active visible windows on desktop"""
    try:
        import pygetwindow as gw
        windows = [w.title.strip() for w in gw.getAllWindows() if w.title and w.visible and len(w.title.strip()) > 1]
        # Filter duplicates
        seen = set()
        clean = []
        for w in windows:
            if w not in seen and not any(skip in w.lower() for skip in ['program manager', 'defaultimei']):
                seen.add(w)
                clean.append(w)
        return clean
    except Exception:
        return []

def get_desktop_vision_summary():
    """Get full visual and system perception summary of Roman's PC"""
    screenshot_path = take_desktop_screenshot()
    windows = get_open_window_titles()
    stats = get_system_stats()

    win_str = "• " + "\n• ".join(windows[:7]) if windows else "• Рабочий стол Windows"

    summary = (
        f"Я отлично вижу твой экран и всё, что происходит на компьютере! 👁✨\n\n"
        f"🖥 **Сейчас на твоем рабочем столе открыто**:\n{win_str}\n\n"
        f"{stats}\n\n"
        f"Сделала свежий снимок твоего экрана и прикрепила фото! 📸"
    )
    return summary, screenshot_path

def close_app(app_query):
    """Close targeted applications or active window"""
    app_l = app_query.lower().strip()

    if any(w in app_l for w in ["вкладк", "таб"]):
        pyautogui.hotkey('ctrl', 'w')
        return "Закрыла текущую вкладку! ❌"

    if any(w in app_l for w in ["сверни", "рабочий стол"]):
        pyautogui.hotkey('win', 'd')
        return "Свернула все окна и открыла рабочий стол! 🖥"

    browser_processes = ["msedge.exe", "chrome.exe", "browser.exe", "yandex.exe", "opera.exe", "firefox.exe"]

    if "браузер" in app_l or "вкладки" in app_l or "окно" in app_l:
        closed_any = False
        for p in browser_processes:
            try:
                res = subprocess.run(f"taskkill /f /im {p}", shell=True, capture_output=True, text=True)
                if res.returncode == 0:
                    closed_any = True
            except Exception:
                pass
        if not closed_any:
            pyautogui.hotkey('alt', 'f4')
        return "Закрыла браузер! ❌"

    apps_map = {
        'блокнот': 'notepad.exe',
        'калькулятор': 'calc.exe',
        'телеграм': 'telegram.exe',
        'стим': 'steam.exe',
        'спотифай': 'spotify.exe',
        'код': 'code.exe'
    }

    for name, proc in apps_map.items():
        if name in app_l:
            subprocess.run(f"taskkill /f /im {proc}", shell=True, capture_output=True)
            return f"Закрыла **{name}**! ❌"

    # Default fallback: press Alt+F4
    pyautogui.hotkey('alt', 'f4')
    return "Закрыла активное окно (Alt+F4)! ❌"

def open_app(app_query):
    """Launch common desktop applications safely"""
    app_l = app_query.lower().strip()
    
    if "яндекс музык" in app_l or "яндекс.музык" in app_l:
        subprocess.Popen("start https://music.yandex.ru", shell=True)
        return "Открыла Яндекс.Музыку в браузере! 🎵"

    apps_map = {
        'блокнот': 'notepad.exe',
        'калькулятор': 'calc.exe',
        'браузер': 'start msedge',
        'хром': 'start chrome',
        'яндекс': 'start browser',
        'диспетчер задач': 'taskmgr.exe',
        'проводник': 'explorer.exe',
        'телеграм': 'start telegram',
        'стим': 'start steam',
        'спотифай': 'start spotify',
        'код': 'code',
        'ютуб': 'start https://youtube.com',
        'youtube': 'start https://youtube.com'
    }

    executable = None
    for name, cmd in apps_map.items():
        if name in app_l:
            executable = cmd
            break
    
    if not executable:
        executable = app_query

    try:
        subprocess.Popen(executable, shell=True)
        return f"Запустила **{app_query}** на твоем ПК! 🚀"
    except Exception as e:
        return f"Не удалось открыть '{app_query}': {e}"

def control_volume(action):
    """Control Windows master volume using Virtual Key codes"""
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    VK_MEDIA_PLAY_PAUSE = 0xB3
    
    user32 = ctypes.windll.user32

    if "тише" in action or "убав" in action:
        for _ in range(5):
            user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
        return "Сделала звук потише 🔊"
    elif "громче" in action or "прибав" in action:
        for _ in range(5):
            user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
            user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
        return "Сделала звук погромче 🔊"
    elif "выключи звук" in action or "мут" in action:
        user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
        user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
        return "Переключила звук (Mute) 🔇"
    elif "пауза" in action or "плей" in action or "стоп" in action:
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
        return "Переключила трек / паузу 🎵"
    
    return "Выполнила команду управления медиа!"

def lock_windows_pc():
    """Lock Windows screen"""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Заблокировала экран твоего ПК! 🔒"
    except Exception as e:
        return f"Не удалось заблокировать ПК: {e}"

def type_text(text_to_type):
    """Type text or send to active window via clipboard"""
    try:
        import pyperclip
        pyperclip.copy(text_to_type)
        pyautogui.hotkey('ctrl', 'v')
    except Exception:
        pyautogui.typewrite(text_to_type, interval=0.02)
    time.sleep(0.3)

def execute_autonomous_computer_task(task_goal):
    """Autonomous agent loop for controlling PC based on goal"""
    goal_l = task_goal.lower()
    steps_log = []

    # Scenario: Yandex Music
    if "яндекс" in goal_l and ("музык" in goal_l or "песн" in goal_l or "трек" in goal_l):
        subprocess.Popen("start https://music.yandex.ru", shell=True)
        time.sleep(2)
        take_desktop_screenshot()
        return "Роман, открыла Яндекс.Музыку в браузере и прикрепила скриншот! 🎵🎧"

    # Scenario: Open Youtube / Music search
    if any(w in goal_l for w in ["ютуб", "youtube"]):
        search_term = re.sub(r'(включи|открой|найди|на ютубе|на youtube|ютуб|youtube|музыку|песню)', '', goal_l).strip()
        if not search_term:
            search_term = "музыка"

        yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_term)}"
        subprocess.Popen(f"start {yt_url}", shell=True)
        time.sleep(2.5)
        pyautogui.press('tab')
        time.sleep(0.3)
        pyautogui.press('enter')
        take_desktop_screenshot()
        return f"Роман, открыла YouTube и включила видео по запросу **«{search_term}»**! 🎬"

    # Scenario: Create a text file or notes in Notepad
    if any(w in goal_l for w in ["блокнот", "заметк", "документ", "напиши на пк"]):
        note_text = re.sub(r'(напиши|создай|открой|в блокноте|в файл|заметку|на пк)', '', task_goal).strip()
        if not note_text:
            note_text = "Заметка от Фелисити: Привет, Роман! Я успешно управляю компьютером!"

        subprocess.Popen("notepad.exe")
        time.sleep(1.5)
        type_text(note_text)
        time.sleep(0.5)
        take_desktop_screenshot()
        return f"Роман, создала заметку в Блокноте и напечатала: «{note_text[:50]}...»! ✍️"

    # Generic Fallback: Launch app & perform action
    app_res = open_app(task_goal)
    time.sleep(1.5)
    take_desktop_screenshot()
    return f"Роман, выполнила команду на ПК: {app_res} 🖥"
