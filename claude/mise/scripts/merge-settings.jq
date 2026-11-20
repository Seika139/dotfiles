# link.sh / status.sh 共通: `jq -s -f merge-settings.jq settings.json settings.local.json`
# 詳細は claude/docs/settings-sync.md を参照。
#
# 基本は .[0] * .[1] (local が portable を上書き) だが、`*` は配列を右辺で丸ごと
# 置換するため hooks だけはイベント単位で portable + local を連結する。
# local 側のエントリで portable 側と完全一致するものは重複として除去する。
# 旧 APM 版 Ponytail の既知 command は、link/status/recover で再導入しない。

def legacy_ponytail_commands:
  ["ponytail-activate.js", "ponytail-mode-tracker.js", "ponytail-subagent.js"]
  | map([
      "node -e \"const p=require('path'),o=require('os');"
      + "process.env.CLAUDE_PLUGIN_ROOT=p.join(o.homedir(),'.apm','apm_modules',"
      + "'DietrichGebert','ponytail');"
      + "require(p.join(process.env.CLAUDE_PLUGIN_ROOT,'hooks/" + . + "'))\"",
      "node -e \"require(require('path').join(process.env.CLAUDE_PLUGIN_ROOT"
      + ".split(String.fromCharCode(92)).join('/'), 'hooks/" + . + "'))\"",
      "node -e \"require(require('node:path').join(process.env.CLAUDE_PLUGIN_ROOT"
      + ".replaceAll(String.fromCharCode(92), '/'), 'hooks/" + . + "'))\""
    ])
  | add;

def is_legacy_ponytail_hook:
  if type != "object" then false
  elif (.command? | type) == "string" then
    .command as $command | (legacy_ponytail_commands | index($command)) != null
  else false end;

def filter_legacy_ponytail_group:
  if type != "object" or (.hooks | type) != "array" then .
  else
    . as $group |
    (.hooks | map(select(is_legacy_ponytail_hook | not))) as $retained_hooks |
    if ($retained_hooks | length) > 0 then .hooks = $retained_hooks
    elif ($group.hooks | length) == 0 then $group
    else empty
    end
  end;

def filter_legacy_ponytail_events:
  with_entries(
    . as $event |
    (.value | map(filter_legacy_ponytail_group)) as $retained_groups |
    if ($retained_groups | length) > 0 or ($event.value | length) == 0 then
      .value = $retained_groups
    else empty end
  );

def hooks_of($name):
  if has("hooks") | not then {}
  elif (.hooks | type) != "object" then error("\($name): hooks はオブジェクトである必要があります (実際: \(.hooks | type))")
  else
    .hooks
    | to_entries
    | map(if (.value | type) != "array" then error("\($name): hooks.\(.key) は配列である必要があります (実際: \(.value | type))") else . end)
    | from_entries
    | filter_legacy_ponytail_events
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
