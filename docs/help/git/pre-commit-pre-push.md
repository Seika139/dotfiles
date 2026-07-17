# pre-commit と pre-push

Git には commit や push などのライフサイクルイベントに合わせて任意のスクリプトを実行できる **Git hooks** という仕組みがある。
代表的な `pre-commit` / `pre-push` を使うと、不用意なコミットや push を機械的に防げるため、ローカルでのうっかりミスをチームに流出させない最後の砦になる。

## Git hooks とは

- リポジトリの `.git/hooks/` ディレクトリに置かれた **実行可能ファイル** が、対応するイベントで自動的に起動される。
- 初期状態では `pre-commit.sample` のように `.sample` 拡張子のテンプレートが置かれているだけで、有効化するには **`.sample` を外して実行権限 (`chmod +x`) を付与する** 必要がある。
- スクリプトの言語は問わない。シェバン (`#!/bin/bash`, `#!/usr/bin/env python3` など) を書けば何でも使える。
- 終了コード `0` で成功扱い、`0 以外` で失敗扱いとなり、失敗時は対応する Git 操作（commit や push）がキャンセルされる。

### 主な hook の種類

|         Hook         |            起動タイミング             |         典型用途         |
| :------------------: | :-----------------------------------: | :----------------------: |
|     `pre-commit`     | `git commit` で commit が作られる直前 | lint / format / 機密検査 |
| `prepare-commit-msg` |      コミットメッセージ生成直後       |     テンプレート挿入     |
|     `commit-msg`     |  メッセージ確定後 / commit 作成直前   |  メッセージ規約チェック  |
|      `pre-push`      |    `git push` でリモートに送る直前    | テスト実行 / push 先制限 |
|    `post-commit`     |            commit 作成直後            |  通知 / メトリクス送信   |

参考: <https://git-scm.com/docs/githooks>

## pre-commit と pre-push の違い

| 観点           | pre-commit               | pre-push                                               |
| :------------- | :----------------------- | :----------------------------------------------------- |
| 起動タイミング | `git commit` 実行時      | `git push` 実行時                                      |
| 標準入力       | なし                     | 1 行ごとに `local_ref local_sha remote_ref remote_sha` |
| 想定処理時間   | 軽い (秒単位)            | 重くても可 (テスト・ビルドなど)                        |
| スキップ方法   | `git commit --no-verify` | `git push --no-verify`                                 |

「軽い静的チェックは pre-commit、重いテストは pre-push」と棲み分けるのが定石。コミットのたびにフルテストを走らせると開発体験が悪化するため、ここのバランスは重要。

## 使用例

### pre-push: このマシンからの push をすべて禁止する

検証用 PC や踏み台サーバなど、誤って push してほしくないマシンに置いておくと安心。

```bash
#!/bin/bash

# pre-push は標準入力から 1 行ごとに 4 値を受け取る
while read local_ref local_sha remote_ref remote_sha; do
    # リモートの参照からブランチ名を抽出
    branch_name="${remote_ref#refs/heads/}"

    echo "[ERROR] このマシンからはあらゆる push を禁止しています。 Current branch: $branch_name"
    exit 1 # 1 を返すと push がキャンセルされる
done

exit 0
```

> **補足**: push 対象が複数 ref ある場合 (例: `git push --all`) は `while` が複数回回る。`exit 1` した時点で push 全体が中止される。

### pre-commit: 特定ブランチへの直接コミットを禁止

`main` や `master` へ手元から直接コミットしてしまうのを防ぐ。

```bash
#!/bin/sh

# 禁止したいブランチ名を指定（複数ある場合は "main|master" のように指定）
FORBIDDEN_BRANCH="main"

# 現在のブランチ名を取得
CURRENT_BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)

if [ "$CURRENT_BRANCH" = "$FORBIDDEN_BRANCH" ]; then
    echo "Error: $FORBIDDEN_BRANCH ブランチへの直接コミットは禁止されています！" >&2
    echo "ブランチを切ってから作業してください。" >&2
    exit 1
fi

exit 0
```

複数ブランチを禁止したい場合は `case` で書くと読みやすい。

```bash
case "$CURRENT_BRANCH" in
    main|master|release/*)
        echo "Error: $CURRENT_BRANCH への直接コミットは禁止されています" >&2
        exit 1
        ;;
esac
```

### pre-commit: lint / format を staged ファイルにだけ実行する

CI と同じチェックを手元でも回しておくと、レビューの差し戻しが減る。
`git diff --cached --name-only --diff-filter=ACM` で **追加・変更されたファイル** のみを対象にできる点がポイント。

```bash
#!/bin/bash
set -euo pipefail

# Python: ruff で lint と format を確認
mapfile -t py_files < <(git diff --cached --name-only --diff-filter=ACM -- '*.py')
if [ ${#py_files[@]} -gt 0 ]; then
    ruff check "${py_files[@]}"
    ruff format --check "${py_files[@]}"
fi

# Shell: shfmt でフォーマット差分を確認
mapfile -t sh_files < <(git diff --cached --name-only --diff-filter=ACM -- '*.sh')
if [ ${#sh_files[@]} -gt 0 ]; then
    shfmt -d "${sh_files[@]}"
fi
```

### pre-push: テストを実行する

push 前にテストを走らせて、CI で落ちる前に気付けるようにする。

```bash
#!/bin/bash
set -euo pipefail

echo "[pre-push] running tests..."
# プロジェクトに合わせて差し替える
uv run pytest -q
```

### pre-commit: 機密情報の混入を防ぐ

API キーや秘密鍵のような文字列が staged にいないかを簡易チェック。

```bash
#!/bin/bash

if git diff --cached -U0 | grep -E '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA|OPENSSH) PRIVATE KEY-----)'; then
    echo "Error: 機密情報らしき文字列が含まれています" >&2
    exit 1
fi
```

> 本格運用したいなら [gitleaks](https://github.com/gitleaks/gitleaks) や [detect-secrets](https://github.com/Yelp/detect-secrets) のような専用ツールを `pre-commit` framework から呼ぶ方が確実。

## チームで hooks を共有する

`.git/hooks/` は **Git の追跡対象外** なので、放っておくと「あの人だけ動いてる」状態になる。共有する方法はいくつかある。

### 1. リポジトリ内ディレクトリを `core.hooksPath` で指す

最もシンプルな手段。リポジトリに `.githooks/` を切ってスクリプトをコミットし、各開発者に一度だけ次のコマンドを実行してもらう。

```bash
git config --local core.hooksPath .githooks
```

`mise` や `direnv` の post-install で自動設定する仕組みを入れておくと、セットアップ漏れを防げる。

### 2. pre-commit framework を使う

<https://pre-commit.com/> は **多言語向けに最適化された hooks ランナー** で、`.pre-commit-config.yaml` に使いたいフックを列挙するだけで導入できる。Python プロジェクトなら `uv tool install pre-commit` などで入れて `pre-commit install` を 1 回叩けば良い。

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
      - id: ruff-format
```

### 3. JavaScript プロジェクトなら husky / lefthook

`package.json` ベースのプロジェクトでは [husky](https://typicode.github.io/husky/) や [lefthook](https://github.com/evilmartian/lefthook) が一般的。`npm install` 時の `prepare` スクリプトで自動セットアップできるため共有が楽。

### 4. git-secrets で禁止文字列を検出する(パターンを追跡外に置く個人用途)

プロジェクト固有の禁止文字列(社内ドメインなど)を正規表現で検出したいが、パターン自体が機密情報なので `.pre-commit-config.yaml` のようにリポジトリへコミットしたくない、というケースがある。そうした個人用途には [git-secrets](https://github.com/awslabs/git-secrets) が向いている。

導入は次の 3 層に分離して考えるとよい。

1. バイナリ導入: `mise` で `git-secrets` コマンド自体をインストールする(Mac / Linux で同一手順)。
2. フック配布: `git config --global init.templatedir` を設定した上で `git secrets --install` をテンプレートディレクトリに対して実行する。これで今後 `git init` / `git clone` するすべてのリポジトリに pre-commit フックが自動でコピーされる(全体 default)。
3. パターン定義: 検出したい正規表現は追跡対象外の `~/.gitconfig.local` の `[secrets]` セクションに書く。`.gitconfig` が `[include] path = ~/.gitconfig.local` で読み込むため、機能はグローバルに効くがパターンの中身は git 追跡に載らない。

パターンの登録例:

```bash
git config --file ~/.gitconfig.local --add secrets.patterns '内緒の正規表現'
```

全体(テンプレートディレクトリ経由)で有効にする一方、既存のリポジトリにはテンプレートが遡及しないため、後付けしたい場合はそのリポジトリで個別に `git secrets --install` を実行する。逆に特定リポジトリだけ除外したい場合は、そのリポジトリの `.git/hooks/` から git-secrets が設置したフックを削除すればよい。ここでも `git commit --no-verify` でスキップ可能なので、後述の「hooks をスキップしたいとき」の通り CI 側で同等のチェックを掛けておくのが定石。

`core.hooksPath` 方式(前述の「1. リポジトリ内ディレクトリを `core.hooksPath` で指す」)はフックスクリプトごとリポジトリにコミットして全員で共有する用途に向いている一方、パターンを追跡外にしたい個人用途では templatedir + `.gitconfig.local` の組み合わせの方が向いている。

## hooks をスキップしたいとき

緊急時など、どうしても hook を止めたい場合は `--no-verify` を付ける。

```bash
git commit --no-verify -m "WIP"
git push --no-verify
```

ただし日常的に使うと hooks の意味が無くなるので、**「なぜスキップしたか」を commit message や PR に必ず残す** こと。CI 側で同等のチェックを掛けておくと、ローカルスキップしても最終的に検知できる。

## デバッグの Tips

- 一時的に `set -x` を入れると実行内容が分かる。
- `exit 1` ではなく `exit 2` を返しても扱いは「失敗」になるが、終了コードを見れば原因切り分けに使える。
- hook 自体に実行権限が無いと **何も実行されずに成功扱い** になるので、動かないと感じたら `ls -l .git/hooks/` で `x` ビットを確認する。
- `GIT_TRACE=1 git commit` で Git 内部のトレースが見え、どの hook が呼ばれたか分かる。

## 参考

- <https://git-scm.com/docs/githooks>
- <https://git-scm.com/book/ja/v2/Git-のカスタマイズ-Git-フック>
- <https://pre-commit.com/>
