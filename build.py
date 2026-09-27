#!/usr/bin/env python3
"""Build the T2W Elite static site into docs/ (served by GitHub Pages).

Content lives in content/:
  pages/*.html      page bodies with a small header block (key: value lines, then ---)
  articles/*.md     blog + Coaches Corner articles (key: value header, then ---, then light markdown)
Run:  python3 build.py
All links are written relative ({{root}}) so the site works both on the GitHub preview
URL (mr2ndwind.github.io/t2welite-site/) and on the real domain (t2welite.com).
"""
import html, json, math, pathlib, re, shutil

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
SITE_URL = "https://t2welite.com"
CFG = json.loads((ROOT / "config.json").read_text())

NAV = [("Home", ""), ("About", "about/"), ("Sports Performance", "sports-performance-training/"),
       ("Basketball Training", "basketball-training/"), ("Team Training", "team-training/"),
       ("Tryouts", "tryouts/"), ("Blog", "blog/"), ("Coaches Corner", "coaches-corner/"), ("Contact", "contact/")]


def esc(s):
    return html.escape(s, quote=True)


def parse_header(text):
    head, body = text.split("---\n", 1)
    meta = {}
    for line in head.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    return meta, body


def form_embed(key, height=None):
    fid = CFG["forms"].get(key)
    if not fid:
        return ('<div class="form-pending"><p><strong>This form is being moved to our new system.</strong></p>'
                '<p class="muted">In the meantime, start with our free athlete evaluation or call (918) 918-3234.</p>'
                '<a class="btn" href="{{root}}evaluation/">Start Free Evaluation</a></div>')
    h = height or CFG["form_heights"].get(key, 900)
    src = f'{CFG["form_host"]}/widget/form/{fid}'
    return (f'<div class="form-box" style="min-height:{h}px"><iframe src="{src}" id="inline-{fid}" '
            f'data-layout="{{\'id\':\'INLINE\'}}" '
            f'data-trigger-type="alwaysShow" data-trigger-value="" data-activation-type="alwaysActivated" '
            f'data-activation-value="" data-deactivation-type="neverDeactivate" data-deactivation-value="" '
            f'data-form-name="{esc(key)}" data-height="{h}" data-layout-iframe-id="inline-{fid}" '
            f'data-form-id="{fid}" data-cookie-consent="false" title="{esc(key)} form" '
            f'style="width:100%;height:100%;min-height:{h}px;border:none;border-radius:8px"></iframe></div>')


def md_to_html(md):
    out, para, lst = [], [], []

    def flush():
        if para:
            out.append("<p>" + esc(" ".join(para)) + "</p>")
            para.clear()
        if lst:
            out.append("<ul>" + "".join(f"<li>{esc(i)}</li>" for i in lst) + "</ul>")
            lst.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush(); continue
        if line.startswith("### "):
            flush(); out.append(f"<h3>{esc(line[4:])}</h3>")
        elif line.startswith("## "):
            flush(); out.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("- "):
            if para:
                out.append("<p>" + esc(" ".join(para)) + "</p>"); para.clear()
            lst.append(line[2:])
        elif line.startswith("> "):
            flush()
            label, _, txt = line[2:].partition(" | ")
            cls = "callout key" if "KEY" in label else "callout"
            out.append(f'<div class="{cls}"><b>{esc(label)}</b>{esc(txt)}</div>')
        else:
            if lst:
                flush()
            para.append(line.strip())
    flush()
    return "\n".join(out)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


CTAS = {
    "evaluation": ("READY TO FIND YOUR TRAINING PATH?", "Take our quick athlete evaluation and get a personalized training recommendation from Coach Corey.", "START YOUR FREE ATHLETE EVALUATION", "evaluation/"),
    "sports": ("BUILD SPEED, STRENGTH & POWER", "Our sports performance training develops the athleticism that translates to every sport. Start with a free evaluation.", "EXPLORE SPORTS PERFORMANCE", "sports-performance-training/"),
    "basketball": ("TRAIN YOUR BASKETBALL SKILLS WITH T2W ELITE", "Shooting, ball handling, footwork, finishing, and basketball IQ — customized to your game.", "EXPLORE BASKETBALL TRAINING", "basketball-training/"),
    "jumpkit": ("FREE 8-WEEK VERTICAL JUMP KIT", "Get a complete vertical jump training program delivered to your inbox. Increase explosiveness and jump higher in 8 weeks.", "GET MY FREE 8-WEEK JUMP KIT", "jump-kit/"),
    "coach": ("COACH WITH T2W ELITE", "If you believe in teaching, development, and accountability, we want to hear from you.", "APPLY TO COACH", "coaches-corner/#apply"),
}


def layout(title, desc, path, body, active=None, schema=None):
    depth = path.count("/")
    root = "../" * depth
    canon = f"{SITE_URL}/{path}"
    on = ' class="on"'
    def link(n, p):
        return f'<a href="{root}{p}"{on if active == p else ""}>{n}</a>'
    training = [("Sports Performance", "sports-performance-training/"), ("Basketball Training", "basketball-training/"),
                ("Team Training", "team-training/")]
    t_on = " on" if active in [p for _, p in training] else ""
    nav = (link("About", "about/")
           + f'<div class="dd"><button class="dd-btn{t_on}" type="button">Training</button><div class="dd-menu">'
           + "".join(link(n, p) for n, p in training) + "</div></div>"
           + "".join(link(n, p) for n, p in [("Tryouts", "tryouts/"), ("Blog", "blog/"),
                                              ("Coaches Corner", "coaches-corner/"), ("Contact", "contact/")]))
    ld = f'<script type="application/ld+json">{json.dumps(schema)}</script>' if schema else ""
    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:image" content="{CFG['og_image']}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0B">
<link rel="icon" href="{CFG['logo']}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Oswald:wght@500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/site.css">
{ld}
</head><body>
<header class="top"><div class="wrap">
<a class="logo" href="{root or './'}" aria-label="T2W Elite home"><img src="{CFG['logo']}" alt="T2W Elite" width="120" height="46"></a>
<button class="menu-btn" aria-expanded="false" aria-controls="nav">MENU</button>
<nav class="nav" id="nav">{nav}<a class="btn sm" href="{root}evaluation/">Free Evaluation</a><a href="{root}portal/login/">Athlete Portal</a></nav>
</div></header>
<main>
{body}
</main>
<footer><div class="wrap">
<div class="foot">
<div><img src="{CFG['logo']}" alt="T2W Elite" width="130" height="50" style="height:50px;width:auto;margin-bottom:16px">
<p class="muted">Sports performance and basketball training designed to help athletes develop speed, strength, power, confidence, and game-changing skills.</p>
<p class="tag">TRAIN FASTER. JUMP HIGHER. COMPETE BETTER.</p></div>
<div><h4>Training</h4><ul>
<li><a href="{root}sports-performance-training/">Sports Performance</a></li>
<li><a href="{root}basketball-training/">Basketball Training</a></li>
<li><a href="{root}team-training/">Team Training</a></li>
<li><a href="{root}evaluation/">Free Athlete Evaluation</a></li>
<li><a href="{root}jump-kit/">Free Vertical Jump Kit</a></li></ul></div>
<div><h4>T2W Elite</h4><ul>
<li><a href="{root}about/">About</a></li>
<li><a href="{root}16u-roster/">16U Roster</a></li>
<li><a href="{root}tryouts/">Tryouts</a></li>
<li><a href="{root}blog/">Blog</a></li>
<li><a href="{root}coaches-corner/">Coaches Corner</a></li>
<li><a href="{CFG['support_url']}" rel="noopener">Donations &amp; Sponsors</a></li></ul></div>
<div><h4>Contact</h4><ul>
<li><a href="tel:+19189183234">(918) 918-3234</a></li>
<li>3074 N Aspen Ave Suite 110<br>Broken Arrow, OK 74012</li>
<li class="muted">Across from Battle Creek Church</li>
<li><a href="{CFG['facebook']}" rel="noopener">Facebook</a></li></ul></div>
</div>
<div class="legal"><span>&copy; <span id="yr">2026</span> T2W Elite, a Team 2nd Wind program. All rights reserved.</span>
<span><a href="{CFG['privacy_url']}">Privacy Policy</a> &middot; <a href="{CFG['terms_url']}">Terms</a></span></div>
</div></footer>
<script>
document.getElementById('yr').textContent=new Date().getFullYear();
var b=document.querySelector('.menu-btn'),n=document.getElementById('nav');
b.addEventListener('click',function(){{var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}});
</script>
<script src="{CFG['form_host']}/js/form_embed.js"></script>
</body></html>
"""
    page = page.replace("{{root}}", root)
    dest = OUT / path / "index.html" if path else OUT / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page)
    return canon


def cta_band(title, text, btn, href):
    return (f'<section class="cta"><div class="wrap"><h2>{esc(title)}</h2><p>{esc(text)}</p>'
            f'<a class="btn" href="{{{{root}}}}{href}">{esc(btn)}</a></div></section>')


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "src" / "site.css", OUT / "assets" / "site.css")
    urls = []

    # Articles
    arts = []
    for f in sorted((ROOT / "content" / "articles").glob("*.md")):
        meta, body = parse_header(f.read_text())
        words = len(body.split())
        meta.setdefault("read", f"{max(3, math.ceil(words / 200))} min read")
        meta["slug"] = f.stem
        meta["body"] = body
        if "excerpt" not in meta:
            first = body.strip().split("\n\n")[0]
            meta["excerpt"] = (first[:170].rsplit(" ", 1)[0] + "…") if len(first) > 170 else first
        arts.append(meta)

    for a in arts:
        cta = a.get("cta", "evaluation")
        if cta == "custom":
            c = (a["cta_title"], a["cta_text"], a["cta_button"], a["cta_link"].lstrip("/"))
        else:
            c = CTAS[cta]
        related = [r for r in arts if r["category"] == a["category"] and r["slug"] != a["slug"]][:3]
        rel_html = "".join(post_card(r) for r in related)
        is_coach = a["category"] == "COACHES CORNER"
        crumb_parent = ('<a href="{{root}}coaches-corner/">Coaches Corner</a>' if is_coach
                        else '<a href="{{root}}blog/">Blog</a>')
        date = f' &middot; {esc(a["date"])}' if a.get("date") else ""
        body = f"""<section class="page-hero"><div class="wrap article">
<div class="crumbs"><a href="{{{{root}}}}">Home</a> / {crumb_parent}</div>
<span class="eyebrow">{esc(a['category'])}</span><h1 style="font-size:clamp(2rem,4.6vw,3.2rem)">{esc(a['title'])}</h1>
<div class="post-meta">By Coach Corey Scyffore &middot; {esc(a['read'])}{date}</div></div></section>
<section><div class="wrap article">{md_to_html(a['body'])}
<div class="card accent" style="margin-top:40px"><h3>{esc(c[0])}</h3><p>{esc(c[1])}</p><a class="btn" href="{{{{root}}}}{c[3]}">{esc(c[2])}</a></div>
<p class="disclaimer">The information in this article is general education and is not individualized medical advice. Athletes with specific health conditions or dietary needs should consult a qualified professional.</p>
</div></section>
{('<section class="band"><div class="wrap"><h2>Related Articles</h2><div class="grid g3">' + rel_html + '</div></div></section>') if related else ''}"""
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"],
                  "author": {"@type": "Person", "name": "Corey Scyffore"},
                  "publisher": {"@type": "Organization", "name": "T2W Elite", "logo": {"@type": "ImageObject", "url": CFG["logo"]}},
                  "description": a["excerpt"]}
        title = a.get("seo") or f'{a["title"]} | T2W Elite'
        if "T2W" not in title and "|" not in title:
            title += " | T2W Elite"
        urls.append(layout(title, a["excerpt"], f"blog/{a['slug']}/", body,
                           active="coaches-corner/" if is_coach else "blog/", schema=schema))

    # Blog index + coach article list are injected into pages via tokens
    blog_arts = [a for a in arts if a["category"] != "COACHES CORNER"]
    coach_arts = sorted([a for a in arts if a["category"] == "COACHES CORNER"],
                        key=lambda a: a.get("date", ""), reverse=False)
    cats = sorted({a["category"] for a in blog_arts})
    filters = '<div class="filters" id="filters"><button class="on" data-c="all">All</button>' + "".join(
        f'<button data-c="{slugify(c)}">{esc(c.title())}</button>' for c in cats) + "</div>"
    tokens = {
        "{{blog_grid}}": filters + '<div class="grid g3" id="posts">' + "".join(post_card(a) for a in blog_arts) + "</div>",
        "{{coach_grid}}": '<div class="grid g3">' + "".join(post_card(a) for a in coach_arts) + "</div>",
    }

    # Pages
    for f in sorted((ROOT / "content" / "pages").glob("*.html")):
        meta, body = parse_header(f.read_text())
        for k, v in tokens.items():
            body = body.replace(k, v)
        body = re.sub(r"\{\{form:([a-z_]+)\}\}", lambda m: form_embed(m.group(1)), body)
        body = re.sub(r"\{\{cta:([a-z]+)\}\}", lambda m: cta_band(*CTAS[m.group(1)]), body)
        schema = None
        if meta["path"] == "":
            schema = {"@context": "https://schema.org", "@type": "SportsActivityLocation", "name": "T2W Elite",
                      "url": SITE_URL, "telephone": "+1-918-918-3234", "image": CFG["logo"],
                      "address": {"@type": "PostalAddress", "streetAddress": "3074 N Aspen Ave Suite 110",
                                  "addressLocality": "Broken Arrow", "addressRegion": "OK", "postalCode": "74012", "addressCountry": "US"},
                      "areaServed": ["Broken Arrow", "Jenks", "Union", "Bixby", "Owasso", "Tulsa"]}
        urls.append(layout(meta["title"], meta["description"], meta["path"], body,
                           active=meta.get("nav", meta["path"]), schema=schema))

    # 404, robots, sitemap, .nojekyll
    (OUT / "404.html").write_text((OUT / "not-found" / "index.html").read_text().replace('href="../', 'href="/'))
    shutil.rmtree(OUT / "not-found")
    urls = [u for u in urls if "not-found" not in u]
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"<url><loc>{u}</loc></url>\n" for u in sorted(set(urls))) + "</urlset>\n")
    (OUT / ".nojekyll").write_text("")
    if CFG.get("custom_domain"):
        (OUT / "CNAME").write_text(CFG["custom_domain"] + "\n")
    print(f"Built {len(urls)} pages into {OUT}")


def post_card(a):
    return (f'<a class="post-card" data-c="{slugify(a["category"])}" href="{{{{root}}}}blog/{a["slug"]}/">'
            f'<span class="meta">{esc(a["category"])} &middot; {esc(a["read"])}</span>'
            f'<h3>{esc(a["title"])}</h3><p>{esc(a["excerpt"])}</p><span class="more">READ ARTICLE &rarr;</span></a>')


if __name__ == "__main__":
    build()
