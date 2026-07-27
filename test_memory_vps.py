import asyncio
import felicity_userbot

async def run_memory_test():
    await felicity_userbot.client.start()
    felicity_userbot.save_user_personal_fact("Роман", "Любит атмосферный музыкальный вайб Siberian Chill - Sunset Drive 🎵")
    felicity_userbot.save_user_personal_fact("Роман", "Создатель и лучший друг Фелисити ✨")
    summary = felicity_userbot.get_user_personal_facts("Роман")
    print("MEMORY SUMMARY FOR ROMAN:\n", summary)

if __name__ == "__main__":
    asyncio.run(run_memory_test())
