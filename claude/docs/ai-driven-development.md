# AI-Driven Development Loop

LLM を活用してソフトウェア開発の全ライフサイクルを自動化・高速化するための包括的な設計。
Claude Code に限らず、複数の LLM をコスト・パフォーマンスの両軸で使い分ける。

## 基本原則

```plain
人間の仕事: 判断する（承認・却下・方向転換）
AI の仕事: それ以外の全て（調査・設計・実装・テスト・レポート）
```

人間がブロッカーになる瞬間を最小化し、AI の稼働時間を最大化する。

## インフラ基盤

### GitHub Issues / Projects をタスクキューとして使う

新しいキューシステムは作らない。人間が普段使う Projects がそのまま自動化の入口になる。

#### Projects のステータスフロー

```plain
Backlog → Ready → In progress → Waiting → Done
                                    ↑
                                人間レビュー待ち
                                （唯一の必須ブロッキングポイント）
```

| Status      | 意味             | 遷移トリガー                                       |
| :---------- | :--------------- | :------------------------------------------------- |
| Backlog     | 未整理           | 人間が Issue を追加 / AI が `/discover` で自動起票 |
| Ready       | 実行可能         | 人間が Priority / Size を設定して移動              |
| In progress | AI が実装中      | Dispatcher が Worker を起動                        |
| Waiting     | 人間レビュー待ち | Worker が PR を作成                                |
| Done        | 完了             | 人間が PR をマージ                                 |

#### 必要なフィールド

| フィールド          | 用途                       |
| :------------------ | :------------------------- |
| Status              | タスクキューの状態管理     |
| Priority (P0/P1/P2) | 実行順序の決定             |
| Size (XS/S/M/L/XL)  | モデル選択・自動実行の閾値 |

### GitHub Actions での実行

Private リポジトリでも GitHub Actions は利用可能。

| プラン      | 月間無料枠 | 備考                     |
| :---------- | :--------- | :----------------------- |
| Free (個人) | 2,000分    | Linux ランナーは 1x 消費 |
| Pro         | 3,000分    |                          |
| Team        | 3,000分    |                          |
| Enterprise  | 50,000分   |                          |

Self-hosted Runner を使えば分数を消費しない。

## 開発ライフサイクル

```plain
① 企画・設計 → ② Issue 細分化 → ③ 実装（並列）
     ↓                                    ↓
⑧ 監視・発見 ←── ⑦ マージ・デプロイ ←── ④ プレビュー
                        ↑                  ↓
                   ⑥ 修正 ←────── ⑤ 人間レビュー
```

### ① 企画・設計

**人間の入力**: 方向性のみ（1行〜数行）

```plain
人間: 「こういうの作りたい」
  ↓
AI (高性能モデル):
  - 既存コードベースを分析
  - 設計ドキュメントの叩き台を生成
  - 要判断事項を明示（不明点は仮置きで進める）
  ↓
人間: 承認 or 修正指示
```

対応コマンド: `/scaffold`, `/discover`

- `/scaffold` —「作りたいもの」から設計 + Issue セットを生成
- `/discover` —「改善したいこと」からコード分析 + Issue 草案を生成

どちらも人間は「選ぶだけ」。詳細な言語化は AI が代行する。

### ② Issue 細分化

**人間の入力**: 承認のみ

```plain
AI:
  - 設計を依存関係付き Issue に分解
  - Priority / Size を自動設定
  - Projects ボードに追加（Status: Ready）
  ↓
人間: 一覧を確認して一括承認
```

Issue の粒度は「1 Issue = 1 PR」を基本とする。

### ③ 実装（並列）

**人間の入力**: なし

Dispatcher + Worker アーキテクチャで並列実行。

```plain
Dispatcher (cron: 15分ごと)
  │
  ├─ Projects から Ready の Issue を取得
  ├─ Priority × Size 順にソート
  ├─ 依存関係を考慮してフィルタ
  └─ Worker を並列起動（最大 N 件）

Worker (Issue 1件を処理)
  │
  ├─ Status → In progress に更新
  ├─ 対象リポジトリを checkout
  ├─ ブランチ作成 → 実装 → テスト → PR 作成
  ├─ Status → Waiting に更新
  └─ Slack で通知
```

並列実行の制約:

- 同じファイルを触る Issue は直列実行（コンフリクト防止）
- 異なるリポジトリの Issue は常に並列可能
- GitHub Actions の concurrency group で同時実行数を制御

### ④ プレビュー

**人間の入力**: なし

```plain
PR 作成
  ↓
CI/CD で自動プレビューデプロイ
  ↓
AI セルフレビュー:
  - 別モデルでクロスレビュー
  - レビュー結果を PR にコメント
  - 問題があれば自動修正して再 push
```

### ⑤ 人間レビュー

**人間の入力**: 最小（承認 or 1行コメント）

唯一の必須ブロッキングポイント。最小化の工夫:

- **バッチレビュー**: 溜まった PR を AI がサマリー → 人間はまとめて確認
- **Slack ボタン**: `[承認] [修正依頼] [却下]` のボタン1つで反応
- **修正依頼**: 1行コメントで AI が自動修正

```plain
Slack 通知:
  「PR #42 がレビュー待ちです。AI サマリー: ○○を修正、テスト追加済み」
  [承認] [修正依頼] [却下]
```

### ⑥ 修正

**人間の入力**: なし

```plain
PR コメント / レビューコメント
  ↓
AI が自動検知 → 修正を実装 → 再 push
  ↓
Status → Waiting に戻る
```

### ⑦ マージ・デプロイ

**人間の入力**: Approve のみ

```plain
人間: PR を Approve
  ↓
auto-merge → CI/CD で本番デプロイ
  ↓
Status → Done に自動更新
```

### ⑧ 監視・発見

**人間の入力**: なし（定期トリアージのみ）

```plain
AI (定期実行):
  - エラーログ分析
  - パフォーマンス監視
  - 依存パッケージの脆弱性チェック
  ↓
問題検知時: Issue を自動起票（Status: Backlog）
  ↓
人間: 次の定期レビューで Backlog を Ready に移動
```

## マルチ LLM 戦略

### モデルの使い分け

Issue の Size / 複雑度に応じて最適なモデルにルーティングする。

| タスクの性質           | Size  | モデル候補          | 理由         |
| :--------------------- | :---- | :------------------ | :----------- |
| 設計判断・複雑な実装   | L, XL | Opus, GPT-4o        | 正確性重視   |
| 一般的な実装・バグ修正 | M     | Sonnet, GPT-4o-mini | バランス     |
| 定型作業・フォーマット | XS, S | Haiku, GPT-4o-mini  | コスト重視   |
| コードレビュー         | —     | 実装とは別モデル    | 多角的な視点 |

### ルーティングの実装

```bash
# Worker 起動時にモデルを選択
case "$SIZE" in
  XS|S) MODEL="haiku" ;;
  M)    MODEL="sonnet" ;;
  L|XL) MODEL="opus" ;;
esac
```

### クロスレビュー

Claude が書いたコードを別のモデル（GPT-4o 等）にレビューさせる。
単一モデルでは見逃すパターンを検出でき、コストは実装の数%で品質向上効果が大きい。

## 安全装置（ガードレール）

| ガードレール          | 実装                                        |
| :-------------------- | :------------------------------------------ |
| 1日の最大実行回数     | Dispatcher でカウント                       |
| 1日の最大コスト       | `--max-budget-usd` の合計上限               |
| 同時実行数の上限      | concurrency group                           |
| 自動実行対象の制限    | Size が XS/S のみ自動。M 以上は人間トリガー |
| PR マージは人間が行う | auto-merge は Approve 後のみ                |
| deny リスト           | 破壊的コマンドの実行を禁止                  |

## 人間のブロッキング最小化

| ブロッキングポイント | 頻度 | 最小化の手段                                |
| :------------------- | :--- | :------------------------------------------ |
| 企画・設計の承認     | 低   | AI が叩き台 → 選択式                        |
| Issue の確認         | 低   | 一括承認                                    |
| PR レビュー          | 中   | バッチレビュー + AI サマリー + Slack ボタン |
| 修正指示             | 低   | 1行コメント → AI 自動修正                   |
| マージ承認           | 低   | auto-merge                                  |
| Backlog トリアージ   | 低   | AI がレコメンド                             |

### 効果の高い施策 TOP 3

1. **バッチレビュー + AI サマリー** — 溜まった PR の要点を AI が要約。1件3分 → 30秒に短縮
2. **PR コメント → 自動修正ループ** — 人間は「ここが違う」と1行書くだけ。修正〜再レビュー依頼まで自動
3. **Dispatcher の依存関係解決** — 並列実行可能な Issue を自動判定。人間が実行順序を考える必要なし

## KPI

| 指標                       | 意味               | 改善方向                 |
| :------------------------- | :----------------- | :----------------------- |
| Waiting → Done の平均時間  | 人間レビューの速度 | 短いほど良い             |
| Ready → Waiting の平均時間 | AI の実装速度      | モデル/プロンプト最適化  |
| 1日あたりの完了 Issue 数   | スループット       | 並列数を増やす           |
| Issue あたりのコスト       | 費用対効果         | モデルルーティング最適化 |

## 関連ドキュメント

- [continuous-operation.md](./continuous-operation.md) — Claude Code 単体の稼働最適化
- [discover-and-scaffold.md](./discover-and-scaffold.md) — 探索型コマンド `/discover`, `/scaffold`
- [ai-driven-dev-resources.md](./ai-driven-dev-resources.md) — 必要リソース一覧・チェックリスト

---

```bash
KOFILE=$(find /lib/modules/$(uname -r) -name 'algif_aead.ko*' 2>/dev/null | head -1)
echo "Target file: $KOFILE"
sudo mv "$KOFILE" "${KOFILE}.disabled-cve-2026-31431"; ls -la "${KOFILE}.disabled-cve-2026-31431"
sudo depmod -a

sudo modprobe algif_aead 2>&1

python3 -c "import socket;s=socket.socket(socket.AF_ALG,socket.SOCK_SEQPACKET,0);s.bind(('aead','gcm(aes)'));print('NG: still vulnerable')" 2>&1
```
