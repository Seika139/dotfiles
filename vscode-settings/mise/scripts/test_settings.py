#!/usr/bin/env python3
"""settings.py のテスト。 `python mise/scripts/test_settings.py` で実行する。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import settings as S  # noqa: E402


def keys(text):
    return [e.key for e in S.split_layer(text).entries]


# コメント内の // と、文字列内の // や /*
text = """{
  // url: http://example.com/*
  "a": "http://x/*y*/", // 行末コメント
  /* block "b": 1 */
  "b": [1, 2,],
}
"""
assert S.parse_jsonc(text) == {"a": "http://x/*y*/", "b": [1, 2]}
assert keys(text) == ["a", "b"]

# 末尾カンマと入れ子 (入れ子の中身はキー扱いしない)
assert keys('{"z": {"inner": 1,}, "a": 2,}') == ["z", "a"]

# ソートはリーダーコメントごと動き、ソート後も同じ内容
src = '{\n  // for b\n  "b": 1,\n\n  // for a\n  "a": {"x": 2}, // tail a\n  // end\n}\n'
out = S.sort_text(src)
assert out == '{\n\n  // for a\n  "a": {"x": 2}, // tail a\n  // for b\n  "b": 1\n  // end\n}\n', out
assert S.parse_jsonc(out) == S.parse_jsonc(src)
assert S.sort_text(out) == out

# マージ時のカンマ: 層の最後のエントリにもカンマが付き、全体の最後だけ付かない
l1 = S.split_layer('{\n  "a": 1\n}')
l2 = S.split_layer('{\n  "b": 2, // c\n}')
l3 = S.split_layer("{\n}")
merged = S.render_layers([l1, l2, l3])
assert merged == '{\n  "a": 1,\n  "b": 2 // c\n}\n', merged
assert S.parse_jsonc(merged) == {"a": 1, "b": 2}
assert S.render_layers([l3, l3]) == "{\n}\n"

# 重複キー検出 (層をまたぐ / 同一ファイル内) とソート違反検出
p = Path("x")
dup = S.find_problems([(p, S.split_layer('{"a": 1}')), (Path("y"), S.split_layer('{"a": 2}'))])
assert len(dup) == 1 and dup[0].startswith("重複キー")
assert any(s.startswith("重複キー") for s in S.find_problems([(p, S.split_layer('{"a": 1, "a": 2}'))]))
unsorted_ = S.find_problems([(p, S.split_layer('{"b": 1, "a": 2}'))])
assert len(unsorted_) == 1 and unsorted_[0].startswith("ソート違反")
assert S.find_problems([(p, S.split_layer('{"a": 1, "b": 2}'))]) == []

# 差分は意味的 (コメント・順序は無視)
a = S.parse_jsonc('{"a": 1, "b": 2, "c": 3}')
b = S.parse_jsonc('// c\n{"c": 3, "b": 9, "d": 4}')
assert S.diff_dicts(a, b) == (["a"], ["d"], ["b"])

# 値とカンマの間の行コメントでカンマがコメントに入らない
gap = '{\n  "a": 1 // c\n  , "b": 2\n}\n'
r = S.render_layers([S.split_layer(gap)])
assert S.parse_jsonc(r) == {"a": 1, "b": 2}, r
assert S.parse_jsonc(S.sort_text(gap)) == {"a": 1, "b": 2}
gap2 = '{\n  "b": 2 // c\n  , // d\n  "a": 1\n}\n'
assert S.parse_jsonc(S.sort_text(gap2)) == {"a": 1, "b": 2}

# { の前と } の後ろのコメントは sort で保持される。} の後ろのコメント以外はエラー
pp = "// 前\n{\n  \"b\": 1,\n  \"a\": 2\n}\n// 後\n"
out = S.sort_text(pp)
assert out.startswith("// 前\n{") and out.endswith("}\n// 後\n"), out
try:
    S.split_layer('{"a": 1} x')
    raise AssertionError("} の後ろのゴミを検出できていない")
except S.SettingsError:
    pass


# ---------- pull ----------
import contextlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import tempfile  # noqa: E402

SHARED_TXT = '{\n  "a.shared": 1,\n  "z.shared": [1, 2]\n}\n'
PROFILE_TXT = """{
  // note for b
  "b.key": "old", // trail
  "c.multi": {
    "x": 1
  },
  "d.removed": true
}
"""
BASE = {"a.shared": 1, "z.shared": [1, 2], "b.key": "old", "c.multi": {"x": 1}, "d.removed": True}


def fixture(local_txt=None):
    tmp = Path(tempfile.mkdtemp())
    (tmp / "shared").mkdir()
    (tmp / "profiles" / "p").mkdir(parents=True)
    (tmp / "shared" / "settings.json").write_text(SHARED_TXT, encoding="utf-8")
    (tmp / "profiles" / "p" / "settings.json").write_text(PROFILE_TXT, encoding="utf-8")
    if local_txt is not None:
        (tmp / "profiles" / "p" / "settings.local.json").write_text(local_txt, encoding="utf-8")
    S.ROOT, S.SHARED = tmp, tmp / "shared" / "settings.json"
    return tmp


def run_pull(tmp, target, *flags):
    t = tmp / "editor.json"
    t.write_text(json.dumps(target), encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = S.main(["pull", "--profile", "p", "--target", str(t), *flags])
    return rc, buf.getvalue()


def layer_text(tmp, name="settings.json"):
    return (tmp / "profiles" / "p" / name).read_text(encoding="utf-8")


def merged_equals(tmp, target):
    return S.parse_jsonc(S.render_profile("p")) == target


# 既存キーの値変更: コメント・キー行を保持。shared のキーはその層で更新される
tmp = fixture()
tgt = {**BASE, "b.key": "new", "a.shared": 2}
rc, out = run_pull(tmp, tgt)
assert rc == 0 and merged_equals(tmp, tgt), out
assert '// note for b\n  "b.key": "new", // trail' in layer_text(tmp), layer_text(tmp)
assert '"a.shared": 2' in (tmp / "shared" / "settings.json").read_text(encoding="utf-8")
assert "更新" in out and "shared/settings.json" in out and "new" not in out.replace("更新", "")

# 複数行の値の置換 (インデントはエントリに合わせる)
tmp = fixture()
tgt = {**BASE, "c.multi": {"x": 1, "y": [2]}}
rc, out = run_pull(tmp, tgt)
assert merged_equals(tmp, tgt)
assert '  "c.multi": {\n    "x": 1,\n    "y": [\n      2\n    ]\n  },' in layer_text(tmp), layer_text(tmp)

# 新規キーは profile に入り、昇順の位置に挿入される。値は表示されない
tmp = fixture()
tgt = {**BASE, "c.new": "VALUE_SECRET_X", "0.first": 1}
rc, out = run_pull(tmp, tgt)
assert merged_equals(tmp, tgt)
ks = [e.key for e in S.split_layer(layer_text(tmp)).entries]
assert ks == sorted(ks) and "c.new" in ks and ks[0] == "0.first", ks
assert "VALUE_SECRET_X" not in out and "追加" in out and not (tmp / "profiles/p/settings.local.json").exists()

# 機密キーは local に入る (local 無しから作成、バックアップ無し)。2 回目は local のバックアップを残す
tmp = fixture()
tgt = {**BASE, "x.path": "/Users/someone/a", "github-enterprise.foo": 1, "y.url": ["https://corp.example.jp/x"], "plain": 1}
rc, out = run_pull(tmp, tgt)
assert merged_equals(tmp, tgt)
lk = [e.key for e in S.split_layer(layer_text(tmp, "settings.local.json")).entries]
assert lk == ["github-enterprise.foo", "x.path", "y.url"], lk
assert "plain" in layer_text(tmp) and "someone" not in out
assert not list((tmp / "profiles/p").glob("settings.local.json.bak-*"))
tgt2 = {**tgt, "x.path": "/Users/other/b"}
rc, out = run_pull(tmp, tgt2)
assert merged_equals(tmp, tgt2) and len(list((tmp / "profiles/p").glob("settings.local.json.bak-*"))) == 1

# 誤判定しない: .jpg や ${userHome} は機密ではない
assert not S.is_sensitive("k", "https://example.com/a.jpg") and not S.is_sensitive("k", "${userHome}/x")
assert S.is_sensitive("k", "~/foo") and S.is_sensitive("k", "C:\\Users\\a") and S.is_sensitive("OCHLO", 1)

# --local は非機密キーも local に入れる
tmp = fixture()
tgt = {**BASE, "plain": 1}
rc, out = run_pull(tmp, tgt, "--local")
assert merged_equals(tmp, tgt) and '"plain"' in layer_text(tmp, "settings.local.json") and '"plain"' not in layer_text(tmp)

# 削除は報告のみ。--prune でリーダーコメントごと削除
tmp = fixture()
tgt = {k: v for k, v in BASE.items() if k != "b.key"}
before = layer_text(tmp)
rc, out = run_pull(tmp, tgt)
assert rc == 0 and "b.key" in out and layer_text(tmp) == before
rc, out = run_pull(tmp, tgt, "--prune")
assert merged_equals(tmp, tgt) and "note for b" not in layer_text(tmp) and "// trail" not in layer_text(tmp)

# 変更なし / dry-run は書かない
tmp = fixture()
rc, out = run_pull(tmp, BASE)
assert "差分なし" in out and layer_text(tmp) == PROFILE_TXT
rc, out = run_pull(tmp, {**BASE, "b.key": "n", "new.k": 1, "x": "/home/u"}, "--dry-run", "--prune")
assert "dry-run" in out and layer_text(tmp) == PROFILE_TXT and not (tmp / "profiles/p/settings.local.json").exists()

# 重複キーがあれば中断して何も書かない
tmp = fixture()
(tmp / "profiles/p/settings.local.json").write_text('{"b.key": 1}\n', encoding="utf-8")
rc, out = run_pull(tmp, {**BASE, "q": 1})
assert rc == 2 and "重複キー" in out and layer_text(tmp) == PROFILE_TXT

# sort --dry-run: 並べ替えが必要なファイルだけを表示し、何も書かない。通常実行は変更があるものだけ書き、local はバックアップを残す
tmp = fixture()
unsorted_txt = '{\n  "b": 1,\n  "a": 2\n}\n'
sorted_txt = '{\n  "a": 1,\n  "b": 2\n}\n'
f_un, f_ok = tmp / "profiles/p/settings.local.json", tmp / "shared/settings.json"
f_un.write_text(unsorted_txt, encoding="utf-8")
f_ok.write_text(sorted_txt, encoding="utf-8")
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    assert S.main(["sort", "--dry-run", str(f_un), str(f_ok)]) == 0
assert str(f_un) in buf.getvalue() and str(f_ok) not in buf.getvalue()
assert f_un.read_text(encoding="utf-8") == unsorted_txt and not list(f_un.parent.glob("*.bak-*"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    assert S.main(["sort", str(f_un), str(f_ok)]) == 0
assert "並べ替えました" in buf.getvalue() and str(f_ok) not in buf.getvalue()
assert f_un.read_text(encoding="utf-8") == '{\n  "a": 2,\n  "b": 1\n}\n'
assert len(list(f_un.parent.glob("settings.local.json.bak-*"))) == 1
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    S.main(["sort", "--dry-run", str(f_un), str(f_ok)])
assert buf.getvalue() == ""

print("OK")
