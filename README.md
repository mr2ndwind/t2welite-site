# T2W Elite website (t2welite.com)

Static site built from simple content files. Forms, alerts and tracking run through GoHighLevel.

## How it works
- `content/pages/*.html` — page bodies (header block, then `---`, then HTML)
- `content/articles/*.md` — blog and Coaches Corner articles (header block, then `---`, then light markdown)
- `config.json` — logo, GHL form IDs, booking links, portal link, domain
- `src/site.css` — all styling (Elite red #F22B0C, black, white, gray)
- `build.py` — run `python3 build.py` to regenerate `docs/`, which GitHub Pages serves

## Placeholders
- `{{form:KEY}}` embeds the GHL form whose ID is in `config.json > forms.KEY` (blank ID shows a fallback box)
- `{{cta:KEY}}` adds a CTA band (evaluation, sports, basketball, jumpkit, coach)
- `{{blog_grid}}` / `{{coach_grid}}` insert article lists

## Article callouts
`> FOR PARENTS | text`, `> FOR ATHLETES | text`, `> KEY TAKEAWAY | text`
