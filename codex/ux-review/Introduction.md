# ux-review 使い方

AI にペルソナを与え、Playwright MCP で対象サービスを実際に触らせて
UI/UX の詰まりどころをレポートする仕組み。

## 全体フロー

```text
1. 初回セットアップ（1 度だけ）
   └─ Playwright MCP をユーザーグローバルに登録 → Codex 再起動

2. プロジェクトごとのセットアップ（プロジェクト初回のみ）
   ├─ この templates/ をプロジェクトの evaluation/ux_review/ などにコピー
   └─ service.md と tasks/<persona>.md をサービス用に書き換える

3. レビュー実行（何度でも）
   └─ /ux-review <service-path> <persona> [scenario]

4. 人間レビュー（毎回）
   └─ レポート末尾の `## 人間レビューメモ` を埋める
```

## ファイル構成

```text
~/dotfiles/codex/ux-review/
├── Introduction.md             # このファイル（使い方の総合ガイド）
└── templates/                  # プロジェクトにコピーする雛形の正本
    ├── README.md
    ├── service.md              # ← プロジェクトごとに必ず編集
    ├── personas/
    │   ├── newcomer.md
    │   ├── power_user.md
    │   └── domain_expert.md
    ├── tasks/                  # ← プロジェクトごとに必ず編集
    │   ├── newcomer.md
    │   ├── power_user.md
    │   └── domain_expert.md
    ├── scenarios/
    │   └── free_exploration.md
    └── reports/_template/
        └── report.md
```

スラッシュコマンド本体は `~/.codex/prompts/ux-review.md`
（実体は `~/dotfiles/codex/profiles/cg-m2-mac/prompts/ux-review.md`）。

## 1. 初回セットアップ（1 度だけ）

```bash
codex mcp add playwright -- npx '@playwright/mcp@latest'
```

Codex を **一度終了して再起動**（MCP を読み込むため）。

## 2. プロジェクトごとのセットアップ

対象プロジェクトのリポジトリルートで、以下のどちらかで雛形を配置する:

### 方法 A: スラッシュコマンド（推奨）

```text
/ux-review init <target-path>
```

例: `/ux-review init path/to/project/ux_review`

内部で `cp -R ~/dotfiles/codex/ux-review/templates/. <target-path>/`
を実行し、編集すべきファイルを案内してくれる。

### 方法 B: 手動コピー

```bash
mkdir -p <target-path>
cp -R ~/dotfiles/codex/ux-review/templates/. <target-path>/
```

### 配置後に必ず編集するファイル

1. **`<target-path>/service.md`**
   - URL・ログイン手順
   - プレフィックス規約（例: `[ux-review/<persona>/<date>]`）
   - レート制約（特許検索 API は 1 セッション N 回以内、など）
   - 禁止事項（本番にアクセスしない、等）

2. **`<target-path>/tasks/<persona>.md`**
   - そのサービス固有の典型タスクを `t1` / `t2` / `t3` として記述
   - ペルソナごとに視点を変える（newcomer は「初手」、power_user は「速さ」、domain_expert は「正確性」）

3. **`<target-path>/README.md`**（任意）
   - プロジェクト固有の補足情報。
     `path/to/project/ux_review/README.md` が参考例

ペルソナは **サービス中立な属性** として扱うので、基本的には書き換えなくてよい。
ただしサービスによって典型ユーザー層が違う場合はペルソナを増減する。

## 3. レビュー実行

```text
/ux-review <service-path> <persona> [scenario]
```

- `<service-path>`: 雛形を配置したディレクトリ
- `<persona>`: `<service-path>/personas/<persona>.md` のファイル名（拡張子なし）
- `[scenario]`: 省略時は `free_exploration`

### 実行例

```text
/ux-review path/to/project/ux_review newcomer
/ux-review path/to/project/ux_review ip_veteran
/ux-review path/to/project/ux_review planner
```

### 実行時に何が起こるか

1. コマンドが MCP 接続を確認
2. `service.md` / `personas/<persona>.md` / `tasks/<persona>.md` / `scenarios/<scenario>.md` を読み込み
3. 実行計画をユーザーに提示
4. Playwright MCP でブラウザを立ち上げ、AI がペルソナに成り切って操作
5. `<service-path>/reports/<YYYY-MM-DD>_<persona>_<scenario>/` に
   `report.md` と `screenshots/*.png` を生成
6. 生成後、人間レビューが必須であることを案内

## 4. 人間レビュー（必須）

生成された `report.md` の末尾に `## 人間レビューメモ` セクションがある。
以下を埋めてから共有する:

- **ペルソナ逸脱チェック**: AI がペルソナ設定を外れていないか
- **Issue 化する改善提案**: レポート中の提案から選ぶ
- **捨てる提案**: 優先度が低い／誤解に基づくものは理由とともに除外

AI の「感想」は一次情報として価値があるが統計的根拠ではない。
複数ペルソナ・複数回の傾向として扱う。

## コマンドが知っている運用ルール

`~/.codex/prompts/ux-review.md` に以下が埋め込まれている:

- MCP 未接続時は `codex mcp add ...` を案内して停止
- 本番環境には絶対にアクセスしない（stg 限定）
- プレフィックス規約とレート制約を毎回遵守
- レポート生成後は必ず「人間レビュー必須」をユーザーに案内

## 雛形の更新

雛形を改善したくなったら `~/dotfiles/codex/ux-review/templates/` を直接編集する。
dotfiles が正本なので、各プロジェクトにすでにコピー済みの資産には自動では反映されない
（既存プロジェクトへの反映は手動マージ）。

## 将来拡張

- **Regression Probe**: Playwright CLI + CDP attach で既知 UX バグの再発チェック（`scenarios/regression_probe.md` として追加する想定）
- **Guided Task**: 半構造化タスクでステップ数を定量化（`scenarios/guided_task.md` として追加する想定）
