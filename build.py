#!/usr/bin/env python3
"""多语言静态页面生成器。

唯一正本是 src/index.html（结构）和 src/i18n.js（文案）。改完任意一个都要跑：

    python3 build.py

生成各语言的静态页面和 sitemap.xml。根目录的产物不要手改，下次 build 会覆盖。

这份脚本在 GLSPACE 的几个 LP 之间通用，站与站的差异全在下面 CONFIG 里。
"""
import html
import json
import os
import re
import subprocess
import sys

# ─────────────────────────── 本站配置 ───────────────────────────
SITE = "https://touchtako.glspace.co.jp"
APP_NAME = "Touch Tako"
APPSTORE = "https://apps.apple.com/app/id6782324502"
ORG = "GLSPACE Co., Ltd."
SUPPORT_MAIL = "support@glspace.co.jp"
OG_IMAGE = SITE + "/icon.png"
APP_CATEGORY = "EducationalApplication"
APP_OS = "macOS"

# この站只做日英简三语，没有繁体
LANGS = {
    "ja": dict(out=".",  path="/",    htmllang="ja",      locale="ja_JP", font="Noto+Sans+JP", name="日本語"),
    "en": dict(out="en", path="/en/", htmllang="en",      locale="en_US", font=None,           name="English"),
    "zh": dict(out="zh", path="/zh/", htmllang="zh-Hans", locale="zh_CN", font="Noto+Sans+SC", name="简体中文"),
}
HREFLANG = {"ja": "ja", "en": "en", "zh": "zh-Hans"}

BASE_FONTS = ["Baloo+2:wght@500;600;700;800"]
ESCAPE_VALUES = False
BODY_CLASS = None
# 跟随系统、手动切不持久 —— 保持原行为，不引入 localStorage
STORAGE_KEY = None
BAR_KEY = {"en": "en", "zh": "zh"}
# 繁体也归到简体（这个站没有繁体版）
DETECT = {"en": "en", "zh-Hans": "zh", "zh-Hant": "zh"}
DEFAULT_LANG = "ja"
EXTRA_URLS = ["/privacy.html", "/support.html", "/terms.html"]

# 首屏键盘演示，与 i18n 无关但依赖当前语言 —— 删掉演示就不动了
_MOCK = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src/mock.js"),
             encoding="utf-8").read()
# ────────────────────────── 配置到此为止 ──────────────────────────

ROOT = os.path.dirname(os.path.abspath(__file__))
BANNER = ("<!-- 由 build.py 自动生成，请勿直接编辑。\n"
          "     改文案 → src/i18n.js，改结构 → src/index.html，然后跑 python3 build.py -->\n")


def load_dict():
    js = "console.log(JSON.stringify(require('./src/i18n.js')))"
    out = subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit("读取 src/i18n.js 失败:\n" + out.stderr)
    return json.loads(out.stdout)


def esc(t):
    if ESCAPE_VALUES == "auto":
        return t if "<" in t else html.escape(t, quote=False)
    return html.escape(t, quote=False) if ESCAPE_VALUES else t


def find_close(s, start, tag):
    """从 start 开始找 tag 的配对闭合标签，处理同名嵌套。"""
    depth = 1
    pat = re.compile(r"<(/?)%s\b[^>]*?(/?)>" % re.escape(tag), re.S)
    pos = start
    while True:
        m = pat.search(s, pos)
        if not m:
            sys.exit("标签 <%s> 没有配对闭合" % tag)
        depth += -1 if m.group(1) else (0 if m.group(2) else 1)
        pos = m.end()
        if depth == 0:
            return m.start(), m.end()


OPEN = re.compile(r"<(\w+)[^>]*\bdata-i18n=\"([^\"]+)\"[^>]*>", re.S)


def fill(fragment, d, used):
    """把 [data-i18n] 节点的文字换成目标语言。

    节点里若还嵌着子元素，只替换第一个子元素之前的那段文字再递归进去——
    运行时那套直接覆盖 innerHTML/textContent 会把子元素整个冲掉。
    """
    out, pos = [], 0
    while True:
        m = OPEN.search(fragment, pos)
        if not m:
            out.append(fragment[pos:])
            return "".join(out)
        tag, key = m.group(1), m.group(2)
        cs, ce = find_close(fragment, m.end(), tag)
        inner = fragment[m.end():cs]
        out.append(fragment[pos:m.end()])
        if key not in d:
            sys.exit("字典缺 key: %s" % key)
        used.add(key)
        nested = re.search(r"<\w+[^>]*\bdata-i18n=", inner)
        if nested:
            head = inner[:nested.start()]
            out.append(esc(d[key]) + (" " if head.endswith(" ") else ""))
            out.append(fill(inner[nested.start():], d, used))
        else:
            out.append(esc(d[key]))
        out.append(fragment[cs:ce])
        pos = ce


def head_extra(lang, d):
    cfg = LANGS[lang]
    url = SITE + cfg["path"]
    bits = ['<link rel="canonical" href="%s" />' % url]
    for l2, c2 in LANGS.items():
        bits.append('<link rel="alternate" hreflang="%s" href="%s%s" />'
                    % (HREFLANG[l2], SITE, c2["path"]))
    bits.append('<link rel="alternate" hreflang="x-default" href="%s%s" />'
                % (SITE, LANGS[DEFAULT_LANG]["path"]))

    def plain(t):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()

    faq = []
    for i in range(1, 21):
        q, a = d.get("faq.q%d" % i), d.get("faq.a%d" % i)
        if q and a:
            faq.append({"@type": "Question", "name": plain(q),
                        "acceptedAnswer": {"@type": "Answer", "text": plain(a)}})

    graph = [
        {"@type": "Organization", "@id": SITE + "/#org", "name": ORG,
         "url": SITE + "/", "email": SUPPORT_MAIL},
        {"@type": "WebSite", "@id": url + "#website", "url": url,
         "name": APP_NAME, "inLanguage": cfg["htmllang"],
         "publisher": {"@id": SITE + "/#org"}},
        # 不写 offers / aggregateRating：站上不标金额，评分也没有真实数据，不编。
        {"@type": "SoftwareApplication", "@id": SITE + "/#app", "name": APP_NAME,
         "applicationCategory": APP_CATEGORY, "operatingSystem": APP_OS,
         "description": plain(d["meta.desc"]), "url": url, "installUrl": APPSTORE,
         "image": OG_IMAGE,
         "inLanguage": [c["htmllang"] for c in LANGS.values()],
         "publisher": {"@id": SITE + "/#org"}},
    ]
    if faq:
        graph.append({"@type": "FAQPage", "@id": url + "#faq",
                      "inLanguage": cfg["htmllang"], "mainEntity": faq})

    bits.append('<script type="application/ld+json">%s</script>'
                % json.dumps({"@context": "https://schema.org", "@graph": graph},
                             ensure_ascii=False, separators=(",", ":")))
    return "\n".join(bits)


def fonts(lang):
    fam = list(BASE_FONTS)
    f = LANGS[lang]["font"]
    if f:
        fam.append("%s:wght@400;500;600;700;800" % f)
    if not fam:
        return "<!-- この言語は Web フォントを読み込みません -->"
    return ('<link href="https://fonts.googleapis.com/css2?family=%s&display=swap" '
            'rel="stylesheet">' % "&family=".join(fam))


DROPDOWN_JS = """(function(){
  var dd=document.querySelector('.lang-dd'); if(!dd) return;
  var btn=dd.querySelector('.lang-dd-btn');
  var close=function(){dd.setAttribute('data-open','false');btn.setAttribute('aria-expanded','false');};
  btn.addEventListener('click',function(e){e.stopPropagation();
    var o=dd.getAttribute('data-open')==='true';
    dd.setAttribute('data-open',String(!o));btn.setAttribute('aria-expanded',String(!o));});
  document.addEventListener('click',function(e){if(!dd.contains(e.target))close();});
})();"""


def script(lang, bar):
    js = [DROPDOWN_JS, _MOCK.replace("%MOCKLANG%", json.dumps(lang))]
    if STORAGE_KEY:
        js.append("""(function(){
  Array.prototype.forEach.call(document.querySelectorAll('a[data-lang]'),function(a){
    a.addEventListener('click',function(){
      try{localStorage.setItem('%s',a.getAttribute('data-lang'));}catch(e){}
    });
  });
})();""" % STORAGE_KEY)
    if lang == DEFAULT_LANG:
        # 首访非默认语言的访客只拿到一条可点的提示；按浏览器语言自动重定向
        # 会干扰搜索引擎索引，所以不做。爬虫没有 localStorage，也就永远不会被跳走。
        paths = {c: LANGS[c]["path"] for c in BAR_KEY}
        stored = ("""
  var stored=null; try{stored=localStorage.getItem('%s');}catch(e){}
  if(stored&&P[stored]){location.replace(P[stored]);return;}
  if(stored==='%s') return;""" % (STORAGE_KEY, DEFAULT_LANG)) if STORAGE_KEY else ""
        remember = ("""
  a.addEventListener('click',function(){try{localStorage.setItem('%s',d);}catch(e){}});"""
                    % STORAGE_KEY) if STORAGE_KEY else ""
        js.append("""(function(){
  var P=%s, K=%s, T=%s, D=%s;%s
  var d=null,list=navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||''];
  for(var i=0;i<list.length;i++){
    var t=(list[i]||'').toLowerCase();
    if(t.indexOf('%s')===0){return;}
    if(t.indexOf('zh')===0){d=/hant|tw|hk|mo/.test(t)?D['zh-Hant']:D['zh-Hans'];break;}
    if(t.indexOf('en')===0){d=D['en'];break;}
  }
  if(!d) d=D['en'];   /* 默认语言以外的其他语言（仏・独・韓など）は英語版へ */
  if(!P[d]||!K[d]||!T[K[d]]) return;
  var a=document.createElement('a');
  a.className='langbar'; a.href=P[d]; a.setAttribute('hreflang',d);
  a.textContent=T[K[d]]+' \\u2192';%s
  document.body.insertBefore(a,document.body.firstChild);
})();""" % (json.dumps(paths), json.dumps(BAR_KEY), json.dumps(bar, ensure_ascii=False),
            json.dumps(DETECT), stored, DEFAULT_LANG, remember))
    return "<script>\n%s\n</script>" % "\n".join(js)


def main():
    alld = load_dict()
    bar = json.load(open(os.path.join(ROOT, "src/langbar.json"), encoding="utf-8"))
    tmpl = open(os.path.join(ROOT, "src/index.html"), encoding="utf-8").read()

    for lang, cfg in LANGS.items():
        d = alld[lang]
        for k in ("meta.title", "meta.desc", "og.desc"):
            if k not in d:
                sys.exit("%s 缺 meta 键: %s" % (lang, k))
        used = set()
        page = fill(tmpl, d, used)
        oth = "".join('\n<meta property="og:locale:alternate" content="%s" />' % c["locale"]
                      for l2, c in LANGS.items() if l2 != lang)
        vals = {
            "HTMLLANG": cfg["htmllang"], "LANG": lang,
            "BODYCLASS": BODY_CLASS.format(lang=lang) if BODY_CLASS else "",
            "TITLE": html.escape(d["meta.title"]),
            "DESC": html.escape(d["meta.desc"]),
            "OGDESC": html.escape(d["og.desc"]),
            "URL": SITE + cfg["path"], "OGLOCALE": cfg["locale"], "OGALT": oth,
            "FONTS": fonts(lang), "HEADEXTRA": head_extra(lang, d),
            "LANGNAME": cfg["name"], "SCRIPT": script(lang, bar),
        }
        for l2, c2 in LANGS.items():
            vals["HREF_" + l2] = c2["path"]
            vals["ACT_" + l2] = "on" if l2 == lang else ""
            vals["SEL_" + l2] = "true" if l2 == lang else "false"
            vals["HL_" + l2] = HREFLANG[l2]
        for k, v in vals.items():
            page = page.replace("{{%s}}" % k, v)
        left = re.findall(r"\{\{[A-Za-z_-]+\}\}", page)
        if left:
            sys.exit("%s 有没替换的占位符: %s" % (lang, sorted(set(left))))

        page = page.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n" + BANNER, 1)
        outdir = os.path.join(ROOT, cfg["out"])
        os.makedirs(outdir, exist_ok=True)
        open(os.path.join(outdir, "index.html"), "w", encoding="utf-8").write(page)
        print("  %-9s → %-12s %3d 键  %6.1f KB"
              % (lang, cfg["path"], len(used), len(page.encode()) / 1024))

    alts = "".join('\n    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>'
                   % (HREFLANG[l], SITE, c["path"]) for l, c in LANGS.items())
    alts += ('\n    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>'
             % (SITE, LANGS[DEFAULT_LANG]["path"]))
    urls = ["  <url>\n    <loc>%s%s</loc>%s\n    <changefreq>monthly</changefreq>\n"
            "    <priority>%s</priority>\n  </url>"
            % (SITE, c["path"], alts, "1.0" if l == DEFAULT_LANG else "0.9")
            for l, c in LANGS.items()]
    urls += ["  <url>\n    <loc>%s%s</loc>\n    <changefreq>yearly</changefreq>\n"
             "    <priority>0.3</priority>\n  </url>" % (SITE, u) for u in EXTRA_URLS]
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n")
    print("  sitemap.xml → %d 条 URL" % len(urls))


if __name__ == "__main__":
    main()
