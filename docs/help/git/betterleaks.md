# betterleaks

[betterleaks](https://github.com/betterleaks/betterleaks) は、ファイルや git 履歴の中からシークレット(API キー、パスワード、秘密鍵など)を探すスキャナである。
Gitleaks の作者らが開発していて、Go 製の単一バイナリとして動く。
キーワードで絞り込んでから正規表現で検出し、エントロピーなどのフィルタで誤検知を落とす流れで動く。
標準の設定には約 470 個のルールが入っている。

## git secrets との使い分け

[git-secrets](git-secrets.md) は commit 時に「自分で登録した禁止パターン」を検査する。
betterleaks は、あらかじめ用意された多数のルールで、既存の履歴を含めて検査する用途に向く。
両者は補い合う関係である。

## v1 と v2

2026年11月時点では v2 はリリース候補(RC)で、安定版は出ていない。
そのため brew や mise でインストールすると v1 系が入る。

v1 と v2 は設定とコマンドの互換性がない。
v1とv2で書き換える点の一覧と、v2 のコマンドと設定は [betterleaks (v2)](betterleaks-v2.md) にまとめている。

v1 では、標準の設定を引き継ぐ(`extend`)と、子の設定のグローバルな `filter` / `prefilter` が反映されないので、v1 で除外を書くときは `[[allowlists]]` を使う。

## インストール確認

```bash
command -v betterleaks
betterleaks version
```

## 基本の使い方

v1.10 で確認したコマンドを元に書いている。v2 は [betterleaks (v2)](betterleaks-v2.md) を参照する。

対象ごとにコマンドを使い分ける。

| 検査したいもの       | コマンド                                   |
| :------------------- | :----------------------------------------- |
| git の履歴           | `betterleaks git [リポジトリ]`             |
| 今のファイル         | `betterleaks dir <パス>`                   |
| 標準入力             | `betterleaks stdin`                        |
| GitHub / GitLab / S3 | `betterleaks github <URL>`、`gitlab`、`s3` |

```bash
cd <リポジトリ>

# 履歴全体を検査する
betterleaks git . --redact -v

# コミットの範囲を絞る (git log のオプションをそのまま渡す)
betterleaks git . --log-opts="origin/main~10..origin/main" --redact -v

# staged の変更だけを検査する (pre-commit 向け)
betterleaks git . --staged --redact -v

# 今のファイルを検査する
betterleaks dir . --redact -v
```

検出があると終了コード 1 で終わる。 `--exit-code 0` を付けると、検出があっても 0 で終わる(警告のみの運用に使う)。

## よく使うオプション

| オプション                                       | 意味                                                  |
| :----------------------------------------------- | :---------------------------------------------------- |
| `--redact`                                       | 検出した値を隠す。**必ず付ける**                      |
| `-v` / `--verbose`                               | 検出内容を画面に出す。付けないと件数の表示だけになる  |
| `--log-opts`                                     | `git log` に渡すオプション。範囲指定は `A..B` と書く  |
| `-c` / `--config`                                | 設定ファイルを指定する                                |
| `-r` / `--report-path`、`-f` / `--report-format` | 結果をファイルに出す(`json`、`csv`、`junit`、`sarif`) |
| `--match-context 3L`                             | 検出箇所の前後 3 行も表示する                         |
| `--confidence high`                              | 確度の低い検出を除外する                              |
| `--isolate-rule <ID>`                            | 指定したルールだけで検査する                          |
| `--disable-rule <ID>`                            | 指定したルールを外す                                  |
| `-b` / `--baseline-path`                         | 既知の検出を無視するためのベースライン                |
| `--max-target-megabytes`                         | 大きいファイルをスキップする                          |
| `--no-banner`、`--no-color`                      | CI のログを読みやすくする                             |

`-v` は、v1 では「詳細表示」で、検証ではない。
検出したキーが有効かを提供元に問い合わせる検証は `--validation` で、付けなければ行われない。
外部への問い合わせが発生するので、通常は付けない。

## 検出の表示から原本をたどる

検出には、場所を特定する情報が含まれる。
`--redact` を付けても、値だけが隠れて、場所は隠れない。

| 項目                         | 意味                                            |
| :--------------------------- | :---------------------------------------------- |
| `File`(画面では `path`)      | ファイル                                        |
| `StartLine`                  | 行                                              |
| `Commit`(画面では `git.sha`) | その値が入ったコミット                          |
| `Author` / `Date`            | 入れた人と日時                                  |
| `Fingerprint`                | `<コミット>:<ファイル>:<ルール>:<行>` の形の ID |

原本は、コミットを指定して git で見る。

```bash
# コミットの差分
git show <コミット> -- <ファイル>

# そのコミットの時点のファイルの行 (値が出るので、先頭だけ見る)
git show <コミット>:<ファイル> | sed -n 55p | cut -c1-40

# ファイルの経緯 (入れたコミットと消したコミットが分かる)
git log --format='%h %ad %an %s' --date=short -- <ファイル>
```

値を消したあとでも、履歴にはその値が残っている。
今のファイルに該当行がなくても、履歴から消えたことにはならない。
検出した値を調べる端末の画面は、共有しない。

## 設定ファイル

設定ファイルは `-c` で明示する。
カレントの `.betterleaks.toml` を自動で読ませるには `--unsafe-auto-load-config` が要るが、信頼できない対象には使わない。

標準の設定を引き継いで、除外だけを足す。

```toml
title = "my betterleaks config"

[extend]
useDefault = true

# サードパーティのコードは検査しない
[[allowlists]]
description = "vendor 配下"
paths = ['''^vendor/''']

# テストのダミー値だけを除外する (ルール + 場所 + 値の形で狭く書く)
[[allowlists]]
description = "テストのダミー UUID"
condition = "AND"
targetRules = ["generic-api-key"]
paths = ['''^tests/''']
regexTarget = "line"
regexes = ['''(?i)device_?token\w*\W+[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}''']
```

| 項目                     | 意味                                                                                                            |
| :----------------------- | :-------------------------------------------------------------------------------------------------------------- |
| `targetRules`            | 除外を適用するルールの ID                                                                                       |
| `paths`                  | 対象のパス(正規表現)                                                                                            |
| `regexes`、`regexTarget` | 値や行に対する条件。`regexTarget` は `line` などを指定する                                                      |
| `condition`              | `AND` にすると、`paths` と `regexes` の両方に合うときだけ除外する。省略すると `OR` で、どちらかに合えば除外する |

設定は検査の前に検証できる。

```bash
betterleaks config check -c .betterleaks.toml   # 構文とルールの検証
betterleaks config show -c .betterleaks.toml    # 解決後の設定を表示
betterleaks config path                         # 使われる設定の場所
```

### 除外の方針

- ルールと場所、必要なら値の形まで指定して、狭く書く。テストのディレクトリ全体を除外しない(テスト用の秘密鍵など、見逃したくないものが紛れる)。
- 除外を足す前に、検出された行の中身を確認して、ダミーであることを確かめる。理由を `description` に書く。
- ファイル名を指定した除外は、そのファイルに後から本物の値を書いても効いてしまう。範囲を広げすぎない。
- 除外を足したら、同じ範囲でもう一度検査して、検出が消えたことと、別の場所の同じ形の値が検出されたままであることの両方を確認する。

### 行末のコメントで許可する

その行だけを許可するには、行末に `betterleaks:allow`(または `gitleaks:allow`)を書く。
文字列として一致するかだけを見るので、コメントの書き方は問わない。

## 試し方の注意

最初から履歴全体を検査しない。
`--log-opts` で直近の数コミットに絞って、出力の傾向を見てから、範囲を広げる。
範囲を広げると、初回の取り込みコミットなどに、誤検知が大量に出る。

古い履歴の検出は、すでに失効や更新が済んでいることも多い。
本物の可能性がある検出は、値が有効かを調べる前に、入れた人と担当者に確認する。
有効だったときは、鍵を失効させて新しい鍵に差し替えるのを先にやる。
履歴からの削除は、その後でよい(失効した鍵は、履歴に残っていても使えない)。

## CI に入れるときの考え方

PR ごとに、追加されたコミットだけを検査するジョブにする。
次のコマンドは v1 の書き方である(v2 の書き方は [betterleaks (v2)](betterleaks-v2.md) の「CI」を参照)。

```bash
betterleaks git . --log-opts="origin/<ベース>..HEAD" -c .betterleaks.toml --redact
```

- 履歴の範囲を正しく取るために、checkout は `fetch-depth: 0` にする。
- ログは閲覧者に見えるので、`--redact` を必ず付ける。
- 検出があるとジョブが失敗する。必須にしない限り、マージは止まらない。
- 誤検知を整理するまでは、`--exit-code 0` で警告のみにする。
- バイナリは、バージョンと SHA-256 を固定して、releases から取得する。ランナーから取得元に届くかは、実機で確認する。

**参考**

- <https://github.com/betterleaks/betterleaks>
- [betterleaks (v2)](betterleaks-v2.md)
- [git-secrets](git-secrets.md)
