# betterleaks (v2)

[betterleaks](https://github.com/betterleaks/betterleaks) の v2 のコマンドと設定の書き方である。
betterleaks というツール自体の説明と、v1.10.1 の使い方は [betterleaks](betterleaks.md) にまとめている。

2026-11-24 時点の v2.0.0-rc.11 の公式ドキュメント(`docs/v2_migration.md`、`docs/scanning.md`、`docs/config.md`)の記述をもとに書いていて、動作は未確認である。
v2 を採用するときは、実際に動かして確認してから使う。

## インストール

v2 の RC は、`brew` や `mise` には出てこない。
バージョンを明示して、`go install` か releases のバイナリで入れる。

```bash
go install github.com/betterleaks/betterleaks/v2@v2.0.0-rc.11
betterleaks version
```

## コマンド

```bash
# 履歴全体を検査する
betterleaks git . --redact

# コミットの範囲を絞る
betterleaks git . --revision=origin/main~10..origin/main --redact

# staged の変更だけを検査する (pre-commit 向け)
set -o pipefail
git diff --cached --no-ext-diff --no-textconv --no-color --src-prefix=a/ --dst-prefix=b/ | betterleaks stdin --git-diff --redact

# 今のファイルを検査する
betterleaks fs . --redact

# 結果をファイルに出す (JSON は {"schema_version", "findings", "scan"} の形)
betterleaks fs . --redact -o findings.json
```

v1 との違いは次のとおり。

- v2 は検出内容を既定で画面に出すので、v1 の `-v`(詳細表示)に当たるオプションは要らない。v2 の `-v` は検証(`--validate`)の意味に変わっている。
- 範囲指定は `--log-opts` ではなく `--revision=A..B` である。`A...B` は使えない。
- マージコミットは既定では検査しない。検査するには `--include=merges` を付ける。
- 検査する対象は `--include` と `--exclude` で足したり引いたりできる(`commit-messages`、`notes`、`reflogs` など)。
- 検証は既定で行わない。`-v` / `--validate` と `-a` / `--analyze` を付けたときだけ、提供元に問い合わせる。
- 検出があると終了コード 1 で終わる点は同じで、`--exit-code` で変えられる。

## 設定ファイル

設定ファイルは `--config` で明示する。
`.betterleaks.toml` は自動では読まれない。
除外は `[[allowlists]]` ではなく、`prefilter` と `filter` の式で書く。
`filter` が `true` を返した検出は、捨てられる。

```toml
title = "my betterleaks config"
minVersion = "2.0.0-rc.1"

[extend]
useDefault = true

# サードパーティのコードは検査しない (ファイルごと検査の対象から外す)
prefilter = '''
matchesAny(attributes["path"], [`^vendor/`])
'''

# テストのダミー UUID だけを除外する (場所 + 値の形 + 行の内容で狭く書く)
filter = '''
matchesAny(attributes["path"], [`^tests/`])
&& matchesAny(finding.secret, [`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$`])
&& matchesAny(finding.line, [`(?i)device_?token`])
'''
```

| v1 の `[[allowlists]]` の項目     | v2 の式                                                                                                                                                                        |
| :-------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `paths`                           | `matchesAny(attributes["path"], [...])`(ファイルごと除外するなら `prefilter`)                                                                                                  |
| `regexes`、`regexTarget = "line"` | `matchesAny(finding.line, [...])`                                                                                                                                              |
| `regexTarget = "secret"`          | `matchesAny(finding.secret, [...])`                                                                                                                                            |
| `condition = "AND"`               | `&&` でつなぐ                                                                                                                                                                  |
| `targetRules`                     | グローバルな `filter` では、ルール ID を使えない。ルールごとに絞るには、そのルールを丸ごと書き写して、ルール内に `filter` を書く(同じ ID のルールは、継承元を丸ごと置き換える) |

設定は検査の前に検証できる。

```bash
betterleaks config check --config .betterleaks.toml
```

## 除外ファイル

v2 の `.betterleaksignore` は、シークレット値の SHA-256 を 1 行に 1 つ並べたファイルである。
v1 の場所ベースの fingerprint とは形式が違い、自動変換はない。

```bash
printf '%s' "$SECRET" | betterleaks fingerprint   # 値は末尾の改行を含めずに渡す
betterleaks fs . --ignore-file .betterleaksignore --redact
```

行末のコメント `betterleaks:allow`(または `gitleaks:allow`)は、v2 でもそのまま使える。

## CI

```bash
betterleaks git . --revision="origin/<ベース>..HEAD" --config .betterleaks.toml --redact
```

checkout は `fetch-depth: 0` にする。
v1 と同様に、ログに値が出ないよう `--redact` を付け、バージョンと SHA-256 を固定して取得する。

## v1 との違い

v2 は v1 と設定とコマンドの互換性がない。
v1 から移行するときは、次の点を書き換える。

| 項目               | v1                                 | v2                                             |
| :----------------- | :--------------------------------- | :--------------------------------------------- |
| コミットの範囲     | `--log-opts="A..B"`                | `--revision=A..B`                              |
| ファイルの検査     | `dir`                              | `filesystem` / `fs`                            |
| 設定の自動読み込み | `--unsafe-auto-load-config` で可能 | しない。`--config` で明示                      |
| 除外               | `[[allowlists]]`                   | 廃止。`prefilter` / `filter` の式で書く        |
| 検証               | `--validation`                     | `-v` / `--validate`(`-v` の意味が変わる)       |
| レポート           | json / csv / junit / sarif         | json / jsonl のみ                              |
| ベースライン       | `-b`                               | 廃止                                           |
| 除外ファイル       | 場所ベースの fingerprint           | シークレット値の SHA-256(`.betterleaksignore`) |
| マージコミット     | 検査する                           | 既定では検査しない                             |
| 履歴の読み方       | `git` コマンドを呼ぶ               | プロセス内で読む                               |

**参考**

- <https://github.com/betterleaks/betterleaks>
- [betterleaks (v1)](betterleaks.md)
