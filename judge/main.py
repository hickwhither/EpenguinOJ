import os, argparse, json, asyncio
from redis.asyncio import Redis

from dotenv import load_dotenv
load_dotenv()

parser = argparse.ArgumentParser(description="HWOJ judge worker")
parser.add_argument("--name", type=str, default="u")
parser.add_argument("--box_id", default=0)
args = parser.parse_args()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JUDGER_NAME = args.name
BOX_ID = args.box_id

from standard import process_submission

async def start_worker():
    redis_client = Redis.from_url(
        REDIS_URL, 
        decode_responses=True,
        socket_timeout=None,
        socket_keepalive=True
    )
    print(f"{JUDGER_NAME} connected and ready!")

    try:
        while True:
            result = await redis_client.blpop("submission", timeout=30)
            if result:
                _, raw_payload = result
                payload = json.loads(raw_payload)
                await process_submission(
                    payload, box_id=BOX_ID, judger_name=JUDGER_NAME,
                )
    except asyncio.CancelledError:
        print("Worker stopping...")
    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(start_worker())