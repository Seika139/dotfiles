# git-secrets

[git-secrets](https://github.com/awslabs/git-secrets) は AWS Labs 製のツールで、正規表現ベースのパターンに対して commit 内容をスキャンし、禁止文字列(機密情報)の混入を検出する。

## このリポジトリでの位置づけ

このリポジトリでは次の 3 層で導入している。

1. `mise` で `git-secrets` コマンド自体をインストールする。
2. `git config --global init.templatedir` を設定した上でテンプレートディレクトリに `git secrets --install` 済みのフックを配置し、今後 `git init` / `git clone` するすべてのリポジトリに pre-commit フックを自動配布する(全体 default)。
3. 検出したい正規表現は追跡対象外の `~/.gitconfig.local` の `[secrets]` セクションに書く。

3 層設計の詳細な理由や `core.hooksPath` 方式との比較は [pre-commit / pre-push](pre-commit-pre-push.md) に譲る。
このページでは git-secrets というツール自体の操作コマンドをチートシートとしてまとめる。

## インストール確認

```bash
command -v git-secrets
git secrets --version  # なければ `mise install` 後に再確認
```

## パターンの登録・確認・削除

```bash
git secrets --add '<regex>'  # デフォルトはlocalリポジトリ設定。-g/--globalをつければglobal
```

このリポジトリの推奨運用は、追跡外の `~/.gitconfig.local` に直接パターンを追記する方法である(パターン自体を git 追跡に載せない運用に合致するため)。

```bash
git config --file ~/.gitconfig.local --add secrets.patterns '<regex>'
```

登録済みのパターンを確認する。

```bash
git secrets --list     # 現在有効なパターン一覧
git secrets --list -g  # global設定のみ
```

パターンの削除には専用サブコマンドが無い。
`~/.gitconfig.local` を直接編集するか、次のように `--unset` で該当パターンを削除する。

```bash
git config --file ~/.gitconfig.local --unset secrets.patterns '<regex>'
```

## フックの導入・確認

```bash
git secrets --install [-f] [<path>]
```

現在のリポジトリまたは指定した path にフックを設置する。
`-f` を付けると既存フックを強制的に再生成できる(冪等に実行できる)。

既存リポジトリに後付けしたい場合は path を省略して実行する。
カレントの `.git/hooks/` にフックが設置される(templatedir は既存リポジトリには遡及しないため)。

フックが設置されているかは次のコマンドで確認できる。

```bash
ls -la .git/hooks/
```

## AWSキー検出のデフォルトルール

```bash
git secrets --register-aws
```

AWS アクセスキーなどの定番パターンを一括登録できる。
このリポジトリの用途(プロジェクト固有の禁止文字列の検出)とは別軸のオプション機能として、必要な場合に利用する。

## 手動スキャン

```bash
git secrets --scan          # ワーキングツリー/指定ファイルをスキャン
git secrets --scan-history  # リポジトリの全履歴をスキャン
```

`--scan-history` は過去のコミットに紛れ込んだ機密の発見に有用。

## 動作確認の実践例

一時ディレクトリで git-secrets の動作を確認する一連の流れ。

- `mkdir -p /tmp/git-secrets-check && cd /tmp/git-secrets-check && git init` でテスト用リポジトリを作る。
- `git secrets --install -f` でこのリポジトリにフックを設置する(templatedir 経由であれば既に入っているはずだが、確認のために明示的に実行する)。
- `git config --file ~/.gitconfig.local --add secrets.patterns 'SECRET_TOKEN_[0-9]+'` のようなテスト用パターンを一時的に登録する。
- `echo 'SECRET_TOKEN_12345' > secret.txt` でパターンに一致するファイルを作成する。
- `git add secret.txt` と `git commit -m 'test'` を実行し、pre-commit フックにコミットが弾かれることを確認する。
- 確認できたら `git config --file ~/.gitconfig.local --unset secrets.patterns 'SECRET_TOKEN_[0-9]+'` でテスト用パターンを削除し、一時リポジトリも削除して後始末する。

## トラブルシュート

フックが動かないと感じたら、次を確認する。

- `.git/hooks/pre-commit` に実行権限(`x` ビット)が付いているか。`ls -la .git/hooks/` で確認する。
- 対象リポジトリがテンプレートディレクトリ設定より後に作成されたものか。既存リポジトリには templatedir の内容は遡及しないため、後付けの場合は `git secrets --install` を個別に実行する必要がある。
- `git commit --no-verify` や `git push --no-verify` で意図的にフックをスキップしていないか。

**参考**

- <https://github.com/awslabs/git-secrets>
- [pre-commit / pre-push](pre-commit-pre-push.md)
