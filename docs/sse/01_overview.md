# SSE (Server-Sent Events)

## 一言でいうと

サーバーからクライアントへ **一方向にリアルタイムでデータを送り続ける** HTTP ベースのプロトコル。
AI チャットの「文字がポツポツ表示される」ストリーミング UI を実現する。

## プロトコルのフォーマット

SSE は `text/event-stream` という Content-Type で、プレーンテキストのストリームを返す。

```text
event: user_message
data: {"id": "abc-123", "content": "こんにちは"}

event: ai_chunk
data: {"content": "はい"}

event: ai_chunk
data: {"content": "、お手伝い"}

event: done
data: {}

```

**ルール:**

- 各フィールドは `フィールド名: 値` の形式
- イベント同士は **空行** で区切る
- `event:` — イベント種別（省略すると `message`）
- `data:` — ペイロード（JSON 文字列が一般的）
- `id:` — イベント ID（再接続時の Last-Event-ID に使う）
- `retry:` — 再接続間隔（ミリ秒）
- `:` で始まる行は **コメント**（クライアントに無視される。keepalive に利用）

```text
: これはコメント。クライアントには届かない
: keepalive
```

## WebSocket との違い

```text
                SSE                         WebSocket
方向          サーバー → クライアント      双方向
プロトコル    HTTP/1.1, HTTP/2              独自プロトコル (ws://)
再接続        ブラウザが自動再接続          自前で実装
認証          Cookie / Authorization        初回ハンドシェイクのみ
ファイアウォール  HTTP なので通過しやすい   ブロックされることがある
メソッド      GET のみ (EventSource API)    N/A
バイナリ      非対応                        対応
```

**SSE を選ぶ場面:**

- サーバーからの一方向プッシュで十分（AI ストリーミング、通知、ログ配信）
- HTTP インフラ（ALB, CDN, プロキシ）をそのまま活用したい
- 自動再接続が欲しい

**WebSocket を選ぶ場面:**

- クライアント → サーバーもリアルタイムで送りたい（チャット、ゲーム）
- バイナリデータを高頻度でやり取りする

## ブラウザの EventSource API

ブラウザには標準で `EventSource` API があるが、**GET リクエストしか対応していない**。
POST でリクエストボディを送る必要がある場合（AI チャットなど）は `fetch` + `ReadableStream` でカスタム実装する。

```javascript
// 標準 EventSource（GET のみ）
const es = new EventSource("/stream");
es.addEventListener("ai_chunk", (e) => {
  console.log(JSON.parse(e.data));
});

// POST が必要な場合 → fetch + ReadableStream で自前パース（後述）
```

## ALB / リバースプロキシとの注意点

SSE は長時間接続を維持するため、以下に注意が必要:

| 項目                                       | 対策                                     |
| ------------------------------------------ | ---------------------------------------- |
| ALB アイドルタイムアウト (デフォルト 60秒) | SSE コメント (`:keepalive`) を定期送信   |
| ALB の接続時間上限 (4000秒)                | 必要なら再接続を設計に組み込む           |
| Nginx の `proxy_buffering`                 | `off` にしないとチャンクがバッファされる |
| HTTP/2 のストリーム多重化                  | 同一ドメインで複数 SSE 接続が可能になる  |
