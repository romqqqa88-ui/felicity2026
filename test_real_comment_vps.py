import asyncio
import felicity_userbot

async def run_real_group_comment():
    await felicity_userbot.client.start()
    for ch in ["tproger_chat", "it_chat"]:
        print(f"EXECUTING REAL REPLY IN GROUP @{ch}...")
        res = await felicity_userbot.comment_on_channel_post(ch)
        print(f"REPLY RESULT FOR @{ch}:\n", res)

if __name__ == "__main__":
    asyncio.run(run_real_group_comment())
