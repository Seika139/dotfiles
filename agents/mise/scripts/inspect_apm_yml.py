#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""apm.yml (+ optional private overlay) を解析し、status 表示用のフィールドを抽出する。

stdout に prefix-tagged な TSV を 1 行 1 件で出力する:

    target      <name>            base の targets
    apm-base    <pkg>           base の dependencies.apm から抽出した package 名
    apm-overlay <pkg>           overlay の dependencies.apm から抽出した package 名
    apm-merged  <pkg>           base + overlay を dedup したあとの package 名

package 名抽出ルール: string form の ref または object form の path が
".../packages/<name>" 形式なら <name>、それ以外は末尾のパスセグメントを
package 名として返す (外部 repo の SKILL.md 配備先ディレクトリ名と一致させるため)。

ただし string form の ref が "packages/" を含まず、かつ "<owner>/<repo>" の
bare な形式 (集約 repo をまとめて取り込む形式) の場合は、その先の
dependencies.apm から実際のサブパッケージ名リストへ展開する。展開元は
次の優先順で決める:

  1. `gh api` で対象 repo の apm.yml を live 取得 (5秒でタイムアウト)。
     取得できて dependencies.apm が非空ならそれを使う。
  2. live 取得に失敗した場合 (オフライン / gh 未認証 / repo 変更等) は、
     ローカルの `~/.apm/apm_modules/<owner>/<repo>/apm.yml`
     (`apm install -g` 実行後に transitively 展開されて配備される先)
     にフォールバックする。
  3. どちらも無ければ bare な文字列自体を 1件として返す。
"""

from __future__ import annotations

import argparse
import base64
import subprocess
import sys
from pathlib import Path

import yaml


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SystemExit(f"❌ {path} のトップレベルが mapping ではありません")
    return data


def _name_from_path(path: str) -> str:
    head = path.split("#", 1)[0].replace("\\", "/").strip("/")
    if head.startswith("packages/"):
        return head.removeprefix("packages/").strip("/")
    if "/packages/" in head:
        return head.rsplit("/packages/", 1)[-1].strip("/")
    # packages/ 慣習を持たない外部 repo (例: owner/repo/skills/<category>/<name>) は
    # 末尾のパスセグメントが SKILL.md 配備先のディレクトリ名と一致するため、それを使う。
    if "/" in head:
        return head.rsplit("/", 1)[-1]
    return head


APM_MODULES = Path.home() / ".apm" / "apm_modules"

GH_FETCH_TIMEOUT_SECONDS = 5  # オフライン時に mise run status を長時間ハングさせない


def _fetch_remote_apm_yml(owner: str, repo: str, git_ref: str | None) -> dict | None:
    """`gh api` で <owner>/<repo> の apm.yml を live に取得する。

    gh 未導入 / 未認証 / オフライン / repo やファイルが見つからない等、
    何らかの理由で取得できない場合は例外を投げず None を返す
    (呼び出し側でローカルキャッシュへフォールバックさせる)。
    """
    args = ["gh", "api", f"repos/{owner}/{repo}/contents/apm.yml", "--jq", ".content"]
    if git_ref:
        args += ["-f", f"ref={git_ref}"]
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=GH_FETCH_TIMEOUT_SECONDS,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        raw = base64.b64decode(result.stdout.strip()).decode("utf-8")
        data = yaml.safe_load(raw)
    except (ValueError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def _looks_like_bare_repo(head: str) -> bool:
    """`<owner>/<repo>` 形式 (追加の path segment を含まない) かどうか。"""
    parts = head.split("/")
    return len(parts) == 2 and all(parts)


def _expand_bare_repo(head: str, git_ref: str | None) -> list[str] | None:
    """owner/repo 形式の集約参照を、参照先自身の apm.yml (dependencies.apm)
    から展開する。

    まず `gh api` で live 取得を試み、取得できなければローカルの
    apm_modules キャッシュにフォールバックする。どちらも無ければ None を
    返し、呼び出し側で bare な文字列自体へフォールバックさせる。
    """
    owner, repo = head.split("/", 1)

    remote_doc = _fetch_remote_apm_yml(owner, repo, git_ref)
    if remote_doc is not None:
        names = [n for r in _apm_list(remote_doc) for n in _pkg_names(r)]
        expanded = _dedup(names)
        if expanded:
            return expanded

    agg_yml = APM_MODULES / owner / repo / "apm.yml"
    if not agg_yml.is_file():
        return None
    agg_doc = _load(agg_yml)
    names = [n for r in _apm_list(agg_doc) for n in _pkg_names(r)]
    return _dedup(names) or None


def _pkg_names(ref) -> list[str]:
    if isinstance(ref, str):
        head, _, git_ref = ref.partition("#")
        raw_head = head.replace("\\", "/").strip("/")
        if "packages/" not in raw_head and _looks_like_bare_repo(raw_head):
            expanded = _expand_bare_repo(raw_head, git_ref or None)
            if expanded:
                return expanded
        return [_name_from_path(ref)]
    if isinstance(ref, dict) and isinstance(ref.get("path"), str):
        return [_name_from_path(ref["path"])]
    return [yaml.safe_dump(ref, sort_keys=True, default_flow_style=True).strip()]


def _apm_list(doc: dict) -> list:
    return ((doc.get("dependencies") or {}).get("apm")) or []


def _dedup(items) -> list:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _iter_lock_deployed_files(lock_path: Path) -> list[str]:
    """apm.lock.yaml の dependencies[].deployed_files を平坦化して返す。

    ファイルが存在しない場合はエラーにせず空リストを返す
    (--lock 未指定時と同じ扱いにするため)。
    """
    if not lock_path.is_file():
        return []
    doc = _load(lock_path)
    files: list[str] = []
    for dep in doc.get("dependencies") or []:
        files.extend(dep.get("deployed_files") or [])
    return _dedup(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()

    base = _load(args.base)
    overlay = _load(args.overlay) if args.overlay and args.overlay.is_file() else {}

    for tgt in base.get("targets") or []:
        print(f"target\t{tgt}")

    base_names = [n for r in _apm_list(base) for n in _pkg_names(r)]
    overlay_names = [n for r in _apm_list(overlay) for n in _pkg_names(r)]

    for n in base_names:
        print(f"apm-base\t{n}")
    for n in overlay_names:
        print(f"apm-overlay\t{n}")
    for n in _dedup(base_names + overlay_names):
        print(f"apm-merged\t{n}")

    if args.lock:
        for path in _iter_lock_deployed_files(args.lock):
            print(f"deployed\t{path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
