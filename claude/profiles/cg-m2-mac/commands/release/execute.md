---
description: "CHANGELOG.md を更新し、SemVer のタグを作成してgit pushします"
allowed-tools: >
  Bash(git tag:*), Bash(git add:*), Bash(git commit:*), Bash(git push:*), Bash(git describe:*),
  Bash(git status:*), Bash(git diff:*), Bash(git branch:*), Bash(git log:*), Bash(git rev-list:*),
  Bash(git rev-parse:*), Bash(grep:*), Bash(awk:*), Bash(sed:*), Bash(date:*), Bash(tr:*),
  Bash(test -f:*), Bash(echo:*), Bash(cat:*), Bash(head:*), Bash(tail:*), Bash(cd:*),
  Bash(pwd:*), Bash(basename:*), Bash(dirname:*), Read(CHANGELOG.md), Write(CHANGELOG.md)
---

# Update CHANGELOG.md and Create Git Tag

現在のリポジトリの状況を把握した上で、新しいバージョンを作成します。
CHANGELOG.md を更新し、SemVer に基づいたタグを作成して git push します。
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

もし `CHANGELOG.md` が存在しない場合は、 `/release:prepare` コマンドを実行して `CHANGELOG.md` を作成するように促してください。

## Context

- Today: !`date +%Y-%m-%d`

## Analyze Repository Status

現在のリポジトリの状況を確認します：

```bash
echo "=== Repository Status ==="
echo "Current branch: $(git branch --show-current)"

STATUS=$(git status --porcelain)
if [ -z "$STATUS" ]; then
  echo "Git status: Clean working directory"
else
  echo "Git status: Uncommitted changes found"
  git status --porcelain
fi

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
echo "Latest tag: $LATEST_TAG"

echo "Commits since latest tag:"
if [ "$LATEST_TAG" != "0.0.0" ]; then
  git log "$LATEST_TAG..HEAD" --pretty=format:'- %s (%h)' | head -10
else
  echo "- No previous tags found"
  git log --pretty=format:'- %s (%h)' | head -10
fi
```

## Recognize Latest Version

現在のリポジトリで最新のタグを取得します。タグが存在しない場合は `0.0.0` とみなします。

```bash
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
```

## Determine Next Version

LATEST_TAG を設定したコミットから最新のコミットまでの変更内容を確認し、次のバージョンを決定します。
この時、差分の内容に基づいて、次のバージョンを `patch`, `minor`, `major` のいずれかに分類します。

- `patch`: バグ修正やドキュメントの変更など、後方互換性のある修正
- `minor`: 新機能の追加や後方互換性のある変更
- `major`: 後方互換性のない変更や大規模なリファクタリング

## Update CHANGELOG.md

新しいバージョン向けに `CHANGELOG.md` を

- [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/)
- [Semantic Versioning](https://semver.org/lang/ja/)

に基づいて更新します。

`## [未リリース]` セクションの内容を新しいバージョンセクションに移動し、適切な日付を追加します。 → `## [X.Y.Z] - YYYY-MM-DD`

リストのスタイルは統一的に記述し、セクションが空であればそのセクションは記述不要です。

### Notes

- PR や Issue の番号は `(#123)` のように括弧付きで記載します。
- リスト項目は簡潔かつ統一的な表現で記載してください。
- `## [未リリース]` セクションと新しいバージョンの比較リンクを追加・更新します。
- 既存の履歴エントリは削除しないでください。

## Stage & Commit Changes

新しいバージョンを決定したら、変更をコミットしてタグを作成します：

```bash
# NEXT_VERSION を決定した後に実行（例：NEXT_VERSION="1.2.3"）
echo "Please specify the next version (e.g., 1.2.3):"
read -p "Next version: " NEXT_VERSION

if [ -z "$NEXT_VERSION" ]; then
  echo "Error: Version cannot be empty"
  exit 1
fi

echo "Staging CHANGELOG.md..."
git add CHANGELOG.md

echo "Creating commit..."
git commit -m "chore(release): v$NEXT_VERSION"

echo "Creating tag..."
git tag "v$NEXT_VERSION"

echo "Version v$NEXT_VERSION has been prepared for release."
```

## Push branch and Tags

変更とタグをリモートにプッシュします：

```bash
echo "Pushing changes to remote..."
git push

echo "Pushing tags to remote..."
git push --tags

echo "Release v$NEXT_VERSION has been published successfully!"
```

Insert a short release note (from the new section) into the command output.
