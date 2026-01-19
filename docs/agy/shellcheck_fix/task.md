# ShellCheck 警告の修正

- [x] ドキュメント用ディレクトリ作成 `docs/agy/shellcheck_fix`
- [x] 実装計画の作成 `docs/agy/shellcheck_fix/implementation_plan.md`
- [x] 各スクリプトの修正
  - [x] `bash/public/11_alias.bash` (SC2086)
  - [x] `bash/public/41_ltsv_to_json.bash` (SC2128, SC2162)
  - [x] `bash/public/12_git_alias.bash` (SC2089, SC2090, SC2086)
  - [x] `bash/public/04_prompt.bash` (SC2016 の精査と対応)
- [x] 修正後の再確認 (mise run shellcheck)
- [x] 完了報告 `docs/agy/shellcheck_fix/walkthrough.md`
