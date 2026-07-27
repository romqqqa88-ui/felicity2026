import asyncio
import felicity_userbot

class DummyEvent:
    def __init__(self):
        self.chat_id = "romqqqa1"
    async def get_sender(self):
        class Sender:
            first_name = "Роман"
            id = 12345
        return Sender()
    async def reply(self, msg):
        print("VISION ENGINE REPLY TO TELEGRAM:")
        print(msg)

async def run_vision_test():
    await felicity_userbot.client.start()
    event = DummyEvent()
    await felicity_userbot.process_incoming_photo_message(event, "test_selfie.jpg", caption="Смотри, что нашел!")

if __name__ == "__main__":
    asyncio.run(run_vision_test())
