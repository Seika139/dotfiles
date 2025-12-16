# docker compose のプロジェクト名ルール

`docker compose` のプロジェクト名はリソース名（コンテナ・ネットワーク・ボリューム）に直結する。複数環境を並行起動するときに衝突や意図しない共有を避けるため、優先順位と挙動を押さえておく。

## 優先順位

1. CLI フラグ: `docker compose -p <project>`
2. 環境変数: `COMPOSE_PROJECT_NAME`
3. compose ファイルの `name:` トップレベルキー
4. 何も指定しない場合: compose ファイルが置かれたディレクトリ名

上位の設定があれば下位は無視される。

## リソース名への影響

- コンテナ: `<project>-<service>-<index>`
- デフォルトネットワーク: `<project>-default`
- 匿名ボリューム: `<project>-<volume>-<hash>`

同じプロジェクト名を使うとこれらを共有し、異なる名前を使うと完全に別リソースになる。

## 典型パターン

### `-p` を明示する運用

```bash
docker compose -p project-name --profile runtime up -d
```

メリット: コマンドだけで名前を固定できる。
デメリット: フラグを付け忘れると別プロジェクトができる。

### `name:` を compose.yml に書く

```yaml
name: spark-patent-search-dev
services:
  db:
    image: postgres
```

メリット: フラグ不要で一貫する。
デメリット: 他リポジトリと同じ `name:` を利用している場合に衝突する。

### `COMPOSE_PROJECT_NAME` を環境変数で固定

```bash
export COMPOSE_PROJECT_NAME=spark-patent-search-dev
docker compose up -d
```

メリット: 複数コマンドに効く。CI で設定しやすい。
デメリット: シェルが変わると消える。

## 実務上の指針

- 並列で複数プロファイル（devcontainer と runtime 等）を「同じ DB を共有」したいなら、同じプロジェクト名にそろえる（`name:` を付ける or 共通の `-p` を使う）。
- 環境ごとに DB やネットワークを分離したいなら、プロジェクト名を分ける（例: `-p spark-patent-search-runtime` と `-p spark-patent-search-devcontainer`）。
- 運用を揃えたいなら `name:` を書いたうえで、`mise` / `make` タスクは `-p` を外すか、逆にタスクで `-p` を必ず付けるよう統一する。混在すると意図せず別プロジェクトができるので注意。

## チェック用コマンド

```bash
# 現在動作中のプロジェクトと構成ファイル
docker compose ls

# 特定プロジェクトのコンテナ一覧
docker ps --filter label=com.docker.compose.project=<project>
```
