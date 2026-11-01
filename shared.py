#!/usr/bin/env python3
"""站の全体で一つにしておく事実。**ここが正本。**

⚠️⚠️ **連絡先を二か所に書かない。** 2026-11-01 に `support@` から `contact@` へ
   移したとき、一つの站の中で同じ住所が**四か所から六か所**に散っていた
   ── 首頁の裾（素の字）、`build.py` の JSON-LD、法務三頁、README。
   どれか一つを直し忘れても**頁はどちらも普通に出る**ので、字面でも検査でも
   分からない。間違いに気づけるのは「送ったのに返事が来ない」と誰かが
   言ってくれた時だけで、その人はもう二度と書いてこない。

   → 頁の中では `{{MAIL}}`（法務の雛形では `{MAIL}`）と書いて、ここから埋める。
     生成していない頁は `check_mail_matches` で**正本と違えば止める**。

対照組:  python3 shared.py --self-test
"""
import io
import os
import re
import sys

CONTACT_MAIL = "contact@glspace.co.jp"

# 裾の「お問い合わせ」の標。站が持っている言語のぶんだけ使う。
CONTACT_LABEL = {"ja": "お問い合わせ", "en": "Contact",
                 "zh": "联系我们", "zh-hant": "聯絡我們"}

# 站ごとに綴りが違う。`tw`・`zhHant`・`zh-hant` が同じものを指す站が在る。
# ⚠️⚠️ **知らない綴りを黙って英語に落とさない。** 2026-11-01 に glspace-apps の
#    鍵が `zhHant` で、この表に無かったため**繁體の頁に "Contact" が出た**。
#    頁は普通に出るし検査も通る ── 気づいたのは 375px で四言語を測った時だけ。
#    → 知らない綴りは **止める**。英語で良い言語は站側で名指しすること。
_ALIAS = {"tw": "zh-hant", "zh-Hant": "zh-hant", "zh-TW": "zh-hant",
          "zhHant": "zh-hant", "zh_Hant": "zh-hant", "hant": "zh-hant",
          "zh-Hans": "zh", "zh-CN": "zh", "zhHans": "zh", "hans": "zh",
          "jp": "ja", "ja-JP": "ja", "en-US": "en", "en-GB": "en"}


def contact_label(lang, english_ok=()):
    """その言語の「お問い合わせ」の標。

    日英簡繁の四つしか訳が無い。それ以外の言語（nazoru の vi / ne / ko など）で
    英語の "Contact" を出してよいなら、**站側で `english_ok` に名指しする**。
    名指しの無い綴りは止める ── 繁體の頁に英語が出たのを黙って通さないため。
    """
    key = _ALIAS.get(lang, lang)
    if key in CONTACT_LABEL:
        return CONTACT_LABEL[key]
    if lang in english_ok or key in english_ok:
        return CONTACT_LABEL["en"]
    sys.exit('「お問い合わせ」の標が無い言語: %r（正規化後 %r）\n'
             '    日英簡繁なら shared.py の _ALIAS に綴りを足す。\n'
             '    英語の "Contact" で良い言語なら、build.py で\n'
             '    contact_label(lang, english_ok=(...)) と名指しする。' % (lang, key))


def check_mail_in_one_place(sources):
    """連絡先が**素の字で**書かれていないか。正本はこのファイル一か所。

    `sources` は {名前: 中身} の表（対照組から偽の中身を渡すため）。
    """
    # ⚠️ 空振り防止。見る源が一つも無いまま「見つからなかった」で通すと、
    #    綴りが変わった日に**何も見ずに緑**になる。
    if not sources:
        sys.exit("連絡先を探す源が一つも無い ── 検査が空振りする")
    host = CONTACT_MAIL.partition("@")[2]
    bad = []
    for name, text in sources.items():
        for found in re.finditer(r"[A-Za-z0-9._%+-]+@" + re.escape(host), text):
            bad.append("%s: %s" % (name, found.group(0)))
    if bad:
        sys.exit("源に素の連絡先が書かれている（正本は shared.py の "
                 "CONTACT_MAIL 一か所）:\n    %s\n"
                 "    頁の中では {{MAIL}} と書くこと。" % "\n    ".join(bad))


def check_mail_matches(sources):
    """手で書いた頁（生成していない法務頁など）の住所が、正本と同じか。

    ⚠️⚠️ 生成していない頁では `{{MAIL}}` が埋まらないので素の字で書くしかない。
       そこを**検査の外に置くと、正本を変えた日にその頁だけ古いまま残る**。
       頁は普通に出るし字面でも分からない ── 気づけるのは返事が来ない時だけ。
       だから「一か所に集める」ではなく「**違っていたら止まる**」で縛る。
    """
    if not sources:
        sys.exit("照合する頁が一つも無い ── 検査が空振りする")
    host = CONTACT_MAIL.partition("@")[2]
    bad, found = [], 0
    for name, text in sources.items():
        hits = re.findall(r"[A-Za-z0-9._%+-]+@" + re.escape(host), text)
        if not hits:
            sys.exit("%s に連絡先が一つも無い ── 頁が変わったのか、名簿が古い" % name)
        found += len(hits)
        for h in sorted(set(hits)):
            if h != CONTACT_MAIL:
                bad.append("%s: %s" % (name, h))
    if bad:
        sys.exit("手で書いた頁の連絡先が正本と違う（正本は shared.py の "
                 "CONTACT_MAIL）:\n    %s" % "\n    ".join(bad))
    return found


def src_sources(root, subdir="src", exts=(".html", ".js", ".json")):
    """`src/` の中の源をぜんぶ読んで {名前: 中身} で返す。

    ⚠️ 名簿を手で書かない。書くと**後から足した源が検査の視界に入らず**、
       そこに素の住所を書いた日に何も言わずに通る。
    ⚠️ 置き場が無ければ止める（空振り防止）。
    """
    base = os.path.join(root, subdir)
    if not os.path.isdir(base):
        sys.exit("源の置き場が無い: %s ── 検査が空振りする" % base)
    out = {}
    for dirpath, _, files in os.walk(base):
        for name in sorted(files):
            if name.endswith(exts):
                full = os.path.join(dirpath, name)
                out[os.path.relpath(full, root)] = io.open(full, encoding="utf-8").read()
    if not out:
        sys.exit("%s に源が一つも無い ── 検査が空振りする" % base)
    return out


def file_sources(root, names):
    """名指しの頁を読む。一つでも無ければ止める。

    ⚠️ **名簿が空振りしたら止める。** 頁の名が変わった時に「無いから見ない」で
       通すと、その頁だけ古い住所のまま誰も気づかない。
    """
    if not names:
        sys.exit("照合する頁の名簿が空 ── 検査が空振りする")
    out = {}
    for name in names:
        full = os.path.join(root, name)
        if not os.path.exists(full):
            sys.exit("照合する頁が無い: %s ── 名簿が古いか、頁が移った" % name)
        out[name] = io.open(full, encoding="utf-8").read()
    return out


def _self_test():
    """検査が**本当に赤くなる**か。壊した源を渡して、止まることを確かめる。"""
    host = CONTACT_MAIL.partition("@")[2]
    src_cases = (
        ("住所は {{MAIL}} 越し（通るはず）",
         {"a": '<a href="mailto:{{MAIL}}">{{MAIL}}</a>'}, None),
        ("裾に素の住所を書いた",
         {"a": '<div class="mail">%s</div>' % CONTACT_MAIL}, CONTACT_MAIL),
        ("古い住所が残っている", {"a": "support@" + host}, "support@"),
        ("文案の中に紛れている",
         {"a": "x", "i18n": "ご連絡は hello@%s へ" % host}, "hello@"),
        ("見る源が無い（空振り）", {}, "空振り"),
    )
    match_cases = (
        ("正本と同じ住所（通るはず）", {"a": "<a>%s</a>" % CONTACT_MAIL}, None),
        ("古い住所が残っている", {"a": "<a>support@%s</a>" % host}, "support@"),
        ("住所が一つも無い", {"a": "<p>連絡先の節が消えた</p>"}, "一つも無い"),
        ("見る頁が無い（空振り）", {}, "空振り"),
    )
    label_cases = (
        ("ja は日本語", lambda: contact_label("ja"), "お問い合わせ"),
        ("tw は繁體", lambda: contact_label("tw"), "聯絡我們"),
        ("zhHant も繁體", lambda: contact_label("zhHant"), "聯絡我們"),
        ("知らない綴りは止まる", lambda: contact_label("xx-YY"), None),
        ("名指しすれば英語", lambda: contact_label("ko", english_ok=("ko",)), "Contact"),
    )
    failures = []
    for label, fn, cases in (("源", check_mail_in_one_place, src_cases),
                             ("照合", check_mail_matches, match_cases)):
        for name, src, wanted in cases:
            caught = None
            try:
                fn(src)
            except SystemExit as stop:
                caught = str(stop)
            if wanted is None:
                if caught is not None:
                    failures.append("%s／%s: 通るはずが止まった\n    %s" % (label, name, caught))
            elif caught is None:
                failures.append("%s／%s: 壊したのに通った" % (label, name))
            elif wanted not in caught:
                failures.append("%s／%s: 止まったが別の理由らしい（「%s」が出ていない）"
                                "\n    %s" % (label, name, wanted, caught))
    for name, call, wanted in label_cases:
        got, caught = None, None
        try:
            got = call()
        except SystemExit as stop:
            caught = str(stop)
        if wanted is None:
            if caught is None:
                failures.append("標／%s: 止まるはずが %r を返した" % (name, got))
        elif caught is not None:
            failures.append("標／%s: 通るはずが止まった\n    %s" % (name, caught))
        elif got != wanted:
            failures.append("標／%s: %r のはずが %r" % (name, wanted, got))

    allc = ([("源／" + n) for n, _, _ in src_cases]
            + [("照合／" + n) for n, _, _ in match_cases]
            + [("標／" + n) for n, _, _ in label_cases])
    print("連絡先の対照組 %d 件" % len(allc))
    for name in allc:
        print("  ・%s" % name)
    if failures:
        print()
        for f in failures:
            print("  ✗ " + f)
        return "対照組 %d 件が期待どおりに動かない" % len(failures)
    print("  → %d 件すべて期待どおり" % len(allc))
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(CONTACT_MAIL)
