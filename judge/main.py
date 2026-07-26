from __future__ import annotations

import os
import argparse
import time
import importlib
import requests
import asyncio
import websockets
from typing import Any
from urllib.parse import urljoin, urlencode, urlparse, urlunparse
import random
from dotenv import load_dotenv
load_dotenv()

parser = argparse.ArgumentParser(description="HWOJ judge worker")
parser.add_argument("--name", type=str, default="u")
parser.add_argument("--box_id", default=0)
parser.add_argument("--server_url", default="http://127.0.0.1:8000")
parser.add_argument("--poll_interval", type=float, default=3.0)
parser.add_argument("--once", action="store_true")
parser.add_argument("--work_dir", default=None, help="Directory for this worker temporary code/input/output/answer files")
args = parser.parse_args()

SECRET_KEY = os.getenv('SECRET_KEY')
JUDGER_NAME = args.name
BOX_ID = args.box_id
SERVER_URL = args.server_url
POLL_INTERVAL = args.poll_interval
WORK_DIR = args.work_dir or os.path.join("tmp", "judge", str(JUDGER_NAME))
os.makedirs(WORK_DIR, exist_ok=True)

languages = ["cpp", "python", "py", "text"]
lang_dict = {}
for i in languages:
    module_name = "python" if i == "py" else i
    module = importlib.import_module(f"languages.{module_name}")
    lang_dict[i] = module.Executor


def get_message() -> str:
    return random.choice([
        "bong thay minh qua dep trai",
        "uoc gi ta bot dang cap hon chut",
        "🐧",
        "vibe judger",
        "Wrong answer judger"
    ])


def get_header():
    return {
        "Authorization": f"Bearer {SECRET_KEY}",
        "Content-Type": "application/json",
        "name": JUDGER_NAME,
        "message": get_message()
    }


def post(path: str, payload: dict = None) -> dict[str, Any]:
    payload = payload or {}
    headers = get_header()
    safe_headers = {
        k: (v.encode('utf-8').decode('latin-1').replace('\n', r'\\n') if isinstance(v, str) else v)
        for k, v in headers.items()
    }
    response = requests.post(urljoin(SERVER_URL, path), json=payload, headers=safe_headers, timeout=30)
    response.raise_for_status()
    return response.json() if response.text else None


def websocket_url() -> str:
    parsed = urlparse(SERVER_URL)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    path = urljoin(parsed.path.rstrip("/") + "/", "judger/ws")
    query = urlencode({"token": SECRET_KEY or "", "name": JUDGER_NAME, "message": get_message()})
    return urlunparse((scheme, parsed.netloc, path, "", query, ""))


from judgers import global_judge


def judge_task(task: dict[str, Any]) -> dict[str, Any]:
    print(f"-> Đang chấm bài nộp ID: {task['id']} - {task['language']}")
    task = task.copy()
    task['language'] = lang_dict[task['language']]
    result = global_judge(box_id=BOX_ID, work_dir=WORK_DIR, **task)
    result["id"] = task["id"]
    print(f"<- Đã chấm xong bài nộp ID: {task['id']}.")
    return result


async def websocket_loop():
    uri = websocket_url()
    while True:
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
                print(f"[WebSocket] Đã kết nối tới {uri}")
                while True:
                    message = await websocket.recv()
                    data = __import__("json").loads(message)
                    message_type = data.get("type")
                    if message_type == "task":
                        result = await asyncio.to_thread(judge_task, data["task"])
                        await websocket.send(__import__("json").dumps({"type": "result", "result": result}))
                        if args.once:
                            return
                    elif message_type == "ping":
                        await websocket.send(__import__("json").dumps({"type": "heartbeat"}))
                    elif message_type == "idle":
                        if args.once:
                            return
        except Exception as exc:
            print(f"[Lỗi WebSocket]: {exc}")
            if args.once:
                return
            await asyncio.sleep(POLL_INTERVAL)


def polling_loop():
    while True:
        try:
            task = post("/judger/get-task")
            if task:
                result = judge_task(task)
                post("/judger/update-result", result)
                print(f"<- Đã gửi kết quả bài nộp ID: {task['id']} thành công.")
        except Exception as network_exc:
            print(f"[Lỗi kết nối hoặc Hệ thống]: {network_exc}")

        if args.once:
            break
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    if SECRET_KEY:
        asyncio.run(websocket_loop())
    else:
        polling_loop()
