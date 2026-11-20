#!/usr/bin/env bash

# Prepare ~/.cursor as a real directory so APM can safely write user-scope files.
# The legacy installer linked the whole directory to dotfiles/.cursor, which
# made APM reject Cursor hook configuration paths that crossed that symlink.

cursor_home_seed_entry() {
  local source_entry="$1"
  local target_dir="$2"
  local entry_name="${source_entry##*/}"
  local target_entry="${target_dir}/${entry_name}"

  [[ -e "${source_entry}" || -L "${source_entry}" ]] || return 0
  [[ -e "${target_entry}" || -L "${target_entry}" ]] && return 0

  case "${entry_name}" in
  .gitignore | argv.json.template)
    if [[ ! -f "${source_entry}" || -L "${source_entry}" ]]; then
      printf '⚠️  Cursor tracked config is not a regular file: %s\n' "${source_entry}"
      return 1
    fi
    ln -s "${source_entry}" "${target_entry}"
    ;;
  mcp.json)
    if [[ ! -f "${source_entry}" || -L "${source_entry}" ]]; then
      printf '⚠️  Cursor MCP config is not a regular file: %s\n' "${source_entry}"
      return 1
    fi
    cp -p "${source_entry}" "${target_entry}"
    ;;
  agents | skills | commands | rules)
    if [[ -L "${source_entry}" || ! -d "${source_entry}" ]]; then
      printf '⚠️  Cursor APM directory is not a real directory: %s\n' "${source_entry}"
      return 1
    fi
    cp -Rp "${source_entry}" "${target_entry}"
    ;;
  hooks.json | apm-hooks.json)
    if [[ ! -f "${source_entry}" || -L "${source_entry}" ]]; then
      printf '⚠️  Cursor hook config is not a regular file: %s\n' "${source_entry}"
      return 1
    fi
    cp -p "${source_entry}" "${target_entry}"
    ;;
  *)
    ln -s "${source_entry}" "${target_entry}"
    ;;
  esac
}

cursor_home_populate() {
  local source_dir="$1"
  local target_dir="$2"
  local source_entry
  local entry_list
  local seed_status=0

  entry_list="$(mktemp "${TMPDIR:-/tmp}/cursor-home-entries.XXXXXX")" || return 1
  if ! find "${source_dir}" -mindepth 1 -maxdepth 1 -print0 >"${entry_list}"; then
    rm -f "${entry_list}"
    printf '⚠️  Could not enumerate Cursor config entries: %s\n' "${source_dir}"
    return 1
  fi
  while IFS= read -r -d '' source_entry; do
    if ! cursor_home_seed_entry "${source_entry}" "${target_dir}"; then
      seed_status=1
      break
    fi
  done <"${entry_list}"
  rm -f "${entry_list}"
  [[ "${seed_status}" -eq 0 ]] || return 1

  # These are APM output directories even when the source profile has no files
  # for them yet. Keep them as real directories from the first install.
  local apm_dir
  for apm_dir in agents skills commands rules; do
    if [[ -L "${target_dir}/${apm_dir}" ]]; then
      printf '⚠️  Cursor APM directory is a symlink; leaving it untouched: %s\n' "${target_dir}/${apm_dir}"
      return 1
    fi
    if [[ -e "${target_dir}/${apm_dir}" && ! -d "${target_dir}/${apm_dir}" ]]; then
      printf '⚠️  Cursor APM path is not a directory; leaving it untouched: %s\n' "${target_dir}/${apm_dir}"
      return 1
    fi
    mkdir -p "${target_dir}/${apm_dir}" || return 1
  done
}

cursor_home_validate_apm_paths() {
  local target_dir="$1"
  local apm_dir
  local hook_file

  for apm_dir in agents skills commands rules; do
    if [[ -L "${target_dir}/${apm_dir}" || (-e "${target_dir}/${apm_dir}" && ! -d "${target_dir}/${apm_dir}") ]]; then
      printf '⚠️  Cursor APM directory must be a real directory: %s\n' "${target_dir}/${apm_dir}"
      return 1
    fi
  done
  for hook_file in hooks.json apm-hooks.json; do
    if [[ -L "${target_dir}/${hook_file}" ]]; then
      printf '⚠️  Cursor hook config must be a regular file, not a symlink: %s\n' "${target_dir}/${hook_file}"
      return 1
    fi
    if [[ -e "${target_dir}/${hook_file}" && ! -f "${target_dir}/${hook_file}" ]]; then
      printf '⚠️  Cursor hook config is not a regular file: %s\n' "${target_dir}/${hook_file}"
      return 1
    fi
  done
  if [[ -L "${target_dir}/mcp.json" ]]; then
    printf '⚠️  Cursor MCP config must be a regular file, not a symlink: %s\n' "${target_dir}/mcp.json"
    return 1
  fi
  if [[ -e "${target_dir}/mcp.json" && ! -f "${target_dir}/mcp.json" ]]; then
    printf '⚠️  Cursor MCP config is not a regular file: %s\n' "${target_dir}/mcp.json"
    return 1
  fi
}

cursor_home_resolve_file_path() {
  local file_path="$1"
  local parent_dir="${file_path%/*}"
  local file_name="${file_path##*/}"

  [[ "${file_path}" == */* ]] || parent_dir="."
  parent_dir="$(cd -- "${parent_dir}" 2>/dev/null && pwd -P)" || return 1
  printf '%s/%s\n' "${parent_dir}" "${file_name}"
}

cursor_home_materialize_mcp() {
  local source_file="$1"
  local target_dir="$2"
  local target_file="${target_dir}/mcp.json"
  local link_target
  local resolved_link_target
  local resolved_source_file
  local temporary

  [[ -e "${source_file}" || -L "${source_file}" ]] || return 0
  if [[ ! -f "${source_file}" || -L "${source_file}" ]]; then
    printf '⚠️  Cursor MCP source is not a regular file: %s\n' "${source_file}"
    return 1
  fi
  if [[ -L "${target_file}" ]]; then
    link_target="$(readlink "${target_file}")"
    if [[ "${link_target}" != /* ]]; then
      link_target="${target_dir}/${link_target}"
    fi
    resolved_link_target="$(cursor_home_resolve_file_path "${link_target}")" || resolved_link_target=""
    resolved_source_file="$(cursor_home_resolve_file_path "${source_file}")" || resolved_source_file=""
    if [[ "${resolved_link_target}" != "${resolved_source_file}" ]]; then
      printf '⚠️  Cursor MCP config points elsewhere; leaving it untouched: %s\n' "${link_target}"
      return 1
    fi
    temporary="$(mktemp "${target_dir}/.mcp.json.XXXXXX")" || return 1
    if ! cp -p "${target_file}" "${temporary}" || ! mv -f "${temporary}" "${target_file}"; then
      rm -f "${temporary}"
      printf '⚠️  Could not materialize Cursor MCP config: %s\n' "${target_file}"
      return 1
    fi
  elif [[ ! -e "${target_file}" ]]; then
    cp -p "${source_file}" "${target_file}" || return 1
  elif [[ ! -f "${target_file}" ]]; then
    printf '⚠️  Cursor MCP config is not a regular file: %s\n' "${target_file}"
    return 1
  fi
}

cursor_home_migrate_apm_config() {
  local dotfiles_root="$1"
  local target_dir="$2"
  local mcp_source="${dotfiles_root}/.cursor/mcp.json"
  local migration_script="${dotfiles_root}/agents/mise/scripts/migrate_cursor_apm_config.py"
  local python_runner="${dotfiles_root}/claude/mise/scripts/run_python.sh"

  cursor_home_materialize_mcp "${mcp_source}" "${target_dir}" || return 1
  cursor_home_validate_apm_paths "${target_dir}" || return 1
  bash "${python_runner}" "${migration_script}" --cursor-dir "${target_dir}" --mcp-source "${mcp_source}"
}

cursor_home_commit_staging() {
  local staging_dir="$1"
  local target_dir="$2"
  local marker_path
  local marker_name
  local staging_name="${staging_dir##*/}"

  marker_path="$(mktemp "${staging_dir}/.cursor-migration-check.XXXXXX")" || return 1
  marker_name="${marker_path##*/}"
  # -n avoids replacing an existing file or link. If a process recreates the
  # target directory during the switch, mv may place staging inside it; the
  # marker check detects that case and moves staging back when possible.
  if ! mv -n "${staging_dir}" "${target_dir}"; then
    rm -f "${staging_dir}/${marker_name}"
    return 1
  fi
  if [[ -f "${target_dir}/${marker_name}" ]]; then
    rm -f "${target_dir}/${marker_name}"
    return 0
  fi
  if [[ -f "${target_dir}/${staging_name}/${marker_name}" ]]; then
    if mv -n "${target_dir}/${staging_name}" "${staging_dir}" && [[ -f "${staging_dir}/${marker_name}" ]]; then
      printf '⚠️  Cursor target appeared during migration; staging was recovered at %s\n' "${staging_dir}"
    else
      printf '⚠️  Cursor target appeared during migration; inspect staged files at %s\n' "${target_dir}/${staging_name}"
    fi
    return 1
  fi
  if [[ -e "${staging_dir}" || -L "${staging_dir}" ]]; then
    rm -f "${staging_dir}/${marker_name}"
    printf '⚠️  Cursor target was not replaced; staging remains at %s\n' "${staging_dir}"
  else
    printf '⚠️  Cursor migration result is uncertain; inspect %s and %s\n' "${target_dir}" "${staging_dir}"
  fi
  return 1
}

ensure_dotfiles_cursor_home() {
  local dotfiles_root="$1"
  local home_dir="$2"
  local source_dir
  local target_dir="${home_dir}/.cursor"
  local current_target
  local resolved_target
  local staging_dir=""
  local backup_path
  local suffix=0

  if ! dotfiles_root="$(cd -- "${dotfiles_root}" 2>/dev/null && pwd -P)"; then
    printf '⚠️  dotfiles root is not an accessible directory: %s\n' "$1"
    return 1
  fi
  source_dir="${dotfiles_root}/.cursor"

  if [[ ! -d "${source_dir}" || -L "${source_dir}" ]]; then
    printf '⚠️  dotfiles Cursor config is not a real directory: %s\n' "${source_dir}"
    return 1
  fi

  if [[ -L "${target_dir}" ]]; then
    current_target="$(readlink "${target_dir}")"
    if [[ "${current_target}" != /* ]]; then
      current_target="${target_dir%/*}/${current_target}"
    fi
    resolved_target="$(cd -- "${current_target}" 2>/dev/null && pwd -P)" || resolved_target=""
    if [[ "${resolved_target}" != "${source_dir}" ]]; then
      printf '⚠️  %s points elsewhere; leaving it untouched: %s\n' "${target_dir}" "${current_target}"
      return 2
    fi

    staging_dir="$(mktemp -d "${home_dir}/.cursor.staging.XXXXXX")" || return 1
    if ! cursor_home_populate "${source_dir}" "${staging_dir}"; then
      rm -rf "${staging_dir}"
      return 1
    fi

    backup_path="${home_dir}/.cursor.legacy-link.$(date +%Y%m%d_%H%M%S).$$"
    while [[ -e "${backup_path}" || -L "${backup_path}" ]]; do
      suffix=$((suffix + 1))
      backup_path="${home_dir}/.cursor.legacy-link.$(date +%Y%m%d_%H%M%S).$$.${suffix}"
    done

    if ! mv "${target_dir}" "${backup_path}"; then
      rm -rf "${staging_dir}"
      printf '⚠️  Could not back up legacy Cursor link: %s\n' "${target_dir}"
      return 1
    fi
    if ! cursor_home_commit_staging "${staging_dir}" "${target_dir}"; then
      if [[ ! -e "${target_dir}" && ! -L "${target_dir}" ]] && mv "${backup_path}" "${target_dir}"; then
        printf '⚠️  Cursor migration failed; restored the original link.\n'
      else
        printf '⚠️  Cursor migration failed. Original link is preserved at %s\n' "${backup_path}"
      fi
      return 1
    fi
    printf '✅ Cursor config is now a real directory: %s\n' "${target_dir}"
    printf '   Legacy link backup: %s\n' "${backup_path}"
  elif [[ -e "${target_dir}" ]]; then
    if [[ ! -d "${target_dir}" ]]; then
      printf '⚠️  Cursor config exists and is not a directory; leaving it untouched: %s\n' "${target_dir}"
      return 2
    fi
    if ! cursor_home_materialize_mcp "${source_dir}/mcp.json" "${target_dir}"; then
      return 1
    fi
    if ! cursor_home_validate_apm_paths "${target_dir}"; then
      return 1
    fi
    if ! cursor_home_populate "${source_dir}" "${target_dir}"; then
      return 1
    fi
    cursor_home_validate_apm_paths "${target_dir}" || return 1
  else
    staging_dir="$(mktemp -d "${home_dir}/.cursor.staging.XXXXXX")" || return 1
    if ! cursor_home_populate "${source_dir}" "${staging_dir}"; then
      rm -rf "${staging_dir}"
      return 1
    fi
    if ! cursor_home_commit_staging "${staging_dir}" "${target_dir}"; then
      printf '⚠️  Could not create Cursor config directory: %s\n' "${target_dir}"
      return 1
    fi
    printf '✅ Created Cursor config directory: %s\n' "${target_dir}"
  fi

  cursor_home_migrate_apm_config "${dotfiles_root}" "${target_dir}" || return 1
}
