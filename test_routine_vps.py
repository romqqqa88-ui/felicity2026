import asyncio
import felicity_userbot

async def run_routine_test():
    status = felicity_userbot.get_felicity_routine_status()
    print("ROUTINE STATUS TEST:\n", status)

if __name__ == "__main__":
    asyncio.run(run_routine_test())
