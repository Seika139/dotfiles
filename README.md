# dotfiles

## 動作環境

以下の環境で動作することを確認しています。（動作するように dotfiles を育ている）
bash を使用してください。

- Mac 系: ターミナル、iTerm2、VS Code 内のターミナル
- Win 系: GitBash、VS Code 内のターミナル（Git Bash）

## install

```bash
source install.sh
```

## uninstall

install.sh でホームディレクトリに作成したシンボリックリンクを uninstall.sh で削除します。

```bash
source uninstall.sh
```

## Change `__git_ps1`

Windows の GitBash が `__git_ps1` を読み込むのに時間をかけているので、ブランチ名だけを表示する簡易的な `__git_ps1` を作成した。
これにより、デフォルトでは Windows の GitBash では git によるファイル差分が表示されなくなっている。

以下のコマンドで表示を切り替えることができる。

```bash
lighten_ps1 # 軽くする(gitによるファイル差分を表示しない)
normalize_ps1 # 普通にする(gitによるファイル差分を表示する)
```

## dotfiles とは

ホームディレクトリに置いてあるドット(.)から始まる設定ファイル(.bashrc とか)を管理しているリポジトリのこと。
先輩につくることを勧められたので私も制作して運用中（4 年目）。

## 参考

### 特に参考になった

- [ようこそ dotfiles の世界へ](https://qiita.com/yutkat/items/c6c7584d9795799ee164)
- [【初心者版】必要最小限の dotfiles を運用する](https://qiita.com/ganyariya/items/d9adffc6535dfca6784b)

### これから見たい

- [dotfiles の育て方](https://qiita.com/reireias/items/b33b5c824a56dc89e1f7)

### その他

- [dotfiles を GitHub で管理](https://qiita.com/okamos/items/7f5461814e8ed8916870)

## TODO

- ライセンスを追加したい
- zsh
  <!-- TODO bash_profile や bashrc を環境(PC)ごとに変えられるようにする -->
  <!-- TODO 勝手なpushを抑制する -->
