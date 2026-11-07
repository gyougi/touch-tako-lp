#!/usr/bin/env python3
"""頁の中の「GLSPACE」（会社名）の頭に、会社の標志を付ける。

付ける所は二つだけ:
  ① 版権の行        「© 2026 GLSPACE 株式会社」→「© 2026 ［標志］GLSPACE 株式会社」
  ② 会社サイトへのリンクで、字が「GLSPACE」だけのもの（裾の「GLSPACE」）

⚠️ **頁の「字」にだけ手を入れる。** タグの属性（content="© … GLSPACE"）、<script>
   （JSON-LD にも「© … GLSPACE」が出る）、<style>、コメントは触らない。
   触ると属性の中に <svg> が入って頁が壊れる。
⚠️ **何度流しても同じ結果**（生成器が毎回呼ぶ）。すでに標志があるリンクには付けない。
⚠️ 標志は glspace.co.jp 本体と同じ形。描線は `currentColor`（文字の色に従う）、
   大きさは `em`（文字と一緒に伸び縮み）なので、站ごとの CSS は要らない。
   頂点の点だけ会社の緑 #A0BF3F。

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
_LINK_OPEN = re.compile(r'<a\b[^>]*\bhref="https?://glspace\.co\.jp/?(?:[#?][^"]*)?"[^>]*>', re.I)


def add_company_mark(page):
    out = []
    in_link = False          # 会社サイトへのリンクを開いた直後（最初の中身を待っている）
    for tok in _TOKEN.split(page):
        if not tok:
            continue
        if tok.startswith("<") and _TOKEN.fullmatch(tok):
            if _LINK_OPEN.fullmatch(tok):
                in_link = True
            else:
                in_link = False   # </a> でも、最初の子が <svg> 等でも、待ちをやめる
            out.append(tok)
            continue
        if _TOKEN.fullmatch(tok):  # script / style / コメント
            out.append(tok)
            continue
        # ── ここからが「字」
        if in_link:
            in_link = False
            core = tok.strip()
            if core == "GLSPACE":
                lead = tok[:len(tok) - len(tok.lstrip())]
                tok = lead + MARK + tok.lstrip()
        tok = _COPY.sub(lambda m: m.group(1) + m.group(2) + MARK + m.group(3), tok)
        out.append(tok)
    return "".join(out)


def _self_test():
    cases = []

    def expect(name, src, check):
        got = add_company_mark(src)
        ok = check(got, src)
        cases.append((name, ok, got))

    n = lambda s: s.count('class="co-mark"')
    expect("版権（日本語）", "<p>© 2026 GLSPACE 株式会社</p>",
           lambda g, s: g == "<p>© 2026 " + MARK + "GLSPACE 株式会社</p>")
    expect("版権（英語）", "<p>© 2026 GLSPACE Co., Ltd.</p>",
           lambda g, s: g == "<p>© 2026 " + MARK + "GLSPACE Co., Ltd.</p>")
    expect("&copy; の書き方", "<p>&copy; 2026 GLSPACE</p>", lambda g, s: n(g) == 1)
    expect("会社リンクの「GLSPACE」", '<a href="https://glspace.co.jp/">GLSPACE</a>',
           lambda g, s: g == '<a href="https://glspace.co.jp/">' + MARK + "GLSPACE</a>")
    expect("target 付きのリンク", '<a href="https://glspace.co.jp/" target="_blank" rel="noopener">GLSPACE</a>',
           lambda g, s: n(g) == 1)
    expect("すでに標志があるリンクには付けない",
           '<a href="https://glspace.co.jp/"><svg class="gl-mark"></svg>GLSPACE</a>',
           lambda g, s: g == s)
    expect("別のサイトへのリンクには付けない", '<a href="https://example.com/">GLSPACE</a>',
           lambda g, s: g == s)
    expect("字が長いリンクには付けない", '<a href="https://glspace.co.jp/">GLSPACE について</a>',
           lambda g, s: g == s)
    expect("文中の GLSPACE には付けない", "<p>GLSPACE の App を作っています。</p>",
           lambda g, s: g == s)
    expect("属性の中は触らない", '<meta name="copyright" content="© 2026 GLSPACE 株式会社">',
           lambda g, s: g == s)
    expect("<script>（JSON-LD）の中は触らない",
           '<script type="application/ld+json">{"name":"© 2026 GLSPACE"}</script>',
           lambda g, s: g == s)
    expect("<style> の中は触らない", "<style>a::after{content:'© 2026 GLSPACE'}</style>",
           lambda g, s: g == s)
    both = '<footer><a href="https://glspace.co.jp/">GLSPACE</a><p>© 2026 GLSPACE 株式会社</p></footer>'
    expect("リンクと版権の両方", both, lambda g, s: n(g) == 2)
    expect("二度流しても同じ（冪等）", both,
           lambda g, s: add_company_mark(g) == g and n(add_company_mark(g)) == 2)
    # 対照：標志を付ける処理が本当に動いていること（何も変えない実装だと上の「触らない」系が全部通ってしまう）
    expect("【対照】何かは変わる", "<p>© 2026 GLSPACE 株式会社</p>", lambda g, s: g != s)

    bad = [(nm, got) for nm, ok, got in cases if not ok]
    print("会社標志の対照組 %d 件" % len(cases))
    for nm, ok, _ in cases:
        print("  %s %s" % ("・" if ok else "✗", nm))
    if bad:
        for nm, got in bad:
            print("\n  ✗ %s\n    %s" % (nm, got[:200]))
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
