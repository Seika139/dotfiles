---
description: "最後の git タグからのコミットを分類し、CHANGELOG.md の Unreleased セクションを更新します"
argument-hint: "[sinceTag?]"
allowed-tools: >
  Bash(git describe:*), Bash(git log:*), Bash(grep:*), Bash(awk:*), Bash(sed:*), Bash(date:*), Bash(tr:*), Bash(git rev-list:*), Bash(git rev-parse:*), Bash(test -f:*), Bash(echo:*), Bash(cat:*), Bash(head:*), Bash(tail:*), Bash(cd:*), Bash(pwd:*), Bash(basename:*), Bash(dirname:*), Bash(touch:CHANGELOG.md), Read(CHANGELOG.md), Write(CHANGELOG.md)
---

# Claude Prepare CHANGELOG.md

現在のリポジトリの状況を把握した上で、CHANGELOG.md の `## [未リリース]` セクションを更新します。
以下の手順で実行してください。

## Ensure Git Repository and CHANGELOG.md

まず、現在のディレクトリが Git リポジトリであることを確認します。

```bash
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  echo "Error: This command must be run inside a Git repository."
  exit 1
fi
```

次に、`CHANGELOG.md` ファイルが存在することを確認します。存在しない場合はエラーを出力して終了します。
現在のディレクトリがリポジトリのルートでない場合は、適宜 `cd` コマンドでルートに移動してください。

```bash
if [ ! -f CHANGELOG.md ]; then
  echo "Warning: CHANGELOG.md file not found."
fi
```

## Context

- Latest tag: !`git describe --tags --abbrev=0 2>/dev/null || echo ""`
- Today: !`date +%Y-%m-%d`
- Raw commits (since latest tag or `$1` if provided): !`(BASE=${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "")}; if [ -n "$BASE" ]; then git log $BASE..HEAD --pretty=format:'%s'; else git log --pretty=format:'%s' ; fi)`

## Create CHANGELOG.md if Missing

リポジトリルートに `CHANGELOG.md` が存在しない場合は、以下の `CHANGELOG.md` を作成します。

```markdown
# CHANGELOG

すべての注目すべき変更はこのファイルに記録されます。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/lang/ja/) に準拠しています。

## [未リリース]

```

## Edit CHANGELOG.md

`CHANGELOG.md` の `## [未リリース]` セクションを

- [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/)
- [Semantic Versioning](https://semver.org/lang/ja/)

に基づいて更新します。

### Notes

- PR や Issue の番号は `(#123)` のように括弧付きで記載します。
- このコマンドは `CHANGELOG.md` のみを編集し、コミットやタグ付けは行いません。新しくバージョンや日付を追加しないでください。
- リスト項目は簡潔かつ統一的な表現で記載してください。
