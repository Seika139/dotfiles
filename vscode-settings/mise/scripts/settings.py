#!/usr/bin/env python3
"""VS Code の settings.json を 3 層 (shared -> profile -> local) のテキスト合成で扱う。

トップレベルエントリ単位でリーダーコメントごと連結するため、コメントは失われない。
同じトップレベルキーが複数層に現れたらエラーにする (上書きしない)。
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "shared" / "settings.json"


class SettingsError(Exception):
    pass


# ---------- 字句処理 ----------


def skip_ws_comments(t, i):
    n = len(t)
    while i < n:
        if t[i].isspace():
            i += 1
        elif t.startswith("//", i):
            j = t.find("\n", i)
            i = n if j < 0 else j
        elif t.startswith("/*", i):
            j = t.find("*/", i + 2)
            if j < 0:
                raise SettingsError("閉じていないブロックコメントがあります")
            i = j + 2
        else:
            break
    return i


def skip_string(t, i):
    j = i + 1
    while j < len(t):
        if t[j] == "\\":
            j += 2
        elif t[j] == '"':
            return j + 1
        else:
            j += 1
    raise SettingsError("閉じていない文字列があります")


def skip_value(t, i):
    n = len(t)
    if i >= n:
        raise SettingsError("値がありません")
    if t[i] == '"':
        return skip_string(t, i)
    if t[i] in "{[":
        depth = 0
        while i < n:
            c = t[i]
            if c == '"':
                i = skip_string(t, i)
                continue
            if t.startswith("//", i) or t.startswith("/*", i):
                i = skip_ws_comments(t, i)
                continue
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise SettingsError("閉じていない括弧があります")
    j = i
    while j < n and not t[j].isspace() and t[j] not in ",}]" and not t.startswith("//", j) and not t.startswith("/*", j):
        j += 1
    if j == i:
        raise SettingsError(f"不正な値です (位置 {i})")
    return j


def parse_jsonc(text):
    """コメントと末尾カンマを除去して json.loads する。文字列内の // や /* は触らない。"""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == '"':
            j = skip_string(text, i)
            out.append(text[i:j])
            i = j
        elif text.startswith("//", i) or text.startswith("/*", i):
            i = skip_ws_comments(text, i)
        elif c == ",":
            k = skip_ws_comments(text, i + 1)
            if k < n and text[k] in "}]":
                i += 1  # 末尾カンマ
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return json.loads("".join(out))


# ---------- トップレベルエントリ分割 ----------


class Entry:
    def __init__(self, key, leader, body, after):
        self.key, self.leader, self.body, self.after = key, leader, body, after

    @property
    def head(self):
        return self.leader + self.body


class Layer:
    def __init__(self, entries, tail, pre="", post=""):
        # pre / post は { より前と } より後ろのコメント
        self.entries, self.tail, self.pre, self.post = entries, tail, pre, post


_COMMENT_LINE = re.compile(r"[ \t]*(//.*)?")


def split_layer(text):
    t = text.replace("\r\n", "\n")
    n = len(t)
    i = skip_ws_comments(t, 0)
    if i >= n or t[i] != "{":
        raise SettingsError("先頭が { ではありません")
    pre = t[:i].strip()
    i += 1
    eol = t.find("\n", i)
    pos = eol + 1 if eol >= 0 and t[i:eol].strip() == "" else i
    entries, tail = [], ""
    while True:
        start = pos
        k = skip_ws_comments(t, start)
        if k >= n:
            raise SettingsError("閉じ括弧 } がありません")
        if t[k] == "}":
            tail = t[start:k].strip("\n").rstrip()
            if tail.strip() == "":
                tail = ""
            if skip_ws_comments(t, k + 1) < n:
                raise SettingsError("閉じ括弧 } の後ろにコメント以外があります")
            post = t[k + 1 :].strip()
            break
        if t[k] != '"':
            raise SettingsError(f"キーが文字列ではありません (位置 {k})")
        key_end = skip_string(t, k)
        key = json.loads(t[k:key_end])
        c = skip_ws_comments(t, key_end)
        if c >= n or t[c] != ":":
            raise SettingsError(f"キー {key!r} の後に : がありません")
        vend = skip_value(t, skip_ws_comments(t, c + 1))
        m = skip_ws_comments(t, vend)
        if m >= n or t[m] not in ",}":
            raise SettingsError(f"キー {key!r} の値の後に カンマも閉じ括弧もありません")
        body = t[k:vend]
        # 値とカンマの間のコメントはカンマの後ろへ回す (カンマがコメントに入らないように)
        gap = t[vend:m].strip() if t[m] == "," else ""
        gap = (" " + gap if "\n" not in gap else "\n  " + gap) if gap else ""
        p = m + 1 if t[m] == "," else vend
        eol = t.find("\n", p)
        line = t[p : (n if eol < 0 else eol)]
        if _COMMENT_LINE.fullmatch(line):
            after, pos = line.rstrip(), (n if eol < 0 else eol + 1)
        else:
            after, pos = "", p
        if gap and after:
            after = gap + "\n  " + after.strip()
        else:
            after = gap + after
        entries.append(Entry(key, t[start:k], body, after))
    return Layer(entries, tail, pre, post)


# ---------- 合成・検査 ----------


def render_layers(layers):
    """layers: [Layer]。全層のエントリを連結し、最後のエントリだけカンマ無しにする。"""
    last = max((i for i, ly in enumerate(layers) if ly.entries), default=-1)
    lines = [ly.pre for ly in layers if ly.pre] + ["{"]
    for li, ly in enumerate(layers):
        for ei, e in enumerate(ly.entries):
            is_last = li == last and ei == len(ly.entries) - 1
            lines.append(e.head + ("" if is_last else ",") + e.after)
        if ly.tail:
            lines.append(ly.tail)
    lines.append("}")
    lines += [ly.post for ly in layers if ly.post]
    return "\n".join(lines) + "\n"


def read_layer(path, required=True):
    path = Path(path)
    if not path.exists():
        if required:
            raise SettingsError(f"ファイルが見つかりません: {path}")
        return Layer([], "")
    try:
        return split_layer(path.read_text(encoding="utf-8-sig"))
    except SettingsError as e:
        raise SettingsError(f"{path}: {e}") from None


def profile_files(profile):
    d = ROOT / "profiles" / profile
    if not d.is_dir():
        raise SettingsError(f"プロファイルが見つかりません: {d}")
    return [(SHARED, True), (d / "settings.json", True), (d / "settings.local.json", False)]


def load_layers(profile):
    return [(p, read_layer(p, req)) for p, req in profile_files(profile)]


def find_problems(named_layers):
    problems, seen = [], {}
    for path, ly in named_layers:
        keys = [e.key for e in ly.entries]
        if keys != sorted(keys):
            problems.append(f"ソート違反: {path} (`mise run sort` で修正できます)")
        for k in keys:
            if k in seen:
                where = "同一ファイル内" if seen[k] == path else f"{seen[k]} と"
                problems.append(f"重複キー {k!r}: {path} ({where})")
            else:
                seen[k] = path
    return problems


def render_profile(profile):
    named = load_layers(profile)
    dups = [p for p in find_problems(named) if p.startswith("重複キー")]
    if dups:
        raise SettingsError("\n".join(dups))
    return render_layers([ly for _, ly in named])


def sort_text(text):
    ly = split_layer(text)
    dups = find_problems([("", ly)])
    dups = [p for p in dups if p.startswith("重複キー")]
    if dups:
        raise SettingsError("\n".join(dups))
    ly.entries.sort(key=lambda e: e.key)
    out = render_layers([ly])
    if parse_jsonc(out) != parse_jsonc(text):
        raise SettingsError("ソート結果が元と意味的に一致しません (書き込みを中止)")
    return out


def write_text(path, text):
    # Path.write_text(newline=) は Python 3.10+ のため open を使う
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def diff_dicts(merged, target):
    return (
        sorted(k for k in merged if k not in target),
        sorted(k for k in target if k not in merged),
        sorted(k for k in merged if k in target and merged[k] != target[k]),
    )


# ---------- pull (エディタの変更を各層へ書き戻す) ----------

# 機密判定: 文字列 (キー・値) がどれかに該当したら settings.local.json へ入れる。追加はここへ。
SENSITIVE_PATTERNS = [
    r"cygames",
    r"ochlo",
    r"/Users/",
    r"/home/",
    r"C:[\\/]Users",
    r"AppData",
    r"^~[\\/]",  # ホームディレクトリ形式の絶対パス
    r"https?://[^\"\s]*\.(jp|local|internal|corp)(?![A-Za-z0-9_])",
]
SENSITIVE_KEY_PREFIXES = ("github-enterprise",)
_SENSITIVE_RE = re.compile("|".join(f"(?:{p})" for p in SENSITIVE_PATTERNS), re.IGNORECASE)


def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)
    elif isinstance(v, dict):
        for k, x in v.items():
            yield k
            yield from _strings(x)


def is_sensitive(key, value):
    if key.lower().startswith(SENSITIVE_KEY_PREFIXES):
        return True
    return any(_SENSITIVE_RE.search(s) for s in [key, *_strings(value)])


def _fmt_value(value, indent, multiline):
    """値を JSON 文字列にする。multiline のとき indent=2 相当で、2 行目以降を indent に揃える。"""
    if not multiline:
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False, indent=2).replace("\n", "\n" + indent)


def _replace_value(entry, value):
    body = entry.body
    c = skip_ws_comments(body, skip_string(body, 0))  # ':' の位置
    vstart = skip_ws_comments(body, c + 1)
    old = body[vstart:]
    indent = entry.leader[entry.leader.rfind("\n") + 1 :]
    entry.body = body[:vstart] + _fmt_value(value, indent, "\n" in old)


def _new_entry(key, value):
    one = json.dumps(value, ensure_ascii=False)
    text = one if len(one) <= 60 else _fmt_value(value, "  ", True)
    return Entry(key, "  ", f"{json.dumps(key, ensure_ascii=False)}: {text}", "")


def pull(profile, target_text, dry_run=False, prune=False, to_local=False, now=None):
    """エディタの settings.json を各層へ書き戻す。戻り値は (表示行, {パス: 新テキスト}, バックアップ対象パス)。"""
    named = load_layers(profile)
    dups = [p for p in find_problems(named) if p.startswith("重複キー")]
    if dups:
        raise SettingsError("\n".join(dups))
    layers = [ly for _, ly in named]
    paths = [p for p, _ in named]
    merged = parse_jsonc(render_layers(layers))
    cur = parse_jsonc(target_text)
    owner = {e.key: i for i, ly in enumerate(layers) for e in ly.entries}
    label = lambda i: Path(paths[i]).relative_to(ROOT).as_posix()  # noqa: E731
    report, touched = [], set()

    for k in sorted(k for k in merged if k in cur and merged[k] != cur[k]):
        i = owner[k]
        _replace_value(next(e for e in layers[i].entries if e.key == k), cur[k])
        touched.add(i)
        report.append(f"更新: {label(i)}  {k}")
    for k in sorted(k for k in cur if k not in merged):
        i = 2 if (to_local or is_sensitive(k, cur[k])) else 1
        layers[i].entries.append(_new_entry(k, cur[k]))
        layers[i].entries.sort(key=lambda e: e.key)
        touched.add(i)
        report.append(f"追加: {label(i)}  {k}")
    removed = sorted(k for k in merged if k not in cur)
    for k in removed:
        i = owner[k]
        if prune:
            layers[i].entries = [e for e in layers[i].entries if e.key != k]
            touched.add(i)
            report.append(f"削除: {label(i)}  {k}")
        else:
            report.append(f"削除されたキー (報告のみ。--prune で削除): {label(i)}  {k}")

    texts = {}
    for i in sorted(touched):
        text = render_layers([layers[i]])
        parse_jsonc(text)
        texts[paths[i]] = text
    # pull 後の render が target と意味的に一致すること (報告のみの削除キーは残る前提)
    expected = dict(cur)
    if not prune:
        expected.update({k: merged[k] for k in removed})
    if parse_jsonc(render_layers(layers)) != expected:
        raise SettingsError("pull 後の合成結果が target と一致しません (書き込みを中止)")
    local_path = paths[2]
    backup = local_path if 2 in touched and Path(local_path).exists() else None
    return report, texts, backup


def write_all_atomic(texts):
    tmps = []
    try:
        for path, text in texts.items():
            tmp = f"{path}.tmp-{os.getpid()}"
            tmps.append((tmp, path))
            write_text(tmp, text)
        for tmp, path in tmps:
            os.replace(tmp, path)
    finally:
        for tmp, _ in tmps:
            if os.path.exists(tmp):
                os.remove(tmp)


# ---------- CLI ----------


def cmd_render(a):
    text = render_profile(a.profile)
    parse_jsonc(text)  # 出力が有効な JSONC であることの保証
    if a.output:
        write_text(a.output, text)
    else:
        sys.stdout.buffer.write(text.encode("utf-8"))


def cmd_check(a):
    problems = find_problems(load_layers(a.profile))
    for p in problems:
        print(p, file=sys.stderr)
    if problems:
        return 1
    print(f"OK: {a.profile}")


def backup_file(path):
    """未追跡ファイルを同じディレクトリに .bak-日時 として残す。"""
    shutil.copy2(path, f"{path}.bak-{datetime.now():%Y%m%d%H%M%S}")


def cmd_sort(a):
    # 全ファイルを検証してから、並べ替えが必要なものだけ書く。変更なしのファイルは何も表示しない
    changed = []
    for f in a.files:
        text = Path(f).read_text(encoding="utf-8-sig")
        out = sort_text(text)
        if out != text.replace("\r\n", "\n"):
            changed.append((f, out))
    for f, out in changed:
        if a.dry_run:
            print(f"並べ替えが必要です: {f}")
            continue
        if Path(f).name == "settings.local.json":
            backup_file(f)  # 未追跡で git では戻せない
        write_text(f, out)
        print(f"並べ替えました: {f}")


def cmd_diff(a):
    target = Path(a.target)
    if not target.is_file():
        print(f"対象ファイルがありません: {target}")
        return 1
    merged = parse_jsonc(render_profile(a.profile))
    cur = parse_jsonc(target.read_text(encoding="utf-8-sig"))
    added, removed, changed = diff_dicts(merged, cur)
    for k in added:
        print(f"+ {k}  (合成結果にあり、対象に無い)")
    for k in removed:
        print(f"- {k}  (対象にあり、合成結果に無い)")
    for k in changed:
        print(f"~ {k}  (値が異なる)")
    if not (added or removed or changed):
        print("意味的に同一です")
        return 0
    return 1


def cmd_pull(a):
    target = Path(a.target)
    if not target.is_file():
        raise SettingsError(f"対象ファイルがありません: {target}")
    report, texts, backup = pull(a.profile, target.read_text(encoding="utf-8-sig"), a.dry_run, a.prune, a.local)
    if not report:
        print("差分なし")
        return 0
    prefix = "[dry-run] " if a.dry_run else ""
    for line in report:
        print(prefix + line)
    if a.dry_run:
        return 0
    if not texts:
        print("書き込む変更はありません (報告のみ)")
        return 0
    if backup:
        backup_file(backup)
    write_all_atomic(texts)
    print("書き込み完了")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("render", cmd_render), ("check", cmd_check), ("diff", cmd_diff)):
        sp = sub.add_parser(name)
        sp.add_argument("--profile", required=True)
        if name == "render":
            sp.add_argument("--output")
        if name == "diff":
            sp.add_argument("--target", required=True)
        sp.set_defaults(fn=fn)
    sp = sub.add_parser("pull")
    sp.add_argument("--profile", required=True)
    sp.add_argument("--target", required=True)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--prune", action="store_true")
    sp.add_argument("--local", action="store_true")
    sp.set_defaults(fn=cmd_pull)
    sp = sub.add_parser("sort")
    sp.add_argument("files", nargs="+")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(fn=cmd_sort)
    a = ap.parse_args(argv)
    try:
        return a.fn(a) or 0
    except (SettingsError, json.JSONDecodeError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
