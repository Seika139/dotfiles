# Docker Management

このディレクトリは PC 全体の Docker リソースを体系的に管理するためのツールセットを提供します。
不要なコンテナ、イメージ、ボリューム、ネットワーク、ビルドキャッシュなどを安全に確認・削除できます。

## 🚀 Quick Start

```bash
# 利用可能なタスクを確認
mise tasks

# システム全体の使用状況を確認
mise run system show

# 未使用リソースを一括削除
mise run system prune
```

## 📋 利用可能なタスク

### 🔍 基本リソース管理

| タスク      | 説明             | 主な用途                       |
| ----------- | ---------------- | ------------------------------ |
| `container` | コンテナ管理     | 停止中コンテナの確認・削除     |
| `image`     | イメージ管理     | 未使用イメージの確認・削除     |
| `network`   | ネットワーク管理 | 未使用ネットワークの確認・削除 |
| `volume`    | ボリューム管理   | 未使用ボリュームの確認・削除   |

### ⚙️ 拡張リソース管理

| タスク    | 説明                     | 主な用途                               |
| --------- | ------------------------ | -------------------------------------- |
| `buildx`  | ビルダー・キャッシュ管理 | マルチプラットフォームビルド環境の整理 |
| `context` | コンテキスト管理         | Docker 接続設定の整理                  |

### 🎯 一括管理

| タスク   | 説明             | 主な用途                   |
| -------- | ---------------- | -------------------------- |
| `system` | システム全体管理 | 全リソースの確認・一括削除 |

## 📖 詳細な使い方

### 基本的な流れ

1. **確認** → **削除** の安全なフロー
2. 各タスクは `show` → `show-deletable` → `prune` の順で実行

```bash
# 1. 現在の状況を確認
mise run <task> show-all

# 2. 削除対象を確認
mise run <task> show-deletable

# 3. 実際に削除
mise run <task> prune
```

### 🐳 Container（コンテナ管理）

```bash
# 全コンテナを表示
mise run container show-all

# 削除可能なコンテナ（停止中・異常終了）を表示
mise run container show-deletable

# 停止中コンテナを削除
mise run container prune
```

**実行タイミング:**

- 開発終了時
- ディスク容量が不足した時
- 環境をクリーンにしたい時

### 🖼️ Image（イメージ管理）

```bash
# 全イメージを表示
mise run image show-all

# 削除可能なイメージを表示
mise run image show-deletable

# タグなしイメージのみ削除
mise run image prune

# 未使用イメージを全て削除（注意: 名前付きイメージも含む）
mise run image prune-all
```

**実行タイミング:**

- 定期的なメンテナンス
- ディスク容量逼迫時
- 古いイメージバージョンの整理時

### 🌐 Network（ネットワーク管理）

```bash
# 全ネットワークを表示
mise run network show-all

# 削除可能なネットワーク（未使用カスタムネットワーク）を表示
mise run network show-deletable

# 未使用ネットワークを削除
mise run network prune
```

**実行タイミング:**

- Docker Compose プロジェクト整理時
- ネットワーク競合解決時

### 💾 Volume（ボリューム管理）

```bash
# 全ボリュームを表示
mise run volume show-all

# 削除可能なボリュームを表示（匿名・名前付き別に分類）
mise run volume show-deletable

# 匿名ボリュームのみ削除
mise run volume prune

# 全未使用ボリューム削除（注意: 名前付きボリュームも含む）
mise run volume prune-all
```

**⚠️ 注意:** `prune-all` は重要なデータを含む可能性があるため慎重に実行

**実行タイミング:**

- データベース開発環境リセット時
- ディスク容量大幅削減が必要な時

### 🏗️ Buildx（ビルダー・キャッシュ管理）

```bash
# ビルダーインスタンス一覧
mise run buildx show-builders

# ビルドキャッシュ使用状況
mise run buildx show-cache

# 削除可能なビルダー表示
mise run buildx show-deletable-builders

# カスタムビルダー削除
mise run buildx prune-builders

# ビルドキャッシュ削除（基本）
mise run buildx prune-cache

# ビルドキャッシュ削除（内部キャッシュ含む全て）
mise run buildx prune-cache-all
```

**実行タイミング:**

- マルチプラットフォームビルド後
- ビルドキャッシュが肥大化した時

### 🔧 Context（コンテキスト管理）

```bash
# 全コンテキスト表示
mise run context show

# 削除可能なコンテキスト表示
mise run context show-deletable

# カスタムコンテキスト削除
mise run context prune
```

**実行タイミング:**

- リモート Docker 環境の整理時
- Kubernetes 連携設定の見直し時

### 🎯 System（システム全体管理）

```bash
# システム全体のリソース使用状況表示
mise run system show

# 未使用リソース一括削除（ビルドキャッシュ除く）
mise run system prune
```

**削除対象:**

- 停止中のコンテナ
- 未使用イメージ（全て）
- 未使用ネットワーク
- 未使用ボリューム（全て）

**⚠️ ビルドキャッシュは含まれません** → 別途 `mise run buildx prune-cache` が必要

**実行タイミング:**

- 定期的な大掃除
- 開発環境の完全リセット
- ディスク容量の大幅削減が必要な時

## 💡 推奨メンテナンス手順

### 📅 日常的なメンテナンス

```bash
# 1. 停止中コンテナの削除
mise run container prune

# 2. タグなしイメージの削除
mise run image prune

# 3. ビルドキャッシュの削除
mise run buildx prune-cache
```

### 🗓️ 週次メンテナンス

```bash
# 1. システム全体の状況確認
mise run system show

# 2. 各リソースの削除対象確認
mise run volume show-deletable
mise run image show-deletable

# 3. 必要に応じて削除実行
mise run system prune
```

### 🚨 緊急時（ディスク容量逼迫）

```bash
# 段階的に実行し、都度容量を確認

# Step 1: 安全な削除
mise run system prune

# Step 2: ビルドキャッシュ削除
mise run buildx prune-cache-all

# Step 3: 慎重に判断して実行
mise run volume prune-all  # データ消失リスクあり
mise run image prune-all   # 再ダウンロードが必要
```

## ⚠️ 安全な使い方

### 削除前の確認事項

1. **稼働中サービスがないか確認**

   ```bash
   docker ps
   ```

2. **重要なボリュームデータの確認**

   ```bash
   mise run volume show-deletable
   ```

3. **必要なイメージの確認**

   ```bash
   mise run image show-deletable
   ```

### 復旧が困難な操作

- `mise run volume prune-all` - データベースデータなど
- `mise run image prune-all` - カスタムイメージなど
- `mise run buildx prune-builders` - カスタムビルド環境

## 🔧 Dependencies

以下のツールが必要です：

- **mise** - タスクランナー
- **fzf** - インタラクティブ選択
- **docker** - Docker CLI
- **awk** - テキスト処理（通常プリインストール）

## 📚 参考情報

- [Docker 公式ドキュメント - システムの掃除](https://docs.docker.com/config/pruning/)
- [mise 公式ドキュメント](https://mise.jdx.dev/)
- [fzf の使い方](https://github.com/junegunn/fzf)
