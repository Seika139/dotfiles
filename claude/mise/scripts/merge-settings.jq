# link.sh / status.sh 共通: `jq -s -f merge-settings.jq settings.json settings.local.json`
# 詳細は claude/docs/settings-sync.md を参照。
#
# 基本は .[0] * .[1] (local が portable を上書き) だが、`*` は配列を右辺で丸ごと
# 置換するため hooks だけはイベント単位で portable + local を連結する。
# local 側のエントリで portable 側と完全一致するものは重複として除去する。

def hooks_of($name):
  if has("hooks") | not then {}
  elif (.hooks | type) != "object" then error("\($name): hooks はオブジェクトである必要があります (実際: \(.hooks | type))")
  else
    .hooks
    | to_entries
    | map(if (.value | type) != "array" then error("\($name): hooks.\(.key) は配列である必要があります (実際: \(.value | type))") else . end)
    | from_entries
  end;

.[0] as $portable |
.[1] as $local |
($portable | hooks_of("settings.json")) as $ph |
($local | hooks_of("settings.local.json")) as $lh |
($portable * $local) |
if ($portable | has("hooks")) or ($local | has("hooks")) then
  .hooks = (reduce (($ph + $lh) | keys[]) as $e ({};
    ($ph[$e] // []) as $pe |
    .[$e] = $pe + (($lh[$e] // []) | map(select(. as $x | $pe | any(. == $x) | not)))
  ))
else . end
