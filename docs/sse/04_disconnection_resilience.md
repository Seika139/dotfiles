# SSE 切断耐性（Disconnection Resilience）

## 問題

SSE 接続はクライアントの都合でいつでも切れる（ブラウザを閉じる、ネットワーク断、ALB タイムアウトなど）。
AI 生成のような高コストな処理を SSE 切断時に一緒に捨ててしまうと、計算リソースとユーザー体験の両方が無駄になる。

## 設計思想: 生成と配信を完全に分離する

```text
                   SSE 接続が切れても
                   ここは止まらない
                        ↓
┌────────────────┐   Queue   ┌────────────────┐   HTTP   ┌──────────┐
│ Background Task │ ────────▶ │ SSE Generator  │ ───────▶ │ Client   │
│ (AI 生成)       │           │ (配信)          │          │          │
└───────┬────────┘           └────────────────┘          └──────────┘
        │
        │ 生成完了後
        ▼
   ┌─────────┐
   │   DB    │  ← 結果は必ず永続化される
   └─────────┘
```

## asyncio による実装パターン

### 1. asyncio.Event で切断を通知

```python
import asyncio


async def stream_generator(prompt: str):
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    disconnected = asyncio.Event()  # 切断シグナル

    task = asyncio.create_task(
        run_generation(prompt, queue, disconnected)
    )

    try:
        while True:
            chunk = await asyncio.wait_for(queue.get(), timeout=5.0)
            if chunk is None:
                break
            yield _sse_event("ai_chunk", {"content": chunk})
    except (asyncio.CancelledError, GeneratorExit):
        # クライアントが切断した
        disconnected.set()
        # バックグラウンドタスクの完了を待って DB 更新するタスクをスケジュール
        _schedule_fire_and_forget(wait_and_finalize(task))
        return

    yield _sse_event("done", {})
```

### 2. 生成側は切断を検知して Queue への put をスキップ

```python
async def run_generation(
    prompt: str,
    queue: asyncio.Queue[str | None],
    disconnected: asyncio.Event,
):
    collected_chunks: list[str] = []
    queue_abandoned = False
    consecutive_timeouts = 0
    max_timeouts = 3

    try:
        async for chunk in ai_model.stream(prompt):
            collected_chunks.append(chunk)  # DB 保存用に常に収集

            # クライアントが切断済みなら Queue に入れない
            if disconnected.is_set() or queue_abandoned:
                continue

            try:
                await asyncio.wait_for(queue.put(chunk), timeout=5.0)
                consecutive_timeouts = 0
            except TimeoutError:
                consecutive_timeouts += 1
                if consecutive_timeouts >= max_timeouts:
                    queue_abandoned = True  # Queue が詰まっている → 諦める
    finally:
        # 生成結果を DB に保存（切断されていても必ず実行）
        content = "".join(collected_chunks)
        await save_to_db(content)

        # Sentinel: 接続中なら Generator にストリーム終了を通知
        if not disconnected.is_set():
            await queue.put(None)
```

**設計のポイント:**

| 要素 | 役割 |
|------|------|
| `asyncio.Event` | 切断をバックグラウンドタスクに通知 |
| `collected_chunks` | Queue への put とは独立にチャンクを収集 → DB 保存を保証 |
| `consecutive_timeouts` | Queue が詰まったら put を諦める（バックプレッシャー制御） |
| `finally` ブロック | 例外が発生しても DB 保存を必ず実行 |

### 3. asyncio.shield で DB 保存を保護

タイムアウトしても DB 保存タスク自体は継続させたい場合に使う。

```python
save_task = asyncio.ensure_future(save_to_db(content))
try:
    await asyncio.wait_for(asyncio.shield(save_task), timeout=10.0)
except TimeoutError:
    logger.warning("db_save_timeout")
    # save_task はバックグラウンドで継続する
```

`asyncio.shield()` は「タイムアウトで `wait_for` が `CancelledError` を投げても、ラップされたタスクにはキャンセルを伝播しない」という仕組み。

### 4. asyncio.Future でバックグラウンド結果を受け渡す

バックグラウンドタスクの結果を SSE Generator 側で待ちたい場合:

```python
from dataclasses import dataclass


@dataclass
class GenerationResult:
    queue: asyncio.Queue[str | None]
    task: asyncio.Task[None]
    disconnected: asyncio.Event
    metadata_future: asyncio.Future[dict]  # 結果の受け渡し用


# バックグラウンドタスク内
if not metadata_future.done():
    metadata_future.set_result({"token_count": 150})

# SSE Generator 内
metadata = await asyncio.wait_for(result.metadata_future, timeout=10.0)
yield _sse_event("complete", metadata)
```

## クライアント側の復旧フロー

SSE が途中で切れた場合のクライアント復旧:

```text
1. SSE 接続が切れる
2. クライアントは ai_message_id を保持している
    （generation_started イベントで受信済み）
3. ポーリング: GET /messages/{id}/generation-status
    → "generating" なら待機
    → "completed" or "failed" なら次のステップへ
4. GET /messages/{id} で完成したメッセージを取得
```

```typescript
async function recoverFromDisconnect(messageId: string): Promise<Message> {
  // ポーリングで生成完了を待つ
  while (true) {
    const status = await fetch(`/messages/${messageId}/generation-status`);
    const { generation_status } = await status.json();

    if (generation_status === "completed" || generation_status === "failed") {
      break;
    }

    await new Promise((r) => setTimeout(r, 2000)); // 2秒間隔
  }

  // 完成メッセージを取得
  const res = await fetch(`/messages/${messageId}`);
  return res.json();
}
```

## 起動時の孤立メッセージ回復

サーバーがクラッシュや OOM で停止すると、`generation_status = "generating"` のまま孤立するメッセージが発生する。起動時にクリーンアップする。

```python
async def cleanup_stale_generating(timeout_seconds: int = 300):
    """起動時に呼ぶ。一定時間以上 generating のままのメッセージを failed に更新。"""
    threshold = datetime.now(UTC) - timedelta(seconds=timeout_seconds * 2)
    stale = await repo.find_by_status_before("generating", threshold)
    for msg in stale:
        msg.generation_status = "failed"
    await repo.save_all(stale)
    logger.info("cleaned_stale_messages", count=len(stale))
```

## 中間チェックポイント

長時間の処理（特許検索パイプラインなど）では、N チャンクごとに DB へ中間保存する。
SSE 切断 + サーバークラッシュの二重障害でも、途中までの結果を復旧できる。

```python
SAVE_INTERVAL = 20  # 20 チャンクごとに中間保存

chunk_count = 0
parts: list[str] = []

async for chunk in pipeline.stream():
    parts.append(chunk)
    chunk_count += 1

    if chunk_count % SAVE_INTERVAL == 0:
        await save_intermediate(message_id, "".join(parts), status="generating")

# 最終保存
await save_final(message_id, "".join(parts), status="completed")
```

## まとめ: 切断耐性パターン一覧

| パターン | 用途 |
|----------|------|
| Queue + Task 分離 | 生成と配信を独立させる |
| `asyncio.Event` (disconnected) | 切断をバックグラウンドに通知 |
| `asyncio.shield()` | DB 保存をキャンセルから保護 |
| `asyncio.Future` | バックグラウンド → Generator の結果受け渡し |
| Sentinel (`None`) | ストリーム終了の明示的シグナル |
| Consecutive timeout counter | Queue のバックプレッシャー制御 |
| Fire-and-forget task set | タスクの GC 防止 |
| Generation status ポーリング | クライアント側の復旧手段 |
| Stale message cleanup | サーバークラッシュからの復旧 |
| 中間チェックポイント | 二重障害時のデータ復旧 |
