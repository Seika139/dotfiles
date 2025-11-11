# TODO

- [ ] cg-mc2-mac で以下のことをする

  - [ ] bash-completion@2 を入れ、 v1 をアンインストールする

    ```bash
    brew uninstall bash-completion
    brew install bash-completion@2
    ```

  - [ ] mise の補完設定の確認 `mise use -g usage` → `~/.config/mise/config.toml` に

    ```toml
    [completion]
    enable = true
    ```

    があることを確認する
