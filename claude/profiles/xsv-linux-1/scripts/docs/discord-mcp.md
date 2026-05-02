# Discord MCP セットアップ

Claude Code から Discord チャンネルへメッセージ送信／読み取りを行うための MCP サーバー設定。

## 用途と限界 (重要)

このセットアップは **Claude → Discord** の「出口」だけを提供します。

| 方向 | 実現方法 | 状態 |
|---|---|---|
| Claude → Discord (出力) | mcp-discord (このセットアップ) | ✅ |
| Discord → Claude (受動的に指示を拾う) | OpenClaw / repo-sync 等のブリッジ | ❌ (このセットアップの対象外) |

具体的に:

- ✅ できる: Claude がセッション中に `discord_send` を能動的に呼んで投稿、`discord_read_messages` で履歴を読む
- ❌ できない: Claude セッションを起動しっぱなしにして、Discord に書いた指示を Claude が自動で拾う運用
  - MCP はツール呼び出しのインタフェースで、Discord Gateway を常駐監視するエージェントではない
  - 「Discord から指示 → Claude が応答」を実現するには、別途 Gateway を張って ACP セッションを spawn するブリッジ層 (OpenClaw など) が必要

## FAQ

### Q. Claude のセッションを起動しっぱなしにしておけば、Discord から指示を出して結果を Discord で受け取れますか？

**A. できません。** MCP は **Claude → Discord の出口のみ** を提供する仕組みで、Discord 側を常駐監視するエージェントではありません。

- Claude は Discord をポーリングしない
- 新着メッセージで Claude が "起動" することもない
- セッションの起動と指示入力はあくまで端末側で行う

「Discord から指示 → Claude が応答」の運用は OpenClaw が担うレイヤー。両者は補完関係:

| やりたいこと | 使うべき仕組み |
|---|---|
| Discord から Claude に作業させて結果を Discord で見る | OpenClaw |
| 端末で起動した Claude に、進捗や結果を Discord にも書かせる | mcp-discord (このセットアップ) |
| 端末で起動した Claude に、Discord の過去ログを読ませて作業させる | mcp-discord |

### Q. MCP を導入した結果、結局何ができるようになりましたか？

**A. Claude にプロンプトで指示すれば、Discord を「道具」として読み書きしてくれる**ようになりました。

書き込み系:

- 任意チャンネルへの投稿、リアクション付与
- 公開スレッドの作成、スレッド内投稿
- チャンネルの作成・編集・削除
- Forum 投稿の作成・返信
- Webhook の作成・送信

読み取り系:

- メッセージ履歴の取得
- メッセージ検索
- サーバー情報・チャンネル一覧の取得

代表的な使い方:

- 長時間ビルドの完了通知を投稿させる
- マルチステップ作業の進捗をステップごとに投稿
- `#design` 等の過去議論を読ませてから実装させる
- CI 失敗時だけアラートチャンネルに転送
- 作業ごとにスレッドを切ってログを集約

### Q. OpenClaw の Bot Token を使い回さなかったのはなぜ？

**A. 主に Discord Gateway の排他性のため。** Discord は **1 Bot Token = 同時 1 Gateway 接続** が原則。OpenClaw は thread binding で常駐 Gateway を張っているため、同じ Token を MCP でも使うと接続が交互に切られる。加えて:

- 監査ログで両者の操作を区別できる
- 権限スコープを最小化できる
- Token rotation を独立に行える

### Q. 招待後に Bot の権限を追加したい。再招待が必要？

**A. 再招待不要。** Server Settings → ロール → Bot 名と同名の Managed Role を直接編集すれば良い。チャンネル個別の権限上書きがある場合はそちらも要確認。

### Q. 現在の権限でスレッドの作成・読み込みはできる？

**A. できる。** 招待時に `permissions=309237713920` で `Create Public Threads` と `Send Messages in Threads` を付与済み。スレッド読み取りは親チャンネルの `View Channels` + `Read Message History` で自動的に可能。

プライベートスレッド作成や archived thread 管理が必要なら追加権限 (`Create Private Threads`, `Manage Threads`) が要る。

### Q. Token をリセットしたらどうすればいい？

**A.** `.env` を更新して Claude Code セッションを再起動。詳細は「運用 → Token を更新する」を参照。

### Q. 新規 Bot を Discord サーバーに招待する手順は？

**A. Application ID を使った OAuth2 招待 URL を踏ませる方式。** Developer Portal の OAuth2 URL Generator UI はモバイルで表示崩れすることがあるので、URL を直接組むのが確実:

```text
https://discord.com/oauth2/authorize?client_id=<APPLICATION_ID>&scope=bot&permissions=<PERMISSION_INT>
```

招待時に `integration requires code grant` エラーが出る場合は Bot タブの `Requires OAuth2 Code Grant` を OFF に。

## 構成要素

| 要素 | 場所 |
|---|---|
| Bot Application | Discord Developer Portal (Application ID: `1500040400742645810`) |
| Bot Token (機密) | `~/.config/claude-discord-mcp/.env` (chmod 600) |
| 起動 wrapper | `~/dotfiles/claude/profiles/xsv-linux-1/scripts/mcp-discord.sh` |
| MCP 本体 | `~/.npm-global/bin/mcp-discord` (`mcp-discord@1.3.4`) |
| MCP 登録 | `~/.claude.json` の `mcpServers.discord` (user scope) |
| 対象 Server | `956245929818746970` (OpenClaw と共用 guild) |
| 対象 Channel | `1500051655377551440` |

### Wrapper の役割

`mcp-discord.sh` は以下をまとめている:

1. `~/.config/claude-discord-mcp/.env` を読み込む (`set -a` / `set +a` で自動 export)
2. `DISCORD_TOKEN` が設定されているか検証
3. `~/.npm-global/bin/mcp-discord` を `exec` で起動

dotfiles 側に置くことで VPS 再構築時の再現性を確保。Token は dotfiles の外 (`~/.config/`) に分離しているため Git に乗らない。

## Bot 権限 (`permissions=309237713920`)

招待時に付与した権限:

- View Channels (1024)
- Send Messages (2048)
- Read Message History (65536)
- Create Public Threads (`1<<35` = 34,359,738,368)
- Send Messages in Threads (`1<<38` = 274,877,906,944)

合計 = 309,237,713,920

## OpenClaw Bot との関係

同じ Discord サーバー (`956245929818746970`) に **OpenClaw 用 Bot と Claude MCP 用 Bot の 2 つ** が並んでいる。Token を分けた理由:

- Discord Gateway は **1 Token = 1 同時接続**。OpenClaw は thread binding で常駐 Gateway を張るため、同じ Token を MCP でも使うと競合
- 監査ログで「OpenClaw のアクション」と「Claude MCP のアクション」を識別できる
- Token rotation を独立に行える
- 権限スコープを最小化できる

## セキュリティ

- `.env`: `chmod 600` (自分以外読めない)
- `~/.config/claude-discord-mcp/`: `chmod 700`
- Token は VPS 上の home 配下のみ。dotfiles リポジトリには含まれない
- `.env.example` には Token を含まないテンプレート (Token フィールドはプレースホルダ)

## 運用

### Token を更新する

1. Discord Developer Portal で Bot Token を Reset
2. `~/.config/claude-discord-mcp/.env` の `DISCORD_TOKEN=` を更新
3. Claude Code セッションを再起動 (新 Token が読み込まれる)

### 出力先チャンネルを変える

`mcp-discord` の `discord_send` は呼び出し時に `channel_id` を指定する方式なので、MCP 側に固定の出力先は無い。

- 運用上のデフォルトは `.env` 内 `DISCORD_CHANNEL_ID` に書いてある (これは MCP 自身は読まない、人間/Claude が参照する用)
- Claude に伝える: 「`#xxx` (channel_id `1500051655377551440`) に投稿して」

### MCP を一時無効化

```bash
claude mcp remove discord -s user
# 再有効化:
claude mcp add discord -s user -- ~/dotfiles/claude/profiles/xsv-linux-1/scripts/mcp-discord.sh
```

### 接続状態の確認

```bash
claude mcp list
# discord: ... ✓ Connected   ← これが出ていれば OK
```

## トラブルシューティング

### `claude mcp list` で Connected にならない

wrapper を直接実行してエラーを確認:

```bash
~/dotfiles/claude/profiles/xsv-linux-1/scripts/mcp-discord.sh
```

- `DISCORD_TOKEN not set` → `.env` の中身と読み取り権限を確認
- `mcp-discord: command not found` → `npm i -g mcp-discord` で再インストール

### Bot がチャンネルに書けない

1. Server Settings → 連携サービス → Bot がリストにあるか
2. Bot の Managed Role の権限 (`Send Messages`) が ON か
3. 対象チャンネルの個別権限上書きで `Send Messages` を Deny していないか
4. カテゴリ階層の権限上書きも要確認

### `Requires OAuth2 Code Grant` で招待が弾かれる

Developer Portal → Bot タブ → `Requires OAuth2 Code Grant` を OFF に。デフォルト OFF だが新規 Application で稀に ON になる。

## 関連リンク

- [mcp-discord (npm)](https://www.npmjs.com/package/mcp-discord)
- [mcp-discord (GitHub)](https://github.com/barryyip0625/mcp-discord)

## 作業ログ

### 2026-05-02 初回セットアップ

- 用途確認: Claude の作業出力を Discord から確認したい (= MCP の B 用途)
  - 通知用途 (A) は repo-sync で実現済みのため対象外
  - 「Discord から指示」用途は OpenClaw が担う領域なので別レイヤー
- MCP 選定: barryyip0625/mcp-discord (`mcp-discord@1.3.4`) を採用
  - Node 製、npm に `bin` あり、機能十分、Java 系より軽量
  - 8GB RAM VPS の制約に合致
- Bot 作成: OpenClaw 用 Bot とは別に新規 Application を作成
  - Discord Gateway の排他性のため Token 共有は不可
- 権限設計: 最小権限 + thread 系 = `permissions=309237713920`
  - 後から「公開スレッドの作成」「スレッドでメッセージを送信」を Server Settings → ロール経由で追加した
- 招待時のハマり: `Requires OAuth2 Code Grant` が ON で `integration requires code grant` エラー → OFF にして解消
- Token 管理: `~/.config/claude-discord-mcp/.env` (`chmod 600`) に分離。dotfiles には wrapper のみ置いて Git に Token が混入しない設計
- スモークテスト: Discord REST API 経由で投稿成功 (message ID `1500054313232367697`、Bot 名「かにことね」)
- MCP 登録: `claude mcp add discord -s user -- <wrapper>`、`claude mcp list` で `✓ Connected` 確認
