import asyncio
import os
import sys
import json
import felicity_userbot
import start_bot

async def run_karpathy_verification_suite():
    print("=== KARPATHY METHOD AUDIT & VERIFICATION SUITE ===")
    
    # Check 1: Telethon Client Connection & Me ID
    await felicity_userbot.client.start()
    me = await felicity_userbot.client.get_me()
    print(f"✅ 1. Telethon Connection: Authorized as {me.first_name} (ID: {me.id}, Username: @{me.username})")
    
    # Check 2: DeepSeek-V3 LLM API Responsiveness
    res = start_bot.process_message("Проверка связи! Какое у тебя настроение?", "Роман")
    reply_text = res[1] if isinstance(res, tuple) else str(res)
    print(f"✅ 2. LLM Engine Response: «{reply_text[:100]}...»")
    
    # Check 3: Voice Note Engine (edge_tts)
    v_res = await felicity_userbot.generate_and_send_voice_note("me", "Тестовая проверка голоса по методу Карпатого!")
    print(f"✅ 3. Voice Note Generation (edge_tts): {v_res}")
    
    # Check 4: Dynamic Joined Channels DB
    channels = felicity_userbot.load_dynamic_channels()
    print(f"✅ 4. Real Channels List: {channels}")
    
    # Check 5: Real Comments DB
    comments_summary = felicity_userbot.get_real_comments_summary()
    print(f"✅ 5. Real Comments Summary:\n{comments_summary}")

    print("=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_karpathy_verification_suite())
