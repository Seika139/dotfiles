# agmsg 導入検討 (調査記録・保留)

[agmsg](https://github.com/fujibee/agmsg) (cross-agent messaging for CLI AI agents) を本 dotfiles/agents 環境へ導入するかの調査記録。

> **本ドキュメントの性質**: 決定記録。2026-06-02 時点で **install task を実装済み・未実行**。`mise run install-agmsg` を走らせれば導入できる状態だが、まだ実行していない。pin した agmsg のコミット: `5aad45e85d8a541d5d202ecc58c4011749804618` (2026-06-14, upstream HEAD)。供給網レビュー済みで `2b8ddbe` (2026-05-31) から更新 (2026-06-15)。

---

## 0. agmsg とは

bash + sqlite3 のみで動く、CLI AI agent (Claude Code / Codex / Gemini CLI) 間の cross-agent messaging 基盤。daemon もネットワークも不要で、SQLite (WAL) ファイルを共有 message bus として使う。team 単位で agent が join し、双方向にメッセージを送受信できる。delivery mode は monitor (Claude Code の Monitor tool でリアルタイム push) / turn (Codex 既定、ターン間で inbox 確認) / both / off。

## 1. 結論: APM パッケージ化はしない/できない

agmsg は **APM パッケージではなく、自前のステートフル installer を持つ peer tool**。`packages/` に取り込む案は構造的に不適。

| 観点   | APM パッケージ                                    | agmsg                                                             |
| ------ | ------------------------------------------------- | ----------------------------------------------------------------- |
| 配布   | 静的なファイル展開 (`apm install`)                | installer がステートフル処理を実行                                |
| 配置先 | `~/.agents/skills/`, `~/.claude/`, `~/.codex/` 等 | `~/.agents/skills/<cmd>/` (DB 同梱)                               |
| 副作用 | なし                                              | SQLite DB 初期化、`~/.codex/config.toml` 改変、slash command 生成 |

APM の静的展開では agmsg の DB 初期化や Codex sandbox 設定を再現できないため、パッケージ化しても動かない。よって **consumer 層 (dotfiles/agents) の install 手順**として扱う。

## 2. installer が実際に行うこと (`install.sh` 精読)

- `~/.agents/skills/<cmd>/` に `scripts/` (bash 群 + lib/)、`templates/`、`db/` (messages.db)、`agents/openai.yaml`、生成 `SKILL.md` を配置する。
- Claude Code: `~/.claude/commands/<cmd>.md` に slash command を生成する (`/<cmd>` で起動)。
- Codex: `~/.codex/config.toml` の `[sandbox_workspace_write] writable_roots` に db/・teams/ を追記する (`.bak` を作成)。`$<cmd>` で起動。
- 依存: `sqlite3` 必須 (macOS は標準、Linux は要 apt install)。
- `setup.sh` は `git clone --depth 1 ... && install.sh` の curl|bash 型ラッパー。

## 3. 導入方式 (実装済み・未実行)

consumer 層の専用 mise file task として実装した。**APM (profiles/*/apm.yml) には載せない** (APM 非管理)。既存 `mise/tasks/*.sh` の作法 (file task + `#MISE` / `#USAGE` + 依存ガード) に揃えてある。

### 3.1 追加・変更したファイル

- `mise/tasks/sqlite3-available.sh` (新規): `apm-available.sh` / `uv-available.sh` と同型の hidden ガード。`command -v sqlite3` が無ければ error + exit 1。
- `mise/tasks/install-agmsg.sh` (新規): 本体。`--cmd` / `--ref` flag を持ち、`sqlite3-available` に depends。
- `mise/tasks/check-agmsg.sh` (新規): agmsg が入っているか / 各 CLI 連携 (Claude command, Copilot skill, Codex writable_roots) が wiring 済みかを `.agmsg` マーカー基準で確認する可視タスク。`--cmd` flag を持ち、install 済みなら exit 0・未 install なら exit 1 を返すので guard/CI 兼用。pin SHA は install-agmsg.sh から読み出して二重管理を避ける。
- `mise/tasks/status.sh` (変更): agmsg は APM 非宣言なので `~/.agents/skills/` の drift 検査で「extra (not declared)」と誤検出される。`.agmsg` マーカーを持つ skill dir を external として識別し、declared vs actual 比較から除外して別枠 (🔌 external) に表示するよう修正。これで `declared=N actual=N ✅ in sync` を保ちつつ agmsg を可視化できる。

### 3.2 使い方

```bash
mise run install-agmsg                 # cmd=agmsg, pin 済み SHA で導入
mise run install-agmsg -- --cmd m      # コマンド名を変える場合 (引数は -- の後ろ)
mise run install-agmsg -- --ref <sha>  # pin を一時上書き
mise run check-agmsg                   # 入っているか / 連携 wiring を確認
```

- pin SHA を上げた後は `mise run install-agmsg` を再実行すれば良い。既存 install (`.agmsg` マーカー) があれば install.sh が `--update` 経路に入り、DB / team を保持したまま新 SHA の scripts・SKILL.md に更新する。
- 取得: `setup.sh` の curl|bash は使わず、**SHA pin で `git clone --filter=blob:none --no-checkout` → checkout → ローカルの install.sh 実行**。
- 冪等: `~/.agents/skills/<cmd>/.agmsg` マーカーを見て、既存なら `install.sh --update` (DB/team 保持)、無ければ新規 `--cmd`。
- pin 更新: agmsg 側の差分をレビューしてから `DEFAULT_AGMSG_REF` を上げる。
- 適用範囲: profile (マシン) ごとに要否が異なるため、全 PC 一律ではなく必要な PC でのみ task を走らせる運用 (APM profiles とは別管理)。

## 4. 注意点 (dotfiles/agents 実装の精読で更新, 2026-06-02)

### 4.1 共存リスクは低い (当初評価から下方修正)

当初「`apm prune` が agmsg dir を消す」懸念を挙げたが、実装精読で**リスクは低い**と判明:

- **dotfiles/agents の install/update task は `apm prune` を使わない**。`mise/tasks/install.sh` は `apm install -g --frozen`、`update.sh` は `apm install -g --refresh --force` のみ。prune 系コマンドは登場しない。
- **APM は所有権を追跡する**。update.sh のコメントいわく、lock を消して `--refresh` すると APM が「自分が書いていないファイル」を上書き拒否する (`--force` で初めて許可)。つまり APM は自分が deploy したファイルしか触らない。agmsg の `~/.agents/skills/agmsg/` は APM 非管理 dir なので、`apm install -g` は触らない。
- 残る唯一の現実的注意: **APM package 名に `agmsg` を使わない** (使うと `~/.agents/skills/agmsg/` がパス衝突する)。現状そんな package は無い。`update.sh` の `--force` はパス衝突したファイルのみ上書きするので、別名なら無関係。

### 4.2 改変先は全て実体ファイル (symlink 汚染なし)

agmsg installer が書き込む先を確認した結果、いずれも実ディレクトリ/実ファイルで、dotfiles repo への symlink 経由の書き込み事故は起きない (README §設計原則1 と整合):

| 改変先                        | 実体/symlink      | 備考                                                             |
| ----------------------------- | ----------------- | ---------------------------------------------------------------- |
| `~/.agents/skills/agmsg/`     | 実 dir            | APM cross-tool 配置先と同居 (別名なので非衝突)                   |
| `~/.claude/commands/agmsg.md` | 実 dir に新規生成 | Claude の slash command                                          |
| `~/.codex/config.toml`        | 実ファイル (600)  | 既存 `sandbox_workspace_write` 無し → agmsg が新規セクション追記 |

### 4.3 残る注意点

- **Codex config の編集は版管理外**: `~/.codex/config.toml` は実ファイルで dotfiles 非追跡。agmsg が追記する `[sandbox_workspace_write] writable_roots` は git 管理されないため、別 PC で再現するには task 側で再適用する (= agmsg install を各 PC で走らせる) 必要がある。`.bak` は作られる。
- **供給網**: 配布は `setup.sh` の curl|bash 型。必ず pin した SHA の内容を確認してから実行する (本調査では `2b8ddbe` を精読済み)。2026-06-15 に `2b8ddbe`→`5aad45e` (HEAD) へ更新する際も install.sh / install 時実行 script の差分をレビュー済み。なお npm package (`bin/agmsg.js` の curl 取得) はこの task では使わず、SHA pin clone → `install.sh` 直接実行のため当該経路の供給網リスクは対象外。
- **依存**: `sqlite3` 必須。hm-m1-mac では `/usr/bin/sqlite3` (3.51.0) 確認済み。Linux profile では別途要確認。

## 5. 関連

- delegate-worktrees skill とは別物。あちらは委任の段取り、agmsg は agent 間通信 transport。両者は独立に扱う。
- agmsg は Claude 専用・実験的な Agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`) の代替候補。ランタイム非依存 (Claude/Codex/Gemini) で安定している点が tool 非依存方針に合う。
- 公式: <https://agmsg.cc/> / <https://github.com/fujibee/agmsg>
