import asyncio
import os
import subprocess

async def test_motion():
    photo_path = r"C:\Users\Romqqqa\.gemini\antigravity\scratch\felicity\kuni-master\data\selfie_1785361241.jpg"
    if not os.path.exists(photo_path):
        print("Photo missing locally, will test on VPS")
        return

if __name__ == "__main__":
    asyncio.run(test_motion())
