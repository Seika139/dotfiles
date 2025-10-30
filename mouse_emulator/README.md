# Mouse Emulator

macOS 上でキーボード操作によるマウスエミュレーションを行うツールです。`mise` を利用して `register` と `emulate` のタスクを提供します。

## 必要要件

- macOS (Apple silicon)
- アクセシビリティで "ターミナル" によるキーボード/マウス操作の許可
- Python 3.11 以上
- `mise`, `uv`

## 使い方

1. `uv sync` で依存関係をセットアップします。
2. `mise run register <profile-name>` でプロファイルを作成し、`profiles/<profile-name>.json` に保存されます。登録時は画面上でキャリブレーションを行い、領域の左上・右下でそれぞれ `shift+enter` を押して範囲を決めます。割り当てたいキーの組み合わせを押すと「キー: ... に対応する座標をクリックしてください」と表示されるので、その後に目的の位置をクリックしてください。
3. `mise run emulate profiles/<profile>.json` で登録済みプロファイルに基づいてマウス操作をエミュレートします。実行時も同様にキャリブレーションを行い、登録済みのキーを押すと対応する位置でクリックが発動します。

詳細は `docs/mise` および `docs/uv` を参照してください。
