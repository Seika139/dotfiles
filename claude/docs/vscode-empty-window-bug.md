# Claude Code + VS Code: 空ウィンドウが開くバグ

## 概要

Windows の VS Code 統合ターミナルで `claude` コマンドを起動すると、空の VS Code ウィンドウが複数開く問題。

## 発生条件

- **OS**: Windows 11
- **VS Code**: 公式インストーラー版（User Setup）
- **Claude Code**: v2.1.23 で確認
- **実行場所**: VS Code 統合ターミナル（bash）

### 発生しない環境

- PowerShell（外部ターミナル）から `claude` を実行 → 発生しない
- WSL 上の VS Code ターミナルから `claude` を実行 → 発生しない
- VS Code が Scoop 管理だった時期 → 発生しなかった

## 原因

Claude Code は環境変数 `TERM_PROGRAM=vscode` を検出すると、VS Code との IDE 統合モードで動作する。
この際、内部的に `code` CLI を呼び出して VS Code と連携しようとするが、公式インストーラー版の `code` CLI との IPC（プロセス間通信）が正常に確立されず、空のウィンドウが開いてしまう。

## 回避策

`TERM_PROGRAM` を空にして Claude Code を起動すると、IDE 統合が無効化され、空ウィンドウは開かなくなる。

### 手動実行

```bash
TERM_PROGRAM= claude
```

### 恒久対策（bash alias）

`.bash_profile` または `.bashrc` に以下を追加：

```bash
alias claude='TERM_PROGRAM= command claude'
```

### 影響

- IDE 統合（VS Code 上でのファイルオープン・diff 表示等）が無効になるが、Claude Code のファイル編集（Edit/Write ツール）は正常に動作するため、実用上の影響はほぼない。

## 今後の見通し

- Claude Code の IDE 統合処理のバグである可能性が高く、**Claude Code のアップデートで修正されうる**
- 修正後は alias を削除すれば IDE 統合機能が利用可能になる
- 状況が変わったら `TERM_PROGRAM=` を外して再テストし、空ウィンドウが開かなくなっていれば alias を削除する

## 関連情報

- 発見日: 2026-03-31
- 背景: VS Code を Scoop 管理から公式インストーラーに移行した際に発生
- GitHub Issues: <https://github.com/anthropics/claude-code/issues>
