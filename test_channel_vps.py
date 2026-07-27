import asyncio
import felicity_userbot

async def main():
    await felicity_userbot.client.start()
    felicity_userbot.set_own_channel("felicity_moments")
    print("CHANNEL SET SUCCESS: @felicity_moments")
    res = await felicity_userbot.publish_post_to_own_channel("Открытие моего личного канала и первые уютные мысли ✨")
    print("PUBLISH RESULT:\n", res)

if __name__ == "__main__":
    asyncio.run(main())
