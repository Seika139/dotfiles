# Pause トグル問題のトラブルシューティング

`auto_emulator` / `mouse_emulator` 共通で利用している `TerminationMonitor`（`src/auto_emulator/runtime/termination.py`）の一時停止トグルに関する既知の挙動と対処をまとめます。デフォルトの `ctrl+p` で再開できなくなる場合に参考にしてください。

## 想定する症状

- `ctrl+p` で一時停止したあと、同じ組み合わせを押しても再開しない。
- `auto-run` よりも `emulate` 実行時に再現しやすい。
- `esc` や `ctrl+c` では正常に終了できる。

## 主な原因候補

1. **キー解放イベントが OS から届かない**
   - macOS の Secure Keyboard Entry、アプリ切り替え直後、アクセシビリティ設定の不足などで `pynput` の `on_release` が呼ばれず、`_pause_combo_active` が `True` のまま固まります。
2. **`emulate` でのリスナー競合**
   - `manage_listener=False` で `TerminationMonitor` を使っているため、プロファイル操作用リスナーが例外終了すると `monitor.on_key_release()` までイベントが届きません。
3. **ホットキー衝突または特殊キー**
   - Terminal のショートカット（履歴スクロール等）や JIS キーボードの `fn` 付き入力が混ざるとキー名変換に失敗し、押下集合から対象キーが消えません。

## 運用上の推奨対策

1. **Pause キーを衝突しにくい組み合わせへ変更**
   `runtime.controls.pause_toggle`（auto_emulator 設定）や `profile.controls.pause_toggle`（mouse_emulator プロファイル）を `cmd+shift+space` などに更新し、`mise run auto-validate` や `mise run emulate --pause-key` で反映を確認します。
2. **Secure Keyboard Entry を無効化**
   Terminal / iTerm2 のメニューから該当機能をオフにし、イベントタップを OS に許可させます。アクセシビリティのキーボード監視権限も要確認です。
3. **発生時はキーを押し直す／`esc` で終了**
   `_pause_combo_active` がリセットされるよう、コンボ対象のキーを単体で順番に押し直すと再開できる場合があります。どうしても戻らない場合は `esc` で終了して再実行します。

## 実装側で検討できる軽減策

- **ウォッチドッグで強制解除**: `_pause_event` が一定時間以上変化しない場合に `_pause_combo_active` をリセットするフェイルセーフ。ただし誤検知で意図しない解除が起こり得ます。
- **ログ出力強化**: `TerminationMonitor.on_key_press/on_key_release` にデバッグログを追加し、押下セットがどう変化しているかを記録して原因を特定します。
- **入力 API の切り替え**: `pynput` の代わりに Quartz Event Tap などを直接利用する。ただし権限や実装コストが大きく、イベント欠落を完全には防げません。

## 調査手順の例

1. 再現直後のターミナル出力を確認し、`Listener stopped` のような例外ログがないか調べる。
2. `TerminationMonitor` に一時的なデバッグログを入れ、押下集合 (`_pressed`) と `_pause_combo_active` の状態を記録する。
3. Pause キーの組み合わせを変更し、`auto-run` / `emulate` 双方で再現性を比較する。
4. Secure Keyboard Entry や IME 切り替えを操作して挙動の違いを確認する。

これらの情報をチーム内で共有し、必要に応じて実装側の軽減策と運用手順を合わせて検討してください。
