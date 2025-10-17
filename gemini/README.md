# Gemini CLI のカスタムスラッシュコマンドの管理

See: <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md>

## メモ

カスタムスラッシュコマンドを定義する toml では `!{}` を使ってシェルコマンドを実行させることができるが、その出力が `less` のようなページャーに渡されてしまうと、そこから抜け出せなくなっているように見える。（`!{}` で囲ってないコマンドを指示したときも同様）

そのため、 `git log` のようなページャーによる出力が発生するコマンドを実行する場合は、 `--no-pager` オプションを付与するなどしてページャーを無効化する必要がある。

例えば git コマンドは --no-pager オプションがあるので、以下のように記述する。

```toml
prompt = """
# BAD EXAMPLE
git log "$LATEST_TAG..HEAD" --pretty=format:'- %s'

# GOOD EXAMPLE
git --no-pager log "$LATEST_TAG..HEAD" --pretty=format:'- %s'
"""
```
