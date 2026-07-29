import os, argparse, json
from redis import asyncio
from redis.asyncio import aioredis

from dotenv import load_dotenv
load_dotenv()

parser = argparse.ArgumentParser(description="HWOJ judge worker")
parser.add_argument("--name", type=str, default="u")
parser.add_argument("--box_id", default=0)
parser.add_argument("--server_url", default="http://127.0.0.1:8000")
args = parser.parse_args()

SECRET_KEY = os.getenv('SECRET_KEY')
REDIS_URL = os.getenv("REDIS_URL")
JUDGER_NAME = args.name
BOX_ID = args.box_id
SERVER_URL = args.server_url

from standard import process_submission

async def start_worker():
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    print(f"{JUDGER_NAME} connected and ready!")

    try:
        while True:
            result = await redis_client.brpop("submission", timeout=0)
            if result:
                _, raw_payload = result
                payload = json.loads(raw_payload)
                await process_submission(payload)
    except asyncio.CancelledError:
        print("Worker stopping...")
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(start_worker())

