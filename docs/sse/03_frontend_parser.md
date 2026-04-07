# フロントエンドでの SSE パーサー実装

## なぜカスタム実装が必要か

ブラウザ標準の `EventSource` API は **GET リクエストしかサポートしていない**。
AI チャットのように POST でリクエストボディ（プロンプトなど）を送る場合は、`fetch` + `ReadableStream` で SSE を自前パースする必要がある。

## TypeScript による Async Generator パーサー

```typescript
export interface SSEEvent {
  event: string;
  data: string;
}

/**
 * fetch の Response から SSE イベントを順次パースする Async Generator。
 * EventSource と違い、POST リクエストに対応できる。
 */
export async function* parseSSEStream(
  response: Response,
): AsyncGenerator<SSEEvent> {
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";
  let currentData = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // stream: true → マルチバイト文字がチャンク境界で分割されても正しくデコード
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");

      // 最後の要素は未完成の行かもしれないのでバッファに残す
      buffer = lines.pop() ?? "";

      for (const rawLine of lines) {
        const line = rawLine.trim(); // \r\n 対策

        if (line === "") {
          // 空行 = イベント区切り
          if (currentData) {
            yield { event: currentEvent || "message", data: currentData };
          }
          currentEvent = "";
          currentData = "";
          continue;
        }

        if (line.startsWith("event:")) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          currentData = line.slice(5).trim();
        }
        // ":" で始まる行（コメント）は無視される
      }
    }

    // ストリーム終了後、バッファに残ったイベントを処理
    if (currentData) {
      yield { event: currentEvent || "message", data: currentData };
    }
  } finally {
    reader.releaseLock();
  }
}
```

## 使い方

```typescript
const response = await fetch("/v1/rooms/123/messages?stream=true", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ content: "こんにちは" }),
});

for await (const event of parseSSEStream(response)) {
  switch (event.event) {
    case "ai_chunk":
      const { content } = JSON.parse(event.data);
      appendToUI(content);
      break;
    case "error":
      handleError(JSON.parse(event.data));
      break;
    case "done":
      finalize();
      break;
  }
}
```

## 実装上の注意点

### 1. チャンク境界の分割

ネットワークのチャンクは SSE のイベント境界と一致しない。1 つのチャンクに複数イベントが含まれたり、1 つのイベントが複数チャンクにまたがることがある。

```text
チャンク 1: "event: ai_chunk\ndata: {\"content\": \"こん"
チャンク 2: "にちは\"}\n\nevent: done\ndata: {}\n\n"
```

対策: `buffer = lines.pop() ?? ""` で未完成の行を次のチャンクに持ち越す。

### 2. マルチバイト文字の分割

UTF-8 のマルチバイト文字（日本語など）がチャンク境界でバイト単位で分割されることがある。

対策: `TextDecoder.decode(value, { stream: true })` を使う。`stream: true` により、不完全なバイト列を内部にバッファし、次の `decode` 呼び出し時に結合してくれる。

### 3. リソースリーク防止

`finally` ブロックで `reader.releaseLock()` を必ず呼ぶ。
呼ばないと `ReadableStream` がロックされたままになり、GC されるまで解放されない。

### 4. `\r\n` 対応

SSE サーバー実装（特に `sse_starlette`）によっては行末が `\r\n` になる。
`split("\n")` 後に `trim()` することで `\r` を除去する。
