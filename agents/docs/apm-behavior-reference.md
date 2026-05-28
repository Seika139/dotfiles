# APM 実挙動リファレンス

APM の進化は著しいので、このリファレンスも陳腐化している可能性がある。必ず最新情報を [APM 公式ドキュメント](https://microsoft.github.io/apm/quickstart/) で確認すること。

APM CLI が「どの CLI のどの path に何を配備するか」「どの flag が何をするか」の **実証済み挙動**をまとめる。移行手順 (process) は `migration-plan.md` / `migration-checklist.md` / `sync-guide.md`、instructions 固有の罠は `instructions-primitive.md` を参照。本書は **APM の挙動そのもの (reference)** を扱う。

最終更新: 2026-05-29 (旧 ONBOARDING.md §3/§5.8/§7 を移設・再構成)

---

## 1. skill 配備フラグ戦略 (結論)

採用 flag: **なし — `apm install -g --frozen` のみ** (`agents/mise/tasks/install.sh`)。
update は `apm install -g --refresh --force` (`update.sh`)。

理由: Claude/Codex/Gemini はいずれも default 配備で skill を認識する (2026-05-28 実機検証)。
かつて `--legacy-skill-paths --exclude agent-skills` を使っていたが冗長と判明し撤去した (§4)。

---

## 2. CLI 別 skill 読み取り path (2026-05-28 実機検証)

APM のデフォルト skill 配備先は **`.agents/skills/<n>/SKILL.md` (cross-tool 共有先)**。
ただし各 CLI が読みに行く path は異なる:

| CLI                  | per-tool (`~/.<tool>/skills/`) | cross-tool (`~/.agents/skills/`) | 備考                                                                                                          |
| -------------------- | ------------------------------ | -------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Claude Code**      | ✅ 読む                        | ❌ 読まない                      | default install で `~/.claude/skills/` に自動配備 (Claude 特別扱い)                                           |
| **Codex CLI**        | ✅ 読む                        | ✅ 読む                          | **conflict resolution 無し** → per-tool と cross-tool 両方にあると **2 重発火**                               |
| **Gemini CLI**       | ✅ 読む                        | ✅ 読む                          | **conflict resolution あり** (`.agents/skills/` 優先で per-tool を override、`gemini skills list` で警告表示) |
| **Cursor / Copilot** | (per-tool 配備で動作中)        | ❓ 未検証                        | CLI 検証手段なし (IDE / 別 install 必要)                                                                      |

### default 配備の実機結果 (per-tool clean → `apm install -g --frozen`)

| Target           | per-tool          | cross-tool | 動作                                      |
| ---------------- | ----------------- | ---------- | ----------------------------------------- |
| Claude           | 21 (default 配備) | 21         | ✅ per-tool 読む                          |
| Codex            | 0                 | 21         | ✅ cross-tool 読む (1 重、2 重発火しない) |
| Gemini           | 0                 | 21         | ✅ `gemini skills list` で 21 件認識      |
| Copilot / Cursor | 0                 | 21         | ❓ 未検証 (skill 主用しないなら影響なし)  |

→ Claude は per-tool に自動で来る + Codex/Gemini は cross-tool を読むので **default で全員動く**。

### `gemini skills list` (Gemini 固有の利点)

Gemini は公式 CLI `gemini skills <list|enable|disable|install|link|uninstall>` を持ち、skill 認識状況の確認・per-skill enable/disable が CLI で完結する。Codex/Claude より進んでいる。

---

## 3. APM 物理制約表 (方針非依存の汎用資料)

| 項目                                | 結論                                                                                                                                                                                                                                                                  |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| codex は APM の正式 target か       | ✅ YES (`apm init` の Accepted values に codex 明記)                                                                                                                                                                                                                  |
| 出力スコープ                        | ✅ repo-local + `-g` で user-scope (`~/.apm/` and 各ツール global)                                                                                                                                                                                                    |
| APM prompt primitive の Codex 対応  | ❌ prompt は Codex に出力されない ("Codex has no prompts/commands primitive")。Codex カバーには skill primitive 必須                                                                                                                                                  |
| ツール別コンテンツ変数/テンプレート | ❌ 存在しない。単一ソースは全 target に byte 同一配備                                                                                                                                                                                                                 |
| ネスト/名前空間 prompt              | ❌ 非対応。`/release:prepare` は不可、フラット `/release-prepare` 化                                                                                                                                                                                                  |
| `apm install -g` 実用度             | ✅ skill は `~/.claude/skills/`, `~/.codex/skills/` 等に正常配備。MCP は Copilot CLI と Codex CLI のみ global 対応                                                                                                                                                    |
| `apm install -g` の manifest 探索   | ⚠️ **cwd を見ない**。`~/.apm/apm.yml` を見る。無いと "Run 'apm install -g <org/repo>' to auto-create + install" で非ゼロ終了 → install.sh は profile/apm.yml を ~/.apm/apm.yml にコピーしてから install する (§5)                                                     |
| user-scope primitive 対応マトリクス | **fully**: claude, gemini, agent-skills, copilot-cowork。**partial**: copilot, cursor, opencode, codex, windsurf。**特定非対応**: copilot (prompts, instructions), cursor (instructions), opencode (hooks), windsurf (instructions)                                   |
| auto-detect の条件                  | ✅ home dir `~/.<tool>/` の存在。実機 (hm-m1-mac) で claude/codex/gemini/copilot/cursor の 5 つを検出 (windsurf/opencode は ~/ に dir 無し → 対象外)。**ただし consumer apm.yml には `targets:` 明示を推奨** (`apm update` が targets 未指定でエラーを出した記録あり) |
| skill デフォルト deploy 先          | ✅ `.agents/skills/<n>/SKILL.md` (cross-tool 共有先)                                                                                                                                                                                                                  |
| `--legacy-skill-paths` 効果         | skill を 5 tools 全部の per-tool path にも配備 (`.claude/skills/` 等)。**現在は未使用** (default で足りるため、§4)                                                                                                                                                    |
| `--exclude agent-skills` 効果       | cross-tool 共有先への配備を抑制。`--legacy-skill-paths` と組で Codex 2 重発火回避に使ったが**現在は未使用**                                                                                                                                                           |
| `--force` の意義                    | lock 削除 + `--refresh` 時に既存ファイル (前回 deploy 物) を「APM 管理外」と判定して上書き拒否する問題を回避。**update task のみで使用** (install は lock 尊重で副作用最小)                                                                                           |
| 配備の冪等性                        | ⚠️ 2 回目 install で `stale files cleaned` + `files skipped` が出る。stale = APM 追跡内の古い deploy 撤去、skipped = 追跡外の既存 file                                                                                                                                |
| instructions の deploy              | Claude/Cursor は file 配備 (`~/.claude/rules/` 等)、Codex/Gemini は AGENTS.md/GEMINI.md compile 統合。`.instructions.md` suffix + `description` frontmatter 必須 (`instructions-primitive.md`)                                                                        |

---

## 4. flag 戦略の方針転換ログ (default 採用の経緯)

当初 `--legacy-skill-paths --exclude agent-skills` を採用していたが、検証で撤去した。

### 経緯

1. 初回 install (no flag) で `~/.codex/skills/` が空 →「Codex に届かない」と誤判断
2. `--legacy-skill-paths` 追加 → 全 5 tool の per-tool path に配備 → **Codex が per-tool + cross-tool 両読みで 2 重発火**
3. `--exclude agent-skills` 追加 → cross-tool 配備を抑制して 2 重回避
4. **再検証で判明**: Codex も Gemini も cross-tool (`~/.agents/skills/`) を読む。
   → 初回の「Codex に届かない」判断が誤りだった (per-tool だけ見て cross-tool を見ていなかった)
5. **default に戻す**: per-tool clean → `apm install -g --frozen` で Claude/Codex/Gemini 全員動作確認

### 教訓

- API 仕様を推測せず **実機の deploy 先を全部確認**する (per-tool だけ見て判断しない)
- `0 instructions` / deploy ゼロは **silent failure** — lock の `deployed_files` を見ないと気づけない
- flag を盛る前に「本当に必要か」を default で検証する (今回は 3 段の対症療法が default 化で全部解消した)

### Cursor / Copilot で skill 認識しない場合 (将来発覚時の選択肢)

- A: 該当 CLI 用に `--legacy-skill-paths` を install.sh に部分復活
- B: per-tool symlink を手動で `~/.{cursor,copilot}/skills/ -> ~/.agents/skills/` 張る
- C: 該当 CLI を諦める (現実的)

---

## 5. install -g の manifest 探索と profile シンク方式

`apm install -g` は **cwd ではなく `~/.apm/apm.yml`** を読む。そのため downstream の
profile apm.yml を ~/.apm/ に届ける必要がある。`agents/mise/tasks/install.sh` の採用方式:

1. `cp profile/apm.yml ~/.apm/apm.yml` (既存と差分があればバックアップ。private overlay 時は merge)
2. `cp profile/apm.lock.yaml ~/.apm/apm.lock.yaml` (あれば)
3. `apm install -g [--frozen]` (cd 不要、~/.apm を直接見る)
4. 新規 lock 生成時は ~/.apm/apm.lock.yaml を profile/ にコピーバック (commit 対象)

**未実装の懸念**: profile から package を除外しても `~/.claude/skills/<n>/` は残る。
`apm prune -g` 等の cleanup step を将来追加要。

---

## 6. その他の APM 実務メモ

- primitive 配備は **`apm install`**。`apm compile` は **AGENTS.md 統合専用**で prompt/skill を配備しない。
- 複数 target は **カンマ区切り** `--target codex,claude`。フラグ反復 `--target a --target b` は最後のみ採用される罠。
- skill frontmatter: `name` (小文字英数ハイフン・1–64字・dir 名と一致必須)、`description` (命令形 "Use when …"・≤1024字)。
- prompt 命名は `<name>.prompt.md` (`.prompt.md` suffix 必須。無いと無視される)。
- **hidden-character スキャン**: 日本語/記号混在で install 時に "contains hidden characters" 警告が出ることがある。
  **方針**: 事前一括 `--force` は採らず、警告が出た時点で個別クレンジング。2026-05-28 時点で
  basic catalog 21 package の全 `*.md` をスキャンし 0 件 (恒常問題ではない)。
- **shell script の実行権限**: `.apm/skills/<n>/scripts/*.sh` は git commit 時に実行ビット欠落しがち。
  upstream で `mise run grant-permission` を pre-commit/CI で回す。
- CLI 導入: mac/linux `curl -sSL https://aka.ms/apm-unix | sh` / win `irm https://aka.ms/apm-windows | iex`。
  private dependency は全 PC で `GITHUB_APM_PAT`。
- 再現配布: `apm.yml` + `apm.lock.yaml` を commit、各 PC で `apm install --frozen`。
- CLI には `--working-dir` フラグ無し → `cd` 必須。
- ドキュメント: <https://microsoft.github.io/apm/>
