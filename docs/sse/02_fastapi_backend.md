# FastAPI での SSE 実装パターン

## ライブラリ

[sse-starlette](https://github.com/sysid/sse-starlette) を使う。Starlette / FastAPI 用の SSE レスポンスクラスを提供。

```bash
uv add sse-starlette
```

## 基本: Async Generator で SSE を返す

```python
import json
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter

router = APIRouter()


def _sse_event(event: str, data: dict) -> dict[str, str]:
    """SSE イベントを sse_starlette が期待する dict 形式に変換する。"""
    return {"event": event, "data": json.dumps(data, default=str)}


@router.post("/messages", status_code=201)
async def create_message(body: MessageCreate):
    if body.stream:
        return EventSourceResponse(
            _stream_generator(body),
            status_code=201,
            media_type="text/event-stream",
        )
    # 非ストリームの場合は通常の JSON レスポンス
    return await _create_message_sync(body)


async def _stream_generator(body: MessageCreate):
    """Async Generator。yield するたびにクライアントに SSE イベントが送られる。"""
    yield _sse_event("user_message", {"id": str(msg.id), "content": body.content})

    async for chunk in ai_service.generate_stream(body.content):
        yield _sse_event("ai_chunk", {"content": chunk})

    yield _sse_event("done", {})
```

`★ Insight ─────────────────────────────────────`

- `default=str` を渡すと UUID や datetime が自動で文字列化される。SSE の data は文字列なので便利
- `status_code=201` は `EventSourceResponse` のコンストラクタに渡す（デコレータの `status_code` とは別に指定が必要な場合がある）
- `?stream=true` パラメータでストリーム / JSON を切り替えるのは後方互換性を保つ定番パターン
`─────────────────────────────────────────────────`

## 実践: Queue + Task パターン（生成と配信の分離）

AI 生成のような重い処理では、**生成タスク**と**SSE 配信**を分離するのが鉄則。
`asyncio.Queue` をバッファとして使い、独立した `asyncio.Task` で生成を回す。

```text
┌──────────────────┐     asyncio.Queue      ┌──────────────────┐
│  Background Task  │ ── chunk ──▶ put() ──▶ │  SSE Generator   │
│  (AI 生成)        │                         │  (get() → yield) │
│                   │ ── None (終了) ──▶      │                   │
└──────────────────┘                         └──────────────────┘
```

```python
import asyncio


async def _stream_generator(prompt: str):
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    # AI 生成を独立タスクとして起動
    task = asyncio.create_task(_run_generation(prompt, queue))

    yield _sse_event("generation_started", {"message_id": "..."})

    while True:
        try:
            chunk = await asyncio.wait_for(queue.get(), timeout=5.0)
        except TimeoutError:
            # タイムアウトしてもタスクが終了していなければ待ち続ける
            if task.done():
                break
            continue

        if chunk is None:  # Sentinel: 生成完了
            break

        yield _sse_event("ai_chunk", {"content": chunk})

    yield _sse_event("done", {})


async def _run_generation(prompt: str, queue: asyncio.Queue[str | None]):
    try:
        async for chunk in ai_model.stream(prompt):
            await queue.put(chunk)
    finally:
        await queue.put(None)  # Sentinel を送って終了を通知
```

**ポイント:**

| 要素                    | 役割                                             |
| ----------------------- | ------------------------------------------------ |
| `asyncio.Queue`         | 生成タスクと SSE generator 間のバッファ          |
| `None` (Sentinel)       | ストリーム終了のシグナル                         |
| `wait_for(timeout=5.0)` | タスク停止を検知するためのタイムアウト           |
| `task.done()`           | タイムアウト時にタスクが異常終了していないか確認 |

## Keepalive: ALB タイムアウト対策

特許検索のようにレスポンスまで時間がかかる処理では、ALB の 60 秒アイドルタイムアウトで接続が切れる。
**SSE コメント** を定期的に送ることで接続を維持する。

```python
SSE_KEEPALIVE_INTERVAL_SEC = 15  # ALB デフォルト 60秒の 1/4


async def _make_stream_with_keepalive(
    queue: asyncio.Queue[dict | None],
):
    """Queue からイベントを取り出しつつ、タイムアウト時に keepalive を送る。"""
    while True:
        try:
            event = await asyncio.wait_for(
                queue.get(), timeout=SSE_KEEPALIVE_INTERVAL_SEC
            )
        except TimeoutError:
            # SSE 仕様: ":" で始まる行はコメント → クライアントに無視される
            yield {"comment": "keepalive"}
            continue

        if event is None:  # Sentinel
            break

        yield event
```

`★ Insight ─────────────────────────────────────`

- `sse_starlette` は `{"comment": "keepalive"}` を受け取ると `: keepalive\n\n` として送信する
- ALB のアイドルタイムアウトは「データが流れない時間」で計測されるため、コメントでも十分にリセットされる
- 15 秒間隔は ALB デフォルト 60 秒の 1/4 で、安全マージンを確保しつつ無駄なトラフィックを抑える
`─────────────────────────────────────────────────`

## Fire-and-Forget タスクの GC 対策

`asyncio.create_task()` で作ったタスクは、参照がなくなると GC されてしまう。
グローバルな `set` に保持し、完了時に自動削除する。

```python
_background_tasks: set[asyncio.Task[None]] = set()


def _schedule_fire_and_forget(coro) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
```

この手法は [Python 公式ドキュメント](https://docs.python.org/3/library/asyncio-task.html#creating-tasks) でも推奨されている。
