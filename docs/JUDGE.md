# HWOJ Judge

The judge receives submissions from the backend via Redis, runs them in an `isolate` sandbox, and writes results back to Redis (which the backend persists).

## Requirements

- Python 3.12+
- `isolate` sandbox (IOI's isolate with cgroup support)
- Redis (shared with backend)

## Isolate setup

```bash
git clone --depth 1 https://github.com/ioi/isolate.git /tmp/isolate
make -C /tmp/isolate isolate install
rm -rf /tmp/isolate
```

Requires `libcap-dev` and `pkg-config` on Debian/Ubuntu.

## Configuration

Copy `example.env` to `.env` and set `REDIS_URL`:

```env
REDIS_URL=redis://localhost:6379
```

## Running

```bash
cd judge
uv sync
python main.py --name=worker1 --box_id=0
```

Arguments:
- `--name` — worker name (shows in submission judger_name)
- `--box_id` — isolate sandbox box ID (must be unique per worker)

## Supervisor (production)

```bash
cp configs/hwoj-judge.conf /etc/supervisor/conf.d/
# Edit paths in the config to match your deploy directory
supervisorctl reread && supervisorctl update
```

Runs 4 worker processes (box_00 through box_03) by default. Each worker gets a unique box_id and name.

## Docker (alternative)

```bash
docker build -t hwoj-judge ./judge

docker run --rm \
  --privileged \
  --name hwoj-judge \
  --network="host" \
  -e REDIS_URL=redis://localhost:6379 \
  hwoj-judge \
  --name=worker1 --box_id=0
```

Flags:
- `--privileged` — required for isolate cgroup sandbox
- `--network="host"` — connect to host Redis

## Architecture

```
Backend → Redis (submission list) → Judge → Redis (live:{id} + results list) → Backend consumer → DB
                                                                                    ↓
                                                                               SSE → Frontend
```

No HTTP calls between judge and backend. The judge only talks to Redis.
