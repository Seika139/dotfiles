# Mouse Emulator Overview

`mouse_emulator` はキーボードのキーコンボにマウス操作を割り当てるツールです。キャリブレーションで指定した矩形領域を基準に、相対座標へ正規化してクリック・ドラッグなどを実行します。

## 主なコマンド

| コマンド | 説明 |
| --- | --- |
| `mise run register --prof <name>` | プロファイルを新規作成し、アクションを対話的に登録します。 |
| `mise run emulate --prof <name>` | 指定プロファイルに基づいてマウス操作をエミュレートします。 |

> どちらも内部で `.venv/bin/python -m mouse_emulator <subcommand>` を呼び出します。`uv run` を直接使うと macOS の SystemConfiguration 制限で失敗する環境があるため、`.venv` を前提にしています。

## キャリブレーションの流れ

1. `register` を実行すると、領域の左上・右下でそれぞれ `shift+enter` を押して矩形を指定します。
2. 割り当てたいキーコンボを押すと「キー: ... に対応する座標をクリックしてください」と表示されるので、マウスで目的の位置をクリックします。
3. すべてのアクションを登録し終えたら `esc` で終了し、プロファイルが JSON として保存されます。

## ランタイム操作

- 既定の終了キーは `esc` または `ctrl+c`。
- プロファイルまたは CLI の `--pause-key` オプションで一時停止・再開用のホットキーを設定できます。
- `mise run emulate --log-file logs/session.log` のように指定すると標準出力に加えてログファイルにも出力します。

プロファイル JSON の詳細やサンプルは [`profiles.md`](profiles.md) を参照してください。基本的なプロファイルは [`../examples/mouse_profile_basic.json`](../examples/mouse_profile_basic.json) に用意してあります。***
