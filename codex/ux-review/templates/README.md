# UX Review Templates

`/ux-review init <target-path>` で展開される雛形一式。
新サービスで UX Review を始める時のスタート地点。

正本: `~/dotfiles/codex/ux-review/templates/`
総合ガイド: `~/dotfiles/codex/ux-review/Introduction.md`

## 含まれるもの

```text
templates/
├── README.md                # このファイル（コピー後は任意で削除）
├── service.md               # サービス情報の雛形 — プロジェクトごとに必ず編集
├── personas/                # 汎用ペルソナ（属性のみ、サービス語彙なし）
│   ├── newcomer.md
│   ├── power_user.md
│   └── domain_expert.md
├── tasks/                   # 汎用タスク雛形 — プロジェクトごとに必ず編集
│   ├── newcomer.md
│   ├── power_user.md
│   └── domain_expert.md
├── scenarios/
│   └── free_exploration.md  # サービス非依存のシナリオ（そのまま使える）
└── reports/_template/
    └── report.md
```

## 新サービスに展開したら

1. `service.md` を埋める（URL、ログイン、プレフィックス規約、レート制約）
2. `personas/` を必要に応じて足す or 削る
3. `tasks/<persona>.md` にそのサービス固有の典型タスクを書く
4. README を書き換えてチームメンバーに共有

サービス固有の語彙は **personas ではなく tasks 側に寄せる** のが保守のコツ。
ペルソナは職種・習熟度のような属性軸、タスクはサービス × ペルソナの交点、
という役割分担。

---

## 実際の README の 例

AI にペルソナを与え、Playwright MCP 経由で stg 環境を実際に触らせ、UI/UX の詰まりどころ・改善余地をレポートとして収集するための枠組み。

[Issue #123](https://github.com/org/repo/issues/123) が起点

## 位置付け

このディレクトリは **サービス用の UX Review 資産置き場**。
呼び口（スラッシュコマンド）と雛形はユーザーグローバルにある:

- スラッシュコマンド: `~/.codex/prompts/ux-review.md`
- 他サービス向け雛形: `~/dotfiles/codex/ux-review/templates/`

## 使い方

### 1. 初回セットアップ（1 度だけ）

```bash
codex mcp add playwright -- npx '@playwright/mcp@latest'
# Codex を終了 → 再起動（MCP を読み込むため）
```

### 2. レビュー実行

新しい Codex セッションで以下を打つ:

```text
/ux-review path/to/project/ux_review newcomer
```

第 2 引数のペルソナは `newcomer` / `power_user` / `domain_expert` から選ぶ。
第 3 引数の scenario は省略可（既定 `free_exploration`）。

### 3. レポートのレビュー

実行後に生成される `reports/YYYY-MM-DD_<persona>_<scenario>/report.md`
を開き、末尾の `## 人間レビューメモ` 欄を埋める:

- ペルソナ設定からの逸脱がないか確認
- Issue 化する改善提案を選ぶ
- 捨てる提案には理由を添える

## ディレクトリ構成

```text
ux_review/
├── README.md            # このファイル
├── service.md           # サービス固有の設定（URL, ログイン, 規約）
├── personas/            # ペルソナ定義（誰として触るか）
│   ├── newcomer.md
│   ├── power_user.md
│   └── domain_expert.md
├── tasks/               # ペルソナ × サービスの典型タスク
│   ├── newcomer.md
│   ├── power_user.md
│   └── domain_expert.md
├── scenarios/           # 実行の型
│   └── free_exploration.md
└── reports/             # 実行結果
    ├── _template/report.md
    └── YYYY-MM-DD_<persona>_<scenario>/
```

## ペルソナ・タスクの増やし方

- **ペルソナを増やす**: `personas/<name>.md` と `tasks/<name>.md` を追加
  - （ペルソナには属性・語彙・嫌がることを、タスクにはサービスでの典型タスクを書く）
- **タスクを調整する**: `tasks/<persona>.md` を編集。`t1` `t2` `t3` の ID は維持するとレポートの比較がしやすい
- **ペルソナ自体は各サービスで使い回せる想定**。サービス固有の語彙は tasks 側に寄せる

## 他サービスで同じ仕組みを使う

新サービス X を対象にする場合:

```text
/ux-review init <X-repo>/evaluation/ux_review
```

`~/dotfiles/codex/ux-review/templates/` から骨格がコピーされる。
その後 `service.md` と `tasks/*.md` を編集すれば
`/ux-review <X-repo>/evaluation/ux_review <persona>` で実行できる。

## 運用上の注意

- AI の「感想」は一次情報。統計的根拠ではない。複数ペルソナ・複数回の
  傾向として扱うこと
- レポートは **事実と解釈を分ける**（行動ログ＝事実、気づき＝解釈）
- 改善案は Issue 化する前にチーム内でレビューする（AI の違和感が必ずしも正しい優先度とは限らない）
