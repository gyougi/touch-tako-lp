#!/usr/bin/env python3
"""頁の中の「GLSPACE」（会社名）の頭に、会社の標志を付ける。

**一つの頁に標志は一か所だけ**（2026-11-07 本人の指示：同じ画面に二つ出ない）。
  ① 頁に「会社サイトへのリンクで、字が GLSPACE だけのもの」があれば、**そのリンク**に付ける。
     版権の行は素のまま。
  ② そういうリンクが無い頁（主に法務の頁）は、**版権の行**に付ける
     「© 2026 GLSPACE 株式会社」→「© 2026 ［標志］GLSPACE 株式会社」。
  どちらの形に変わる場合でも、前の形の標志は取り除く（何度流しても同じ結果＝冪等）。

⚠️ **頁の「字」にだけ手を入れる。** タグの属性（content="© … GLSPACE"）、<script>
   （JSON-LD にも「© … GLSPACE」が出る）、<style>、コメントは触らない。
   触ると属性の中に <svg> が入って頁が壊れる。
⚠️ 標志は glspace.co.jp 本体と同じ形。描線は `currentColor`（文字の色に従う）、
   大きさは `em`（文字と一緒に伸び縮み）なので、站ごとの CSS は要らない。
   頂点の点だけ会社の緑 #A0BF3F。
⚠️ すでに自前の標志（`gl-mark`）が付いているリンクは**そのまま**数える（二重に付けない）。

使い方:
  生成器から   from company_mark import add_company_mark ; page = add_company_mark(page)
  生成していない頁に   python3 company_mark.py 頁.html ...        （その場で書き換える）
                      python3 company_mark.py --check 頁.html ...  （変わる頁を挙げるだけ）
  対照組        python3 company_mark.py --self-test
"""
import io
import re
import sys

MARK = ('<svg class="co-mark" viewBox="0 0 64 64" fill="none" aria-hidden="true" focusable="false" '
        'style="width:1.15em;height:1.15em;vertical-align:-.24em;margin-right:.4em">'
        '<polygon points="32,3 57,17.5 57,46.5 32,61 7,46.5 7,17.5" stroke="currentColor" '
        'stroke-width="4" stroke-linejoin="round"/>'
        '<polyline points="12,45 22,34 28,41 32,25 36,41 42,34 52,45" stroke="currentColor" '
        'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="32" cy="25" r="2.2" fill="#A0BF3F"/></svg>')

# 字ではない塊（これらの中は触らない）と、タグ
_TOKEN = re.compile(r'(<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<[^>]+>)',
                    re.S | re.I)
_COPY = re.compile(r'(©|&copy;)(\s*20\d\d\s*)(GLSPACE)')
# 版権の行についた標志（前の形）。自分が付けた形（MARK そのまま）だけを外す
_COPY_MARKED = re.compile(r'(©|&copy;)(\s*20\d\d\s*)' + re.escape(MARK) + r'(?=GLSPACE)')
_LINK_OPEN = re.compile(r'<a\b[^>]*\bhref="https?://glspace\.co\.jp/?(?:[#?][^"]*)?"[^>]*>', re.I)


def _mark_links(page):
    """会社リンク（字が GLSPACE だけ）に標志を付ける。戻り値: (頁, 標志付きの会社リンクがあるか)"""
    out = []
    in_link = False          # 会社サイトへのリンクを開いた直後（最初の中身を待っている）
    has_marked = False
    for tok in _TOKEN.split(page):
        if not tok:
            continue
        if _TOKEN.fullmatch(tok):
            if tok.startswith("<") and not re.match(r"<(script|style|!--)", tok, re.I):
                if _LINK_OPEN.fullmatch(tok):
                    in_link = True
                else:
                    if in_link and tok.lower().startswith("<svg"):
                        has_marked = True     # 最初の子が <svg>＝すでに標志が付いたリンク
                    in_link = False
            out.append(tok)
            continue
        if in_link:
            in_link = False
            if tok.strip() == "GLSPACE":
                lead = tok[:len(tok) - len(tok.lstrip())]
                tok = lead + MARK + tok.lstrip()
                has_marked = True
        out.append(tok)
    return "".join(out), has_marked


def _mark_copyright(page):
    """版権の行（字）に標志を付ける。<script>・<style>・属性・コメントは触らない。"""
    out = []
    for tok in _TOKEN.split(page):
        if tok and not _TOKEN.fullmatch(tok):
            tok = _COPY.sub(lambda m: m.group(1) + m.group(2) + MARK + m.group(3), tok)
        out.append(tok)
    return "".join(out)


def add_company_mark(page):
    page, has_link = _mark_links(page)
    # いったん版権の行の標志を外してから、要る頁にだけ付け直す（形が変わっても冪等）
    page = _COPY_MARKED.sub(lambda m: m.group(1) + m.group(2), page)
    if not has_link:
        page = _mark_copyright(page)
    return page


def _self_test():
    cases = []

    def expect(name, src, check):
        got = add_company_mark(src)
        cases.append((name, check(got, src), got))

    n = lambda s: s.count('class="co-mark"')
    LINK = '<a href="https://glspace.co.jp/">GLSPACE</a>'
    OLD = '<a href="https://glspace.co.jp/"><svg class="gl-mark"></svg>GLSPACE</a>'
    CP = "<p>© 2026 GLSPACE 株式会社</p>"
    expect("リンクが無い頁：版権に付く（日本語）", CP,
           lambda g, s: g == "<p>© 2026 " + MARK + "GLSPACE 株式会社</p>")
    expect("リンクが無い頁：版権に付く（英語）", "<p>© 2026 GLSPACE Co., Ltd.</p>",
           lambda g, s: g == "<p>© 2026 " + MARK + "GLSPACE Co., Ltd.</p>")
    expect("リンクが無い頁：&copy; の書き方", "<p>&copy; 2026 GLSPACE</p>", lambda g, s: n(g) == 1)
    expect("リンクがある頁：リンクにだけ付き、版権は素のまま", LINK + CP,
           lambda g, s: g == '<a href="https://glspace.co.jp/">' + MARK + "GLSPACE</a>" + CP)
    expect("リンクが版権より後ろでも同じ", CP + LINK,
           lambda g, s: n(g) == 1 and "© 2026 GLSPACE 株式会社" in g)
    expect("target 付きのリンク", '<a href="https://glspace.co.jp/" target="_blank" rel="noopener">GLSPACE</a>' + CP,
           lambda g, s: n(g) == 1 and "© 2026 GLSPACE" in g)
    expect("すでに自前の標志があるリンク：何も足さない", OLD + CP, lambda g, s: g == s)
    expect("【掃除】前の形（リンクにも版権にも標志）→ 版権の標志が外れる",
           LINK.replace(">GLSPACE<", ">" + MARK + "GLSPACE<") + "<p>© 2026 " + MARK + "GLSPACE 株式会社</p>",
           lambda g, s: n(g) == 1 and "© 2026 GLSPACE 株式会社" in g)
    expect("【掃除】自前の標志のリンク＋版権の標志 → 版権の標志が外れる",
           OLD + "<p>© 2026 " + MARK + "GLSPACE 株式会社</p>",
           lambda g, s: g == OLD + CP)
    expect("別のサイトへのリンクはリンクと数えない（版権に付く）", '<a href="https://example.com/">GLSPACE</a>' + CP,
           lambda g, s: n(g) == 1 and "© 2026 " + MARK in g)
    expect("字が長いリンクはリンクと数えない（版権に付く）", '<a href="https://glspace.co.jp/">GLSPACE について</a>' + CP,
           lambda g, s: n(g) == 1 and "© 2026 " + MARK in g)
    expect("文中の GLSPACE には付けない", "<p>GLSPACE の App を作っています。</p>", lambda g, s: g == s)
    expect("属性の中は触らない", '<meta name="copyright" content="© 2026 GLSPACE 株式会社">',
           lambda g, s: g == s)
    expect("<script>（JSON-LD）の中は触らない",
           '<script type="application/ld+json">{"name":"© 2026 GLSPACE"}</script>',
           lambda g, s: g == s)
    expect("<style> の中は触らない", "<style>a::after{content:'© 2026 GLSPACE'}</style>",
           lambda g, s: g == s)
    expect("一頁に標志は一つだけ（リンク＋版権）", LINK + CP, lambda g, s: n(g) == 1)
    expect("一頁に標志は一つだけ（版権が複数＝言語区塊）", CP + CP + CP, lambda g, s: n(g) == 3)
    expect("二度流しても同じ（冪等・リンクあり）", LINK + CP,
           lambda g, s: add_company_mark(g) == g)
    expect("二度流しても同じ（冪等・リンクなし）", CP,
           lambda g, s: add_company_mark(g) == g)
    expect("【対照】何かは変わる", CP, lambda g, s: g != s)

    bad = [(nm, got) for nm, ok, got in cases if not ok]
    print("会社標志の対照組 %d 件" % len(cases))
    for nm, ok, _ in cases:
        print("  %s %s" % ("・" if ok else "✗", nm))
    if bad:
        for nm, got in bad:
            print("\n  ✗ %s\n    %s" % (nm, got[:240]))
        return "対照組 %d 件が期待どおりに動かない" % len(bad)
    print("  → %d 件すべて期待どおり" % len(cases))
    return 0


def main(argv):
    if "--self-test" in argv:
        return _self_test()
    check = "--check" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__)
        return 0
    changed = 0
    for path in files:
        src = io.open(path, encoding="utf-8").read()
        new = add_company_mark(src)
        if new != src:
            changed += 1
            print(("要変更 " if check else "書いた ") + path)
            if not check:
                io.open(path, "w", encoding="utf-8").write(new)
    print("%d / %d 頁が変わる" % (changed, len(files)) if check else "%d / %d 頁を書き換えた" % (changed, len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
