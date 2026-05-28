# Drift Prevention Plan: PS package の prompt ↔ skill 同期維持

`Caromaf/agent-package-basic` の **PS package (prompt + skill 両建て) 12 件** で、
両ファイルの本文が drift しないようにする CI / script の設計計画。
**実装は upstream catalog repo 側で行う必要があるため、本ドキュメントは方針のみを残す**。

> **本ドキュメントの性質**: 計画書 (TODO 段階)。
> 関連: [migration-plan.md](./migration-plan.md) (PS package 両建ての drift 課題)

---

## 1. 現状の事実 (2026-05-28 計測)

`Caromaf/agent-package-basic/packages/*/` を全 21 件 walk して prompt と skill を比較した結果:

| Package           | prompt 行数 | skill 行数 | delta | 同期方針  |
| ----------------- | ----------: | ---------: | ----: | --------- |
| close-issue       |         385 |        386 |    +1 | identical |
| create-issue      |         237 |        238 |    +1 | identical |
| discover          |         238 |        237 |    -1 | identical |
| release-execute   |         131 |        126 |    -5 | identical |
| release-prepare   |          99 |         97 |    -2 | identical |
| **respond-pr**    |      **45** |    **251** |  +206 | diverged  |
| review-design-doc |          52 |         51 |    -1 | identical |
| review-pr         |         110 |        109 |    -1 | identical |
| scaffold          |         309 |        308 |    -1 | identical |
| solve-issue       |         364 |        365 |    +1 | identical |
| ux-review         |         178 |        177 |    -1 | identical |
| worktree          |         107 |        112 |    +5 | identical |

- **identical**: 11/12 件。delta ±5 行以内、frontmatter 違いのみ。同期維持が必要。
- **diverged**: 1/12 件 (respond-pr)。prompt は短い起動文、skill は詳細 workflow。
  **意図的に分担**しているので drift check 対象外 (2026-05-28 確定)。

> -S package (9 件) は skill 単独なので drift 概念なし。

### 1.1 respond-pr の意図的分担 (2026-05-28 議論)

ユーザーから「respond-pr だけ identical でないのが気になる」との指摘を受け、3 案を比較:

- **A. respond-pr 方式に 12 件全部統一** — prompt を「SKILL.md 参照」型 entry pointer に
  縮め、SKILL.md を真実の単一情報源にする。drift リスクが構造的にゼロになるが、
  11 件の prompt 書き換え工数大。
- **B. 他 11 件方式に統一** — respond-pr の prompt にも SKILL.md 全文を複製。drift CI で
  全件 identical mode を守る。工数小だが二重管理リスク残存。
- **C. 現状維持 + `x-drift-mode: diverged` 宣言** ← **採用**。respond-pr のみ意図的分担と
  明示し、残り 11 件は identical mode で CI 監視。

採用理由: respond-pr の prompt (45 行 entry pointer) は **意図的に短く保たれている**
構造で、SKILL.md (251 行) が独立して全手順を持つ。これは将来 11 件を A 方式に移行する
ための **prototype** とも見なせる。今は drift CI で 11 件の二重管理を機械的に守りつつ、
頻繁に drift が発生するようなら A 方式に段階移行する判断基準を残す。

---

## 2. 方針

### 2.1 各 package で同期方針を宣言する

`packages/<n>/apm.yml` に **`x-drift-mode`** 拡張フィールドを追加:

```yaml
name: review-pr
version: 0.1.0
description: ...
x-drift-mode: identical # or "diverged" or "skip"
includes: auto
dependencies:
  apm: []
  mcp: []
```

- **`identical`**: prompt 本文 == skill 本文 (frontmatter 除く) を CI で強制。
- **`diverged`**: 意図的に分担。CI 対象外。
- **`skip`**: -S package or 一時的に check 除外。

`x-` prefix は YAML/APM の **拡張属性慣習** に従う (APM 本体は無視)。

### 2.2 CI script の設計 (擬似コード)

```python
# scripts/check_ps_drift.py
import re
from pathlib import Path
import yaml

def strip_frontmatter(text: str) -> str:
    """先頭の --- ... --- ブロックを除去。"""
    return re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)

def normalize(text: str) -> str:
    """末尾改行・連続空行・タブを正規化して比較可能にする。"""
    text = strip_frontmatter(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

failures = []
for pkg_dir in sorted(Path("packages").iterdir()):
    apm_yml = pkg_dir / "apm.yml"
    cfg = yaml.safe_load(apm_yml.read_text())
    mode = cfg.get("x-drift-mode", "identical")  # default identical

    if mode != "identical":
        continue

    prompt_files = list((pkg_dir / ".apm/prompts").glob("*.prompt.md"))
    skill_md = pkg_dir / f".apm/skills/{pkg_dir.name}/SKILL.md"

    if not prompt_files or not skill_md.exists():
        continue  # -S package

    prompt = normalize(prompt_files[0].read_text())
    skill = normalize(skill_md.read_text())

    if prompt != skill:
        failures.append((pkg_dir.name, prompt_files[0], skill_md))

if failures:
    for name, p, s in failures:
        print(f"DRIFT in {name}:\n  prompt: {p}\n  skill:  {s}")
    raise SystemExit(1)
```

### 2.3 実行タイミング

1. **pre-commit hook**: コミット前ローカル実行。
   `mise.toml` に task 化して `mise run check-drift` で叩けるようにする。
2. **GitHub Actions** (`.github/workflows/drift-check.yml`):
   PR open 時と main push 時に同じスクリプトを回す。fail で merge block。

### 2.4 drift 検知時の修正フロー

CI fail 時、開発者は **diff を見て「prompt が真か skill が真か」を判断**:

- **drift が新しい instruction の追加だった** → 反対側にも反映。
- **drift が誤更新だった** → revert。
- **drift が必要 (e.g. respond-pr のように)** → `x-drift-mode: diverged` に変更。

---

## 3. 補完案 (drift 検知より前段)

CI で「壊れたら止める」だけでなく、**drift を起こりにくくする生成パイプライン**も検討余地あり:

### 3.1 単一 source from skill

「SKILL.md を canonical とし、prompt は SKILL.md からテンプレ生成」する。
APM の `includes:` がそのまま生成スクリプトを呼べる仕組みは無いので、`mise run sync-prompts` で
明示的に走らせる pre-commit/CI step として実装。

### 3.2 単一 source from prompt

逆方向 (prompt → skill 生成) も技術的には可能だが、SKILL.md は description が
1024 文字以内など Claude Code 固有制約があり、生成元には向かない。

### 3.3 採用判断

- **当面は §2 (CI による drift 検知のみ)** を採用。
- §3.1 は drift が頻発するようなら次のフェーズで導入。

---

## 4. 実装着手の前提

- `Caromaf/agent-package-basic` への push 権限が必要 (本 PC からは push 不可なので
  別 PC か他の手段で着手)。
- `apm.yml` に `x-drift-mode` を追加することで APM CLI 側で warning が出ないかを実機検証
  (拡張フィールドは無視されるはずだが、APM 本体のバージョンによる)。

---

## 5. 関連タスクとの依存

- **`#main` 恒常運用** (旧 `v0.1.0` tag 案は撤回): drift CI が main を block しなければ
  日常運用に影響しない。
- [migration-plan.md §8](./migration-plan.md): `custom-config` 依存 (create-issue) とは独立。
