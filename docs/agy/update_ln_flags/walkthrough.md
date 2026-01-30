# ln コマンドのフラグ更新結果の詳細

既存のシンボリックリンク作成コマンドにおいて、ディレクトリを扱う際の安全性を高めるため、`-sfv` から `-sfnv` への一括更新を行いました。

## 変更内容

以下のファイルにおいて、`ln -sfv` を `ln -sfnv` に変更しました。

### 変更されたファイル

1. **[install.sh](file:///Users/suzukikenichi/dotfiles/install.sh)**
    - 初期セットアップ時のシンボリックリンク作成処理を一括更新。
2. **[claude/mise.toml](file:///Users/suzukikenichi/dotfiles/claude/mise.toml)**
    - Claudeプロファイル切り替え時のリンク処理を更新。
3. **[codex/mise.toml](file:///Users/suzukikenichi/dotfiles/codex/mise.toml)**
    - Codexプロファイル切り替え時のリンク処理を更新。
4. **[gemini/mise.toml](file:///Users/suzukikenichi/dotfiles/gemini/mise.toml)**
    - Geminiプロファイル切り替え時のリンク処理を更新。
5. **[11_alias.bash](file:///Users/suzukikenichi/dotfiles/bash/public/11_alias.bash)**
    - `bat` および `fd` のシンボリックリンク作成箇所を更新。

## 検証結果

### ShellCheck による検証

`install.sh` および `11_alias.bash` に対して `shellcheck` を実行し、構文エラーがないことを確認しました。

```bash
$ shellcheck install.sh && echo "ShellCheck passed"
ShellCheck passed
```

### 内容の目視確認

各ファイルにおける置換が正しく行われ、余分なスペースや誤字が混入していないことを確認しました。

## 注意事項

`-n` フラグは「リンク先がすでにディレクトリへのシンボリックリンクである場合、そのリンク自体を上書きする（辿らない）」動作を保証します。これにより、予期せぬディレクトリ内への二重リンク作成を防ぐことができます。
