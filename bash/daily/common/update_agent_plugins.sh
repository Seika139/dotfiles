#!/usr/bin/env bash

set -u

PONYTAIL_SOURCE="DietrichGebert/ponytail"
PONYTAIL_PLUGIN="ponytail@ponytail"
UPDATE_STATUS=0

daily_plugin_warning() {
  printf 'Ponytail/plugin update: %s\n' "$1" >&2
}

read_claude_plugins() {
  # Keep JavaScript template interpolation literal for Node, not Bash.
  # shellcheck disable=SC2016
  node -e '
const fs = require("fs");
const plugins = JSON.parse(fs.readFileSync(0, "utf8"));
if (!Array.isArray(plugins) || plugins.some(plugin =>
  !plugin || typeof plugin.id !== "string" || !plugin.id ||
  typeof plugin.scope !== "string" || typeof plugin.enabled !== "boolean"
)) process.exit(2);

const userPlugins = new Map();
for (const plugin of plugins) {
  if (plugin.scope === "user") {
    userPlugins.set(plugin.id, Boolean(userPlugins.get(plugin.id) || plugin.enabled));
  }
}
for (const [id, enabled] of userPlugins) {
  if (id.startsWith("-") || /[\x00-\x1f\x7f]/.test(id)) continue;
  process.stdout.write(`${id}\t${enabled ? "1" : "0"}\n`);
}
'
}

read_codex_plugins() {
  node -e '
const fs = require("fs");
const data = JSON.parse(fs.readFileSync(0, "utf8"));
if (!data || !Array.isArray(data.installed) || data.installed.some(plugin =>
  !plugin || typeof plugin.pluginId !== "string" ||
  typeof plugin.installed !== "boolean" || typeof plugin.enabled !== "boolean"
)) process.exit(2);
process.stdout.write(data.installed.some(plugin =>
  plugin.installed && plugin.pluginId === "ponytail@ponytail"
) ? "present" : "absent");
'
}

codex_ponytail_marketplace_status() {
  node -e '
const fs = require("fs");
const data = JSON.parse(fs.readFileSync(0, "utf8"));
if (!data || !Array.isArray(data.marketplaces) || data.marketplaces.some(marketplace =>
  !marketplace || typeof marketplace.name !== "string"
)) process.exit(2);

const ponytail = data.marketplaces.find(marketplace => marketplace.name.toLowerCase() === "ponytail");
process.stdout.write(ponytail ? "registered" : "missing");
'
}

codex_ponytail_plugin_source_status() {
  node -e '
const fs = require("fs");
const data = JSON.parse(fs.readFileSync(0, "utf8"));
if (!data || !Array.isArray(data.available) || data.available.some(plugin =>
  !plugin || typeof plugin.pluginId !== "string"
)) process.exit(2);

const ponytail = data.available.find(plugin => plugin.pluginId === "ponytail@ponytail");
if (!ponytail) {
  process.stdout.write("missing");
} else {
  const source = ponytail.marketplaceSource;
  const value = source && typeof source.source === "string" ? source.source.trim() : "";
  const normalized = value.replace(/@main$/i, "").replace(/\.git$/i, "").toLowerCase();
  const isPonytail = source && source.sourceType === "git" && (
    normalized === "dietrichgebert/ponytail" ||
    normalized === "https://github.com/dietrichgebert/ponytail" ||
    normalized === "git@github.com:dietrichgebert/ponytail"
  );
  process.stdout.write(isPonytail ? "same" : "conflict");
}
'
}

update_claude_plugins() {
  if ! command -v claude >/dev/null 2>&1; then
    return 0
  fi

  local plugin_records=""
  local inventory_valid=false
  local ponytail_installed=false
  local plugin_id=""
  local enabled=""
  local ponytail_added=false

  if ! command -v node >/dev/null 2>&1; then
    daily_plugin_warning "node が無いため Claude の plugin 一覧を確認できません。Ponytail install と個別更新をスキップします。"
  elif plugin_records="$(claude plugin list --json </dev/null)"; then
    if plugin_records="$(printf '%s\n' "$plugin_records" | read_claude_plugins 2>/dev/null)"; then
      inventory_valid=true
      while IFS=$'\t' read -r plugin_id enabled; do
        [[ -n "$plugin_id" ]] || continue
        if [[ "$plugin_id" == "$PONYTAIL_PLUGIN" ]]; then
          ponytail_installed=true
        fi
      done <<<"$plugin_records"
    else
      daily_plugin_warning "Claude の plugin 一覧が不正な JSON 形式のため、Ponytail install と個別更新をスキップします。"
    fi
  else
    daily_plugin_warning "Claude の plugin 一覧を取得できないため、Ponytail install と個別更新をスキップします。"
  fi

  if [[ "$inventory_valid" == "true" && "$ponytail_installed" == "false" ]]; then
    printf '%s\n' "Claude に Ponytail を追加します。"
    if claude plugin install ponytail --marketplace "$PONYTAIL_SOURCE" --scope user </dev/null; then
      ponytail_added=true
    else
      daily_plugin_warning "Claude への Ponytail install に失敗しました。"
      UPDATE_STATUS=1
    fi
  fi

  printf '%s\n' "Claude の全 marketplace を更新します。"
  if ! claude plugin marketplace update </dev/null; then
    daily_plugin_warning "Claude marketplace の更新に失敗しました。"
    UPDATE_STATUS=1
  fi

  if [[ "$ponytail_added" == "true" ]]; then
    plugin_records="${plugin_records}${plugin_records:+$'\n'}${PONYTAIL_PLUGIN}"$'\t1'
  fi

  if [[ "$inventory_valid" == "true" && -n "$plugin_records" ]]; then
    while IFS=$'\t' read -r plugin_id enabled; do
      [[ "$enabled" == "1" ]] || continue
      if ! claude plugin update "$plugin_id" --scope user </dev/null; then
        daily_plugin_warning "Claude plugin ${plugin_id} の更新に失敗しました。"
        UPDATE_STATUS=1
      fi
    done <<<"$plugin_records"
  fi
}

update_codex_plugins() {
  if ! command -v codex >/dev/null 2>&1; then
    return 0
  fi

  local plugin_inventory=""
  local inventory_valid=false
  local ponytail_installed=false
  local marketplace_json=""
  local marketplace_status=""
  local plugin_list_json=""
  local plugin_source_status=""

  if ! command -v node >/dev/null 2>&1; then
    daily_plugin_warning "node が無いため Codex の plugin 一覧を確認できません。Ponytail install をスキップします。"
  elif plugin_inventory="$(codex plugin list --json </dev/null)"; then
    if plugin_inventory="$(printf '%s\n' "$plugin_inventory" | read_codex_plugins 2>/dev/null)"; then
      inventory_valid=true
      [[ "$plugin_inventory" == "present" ]] && ponytail_installed=true
    else
      daily_plugin_warning "Codex の plugin 一覧が不正な JSON 形式のため、Ponytail install をスキップします。"
    fi
  else
    daily_plugin_warning "Codex の plugin 一覧を取得できないため、Ponytail install をスキップします。"
  fi

  if [[ "$inventory_valid" == "true" && "$ponytail_installed" == "false" ]]; then
    if marketplace_json="$(codex plugin marketplace list --json </dev/null)"; then
      if marketplace_status="$(printf '%s\n' "$marketplace_json" | codex_ponytail_marketplace_status 2>/dev/null)"; then
        case "$marketplace_status" in
        missing)
          if codex plugin marketplace add "$PONYTAIL_SOURCE" </dev/null; then
            plugin_source_status="same"
          else
            daily_plugin_warning "Codex の Ponytail marketplace を追加できませんでした。"
            UPDATE_STATUS=1
          fi
          ;;
        registered)
          if plugin_list_json="$(codex plugin list --marketplace ponytail --available --json </dev/null)"; then
            if plugin_source_status="$(printf '%s\n' "$plugin_list_json" | codex_ponytail_plugin_source_status 2>/dev/null)"; then
              case "$plugin_source_status" in
              conflict)
                daily_plugin_warning "Codex の ponytail marketplace が別 source を指しているため、Ponytail install をスキップします。"
                ;;
              missing)
                daily_plugin_warning "Codex の ponytail marketplace に Ponytail plugin が無いため、install をスキップします。"
                ;;
              esac
            else
              daily_plugin_warning "Codex の available plugin 一覧が不正な JSON 形式のため、Ponytail install をスキップします。"
              plugin_source_status="invalid"
            fi
          else
            daily_plugin_warning "Codex の available plugin 一覧を取得できないため、Ponytail install をスキップします。"
            plugin_source_status="invalid"
          fi
          ;;
        esac
      else
        daily_plugin_warning "Codex の marketplace 一覧が不正な JSON 形式のため、Ponytail install をスキップします。"
        marketplace_status="invalid"
      fi
    else
      daily_plugin_warning "Codex の marketplace 一覧を取得できないため、Ponytail install をスキップします。"
      marketplace_status="invalid"
    fi

    if [[ "$plugin_source_status" == "same" ]] && ! codex plugin add "$PONYTAIL_PLUGIN" </dev/null; then
      daily_plugin_warning "Codex への Ponytail install に失敗しました。"
      UPDATE_STATUS=1
    fi
  fi

  printf '%s\n' "Codex の全 Git marketplace と plugin cache を更新します。"
  if ! codex plugin marketplace upgrade </dev/null; then
    daily_plugin_warning "Codex marketplace の更新に失敗しました。"
    UPDATE_STATUS=1
  fi
}

if [[ -z "${HOME:-}" ]] || ! cd "$HOME"; then
  daily_plugin_warning "user scope に移動できないため更新をスキップします。"
  exit 1
fi

update_claude_plugins
update_codex_plugins
exit "$UPDATE_STATUS"
