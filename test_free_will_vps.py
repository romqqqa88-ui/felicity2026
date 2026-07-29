import asyncio
import felicity_userbot

async def run_free_will_test():
    await felicity_userbot.client.start()
    print("EXECUTING REAL COMMENT & DM TEST...")
    res_comment = await felicity_userbot.comment_on_channel_post("tproger_chat")
    print("REAL COMMENT RESULT:", res_comment)
    res_dm = await felicity_userbot.send_real_dm_to_random_user()
    print("REAL DM RESULT:", res_dm)

if __name__ == "__main__":
    asyncio.run(run_free_will_test())
