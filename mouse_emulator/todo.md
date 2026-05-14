# TODO

- テンプレート画像と OCR 対象の素材を、実運用したいアプリ画面で取り直し sample_images/ から専用ディレクトリへ切り出す。合わせて profiles/auto_emulator/ 側の template_path や pattern を本番用に更新。
- auto_emulator.md をベースに、チーム内で使う設定テンプレートと check-list（初回キャリブレーション手順、Tesseract のパス確認など）をまとめた運用ノートを用意しておく。
- 期待シナリオを 1〜2 件選び、tests/ 配下に画像ベースの回帰テストケースを追加して「画像差し替え →pytest」で壊れないことを定期確認できるようにする。
- 高頻度で使う操作が固まってきたら、共通アクション（例: long_press, keyboard_input）や追加検出器（カラー領域判定など）の TODO を洗い出し、優先度の高いものから実装計画に上げる。

このあたりを片付けると、現場投入後のトラブルが大幅に減らせます。

## 追加すべき仕様

- [x] 標準出力アクション
- [x] 現在の id や条件を満たした回数などをコンソールに出力するアクションを追加すると、デバッグが楽になる。
- [x] 設定をするサポート機能（キャリブレーションした領域に対してどの辺の位置を指しているかを知る機能）
- [x] ocr で取得した値を条件に利用したい
- [x] キャリブレーションせずに事前に与えた座標を利用したい
  - [x] NSScreen と pynput の座標系の違いを吸収するコードを書く、今のままだと profile に書いた座標がずれている
- [x] action で利用する offset とは何か
- [x] 何かを検知していない場合にとりあえずクリックするような動作をさせたい
- [x] 出力を標準出力以外に吐き出させたい（ログファイルなど）
- [x] 一時停止機能を追加したい
- [x] conditions の解説をもっと詳しくする
- [x] ocr を選択した時に region ではなく、画面全体を見ているような気がする → 自分の region の指定方法が間違っていた
- [ ] starlight/tailwind でドキュメントを作る
- [x] emulator の方が ctrl + p で停止した後再開できない

## プロデュース自走 (W.I.N.G. 自動走破)

`auto_emulator.games.produce` パッケージ。旧 `sample2.yml` の機械的
クリックループから、状態 OCR + 戦略決定 + 画面遷移検証を持つ
`ProduceEngine` 一本に移行する大型タスク。

### 観測・戦略レイヤー

- [x] M1-M16 観測ルールの集約 (`docs/auto_emulator/produce_rules.md`)
- [x] `SEASON_STRATEGY` (シーズン別目標オーディション / ファン目標)
- [x] `choose_dialog_option` (3 択の prompt 文脈判定 / M11, M16)
- [x] `_should_rest` / `_should_reflect` / `_pick_audition` / `_pick_lesson_slot`
- [x] WING オーディション優先 (C4)

### 画面読取 (Reader / Matcher)

- [x] `ProduceStateReader` で 7 状態フィールドを fractional 領域から抽出
- [x] `DigitMatcher` (cv2.matchTemplate + style filter) で装飾フォント数字を判定
- [x] `detect_screen_kind` で右下色 signature ベースの画面種別判定
- [x] HP バー HSV saturation 列射影読取
- [x] OCR フォールバック (`_ocr_int`) — Tesseract 装飾フォント弱点を回避

### 実行・統合 (Engine / CLI)

- [x] `consume_until_home` で中間画面消化 + unknown streak 検出
- [x] `try_dismiss_modal` 想定外モーダル除去 4 候補
- [x] checkmark fallback (E1.3, 旧 `option_check.png` 相当)
- [x] `wait_for_screen` / `read_state_with_retry` (B1) / no_progress 検出 (B2)
- [x] `run_full_produce` の停止理由 enum (complete / max_turns / stuck:*)
- [x] CLI `auto_emulator produce-run` + mise task `produce-auto` (E1.4)
- [x] JSONL ターンログ (`JsonlTurnLogger`) と `RunSummary` (D6)
- [x] 自動命名 `~/.cache/auto-emulator/produce/produce-YYYYMMDD-HHMM.jsonl` (D5)
- [x] `produce-analyze` で既存ログを後追い集計 (D7)

### ツーリング

- [x] `tools/calibrate_produce.py overlay` でリージョン/ポイント重ね描き
- [x] `tools/calibrate_produce.py extract` で digit テンプレ補充を CLI 一発 (T1)
- [x] `tools/calibrate_produce.py dump-regions` で全座標を JSON 出力 (T2)

### テスト

- [x] reader / decision / digit_matcher / engine / dialog / turn_log の各レイヤー単体
- [x] CLI エラーパス + `produce-analyze` 集計テスト
- [x] checkmark fallback の順序検証 (E1.3)

### 残タスク

- [ ] Phase 3: 実機 dry-run (ブラウザ起動 + ファン到達まで 1 周)
- [ ] E1.5: yml の archive 化 (実機 dry-run で完全置換が確認できたら)
- [ ] G1: `item_tab` 座標の実機キャリブ (推定値 (0.050, 0.490))
- [x] G2: `audition_swipe` を「すでに目的カードが見えていればスキップ」する智化
- [x] G3: `LessonOption.preview_fans` の OCR 実装 (M8)
- [ ] G2/G3 の実機 fixture でキャリブ + 非 None ケースの E2E テスト
- [ ] 数字テンプレ "4" を新フィクスチャから補充
- [ ] Phase 5c: スキルパネル内部 (振り返り時のスキル取得 / パッシブ ON)
