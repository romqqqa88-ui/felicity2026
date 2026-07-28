import asyncio
import felicity_userbot
from telethon import functions, types

async def test():
    await felicity_userbot.client.start()
    groups = ["ru_python_chat", "spb_chat", "moscow_chat", "it_chat", "tproger_chat", "habr_com"]
    for ch in groups:
        try:
            await felicity_userbot.join_telegram_channel(ch)
            messages = await felicity_userbot.client.get_messages(ch, limit=5)
            print(f"SUCCESS GETTING MESSAGES FOR @{ch}! Found {len(messages)} messages.")
            for m in messages:
                if m.text and len(m.text) > 10:
                    print(f"  - Msg id {m.id} from {m.sender_id}: {m.text[:60]}...")
        except Exception as e:
            print(f"ERROR FOR @{ch}:", e)

if __name__ == "__main__":
    asyncio.run(test())
