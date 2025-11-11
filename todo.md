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

- [ ] `~/.config/` の一部のアプリを dotfiles で管理するようにする

  - [ ] mise の設定ファイル

    - [ ] `~/.config/mise/config.toml` を dotfiles で管理するようにする

      - [ ] `mise use -g config` で config ファイルのパスを確認する

      - [ ] `dotfiles/config/mise/config.toml` に移動させる

      - [ ] シンボリックリンクを作成する

        ```bash
        ln -s ~/dotfiles/config/mise/config.toml ~/.config/mise/config.toml
        ```

      - [ ] dotfiles の管理下に置く

    - [ ] 他に管理したいアプリケーションがあれば同様に行う
