"""Baut die Karussell-Folien für „Светлата страна“.

Aufruf: python3 render.py <post-ordner> <fontsource-ordner>
  <post-ordner>       enthält post.json und optional photo.jpg
  <fontsource-ordner> node_modules/@fontsource (unbounded + manrope)
Ergebnis: <post-ordner>/out/1.jpg … n.jpg (1080×1350)
"""
import asyncio, base64, html, json, pathlib, sys
from playwright.async_api import async_playwright

NAVY, SUN, CREAM, KICK = "#1B2440", "#F5B400", "#FFF6E5", "#7A5A00"
W, H = 1080, 1350


def e(s):
    return html.escape(str(s))


def sun(size, horizon, stroke=4):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">'
            f'<path d="M14 42 A18 18 0 0 1 50 42 Z" fill="{SUN}"/>'
            f'<line x1="32" y1="10" x2="32" y2="18" stroke="{SUN}" stroke-width="{stroke}" stroke-linecap="round"/>'
            f'<line x1="12" y1="20" x2="17" y2="25" stroke="{SUN}" stroke-width="{stroke}" stroke-linecap="round"/>'
            f'<line x1="52" y1="20" x2="47" y2="25" stroke="{SUN}" stroke-width="{stroke}" stroke-linecap="round"/>'
            f'<line x1="6" y1="46" x2="58" y2="46" stroke="{horizon}" stroke-width="{stroke}" stroke-linecap="round"/></svg>')


def cover(p, photo_uri):
    c = p["cover"]
    ph = p.get("photo_height", H)  # Foto kann auf den oberen Teil begrenzt werden, damit das Motiv über dem Text bleibt
    bg = (f'<img src="{photo_uri}" style="position:absolute;top:0;left:0;width:100%;height:{ph}px;object-fit:cover;'
          f'object-position:{e(p.get("photo_position", "center"))}">' if photo_uri else
          f'<div style="position:absolute;inset:0;background:{NAVY}"></div>')
    credit = p.get("photo_credit", "")
    return f'''
<div style="width:{W}px;height:{H}px;position:relative;overflow:hidden;background:{NAVY};font-family:Manrope,sans-serif">
{bg}
<div style="position:absolute;left:0;right:0;bottom:0;height:780px;background:linear-gradient(180deg,rgba(27,36,64,0) 0%,rgba(27,36,64,.8) 32%,rgba(27,36,64,1) 56%,rgba(27,36,64,1) 100%)"></div>
<div style="position:absolute;top:56px;left:64px;background:{SUN};color:{NAVY};font-weight:700;font-size:24px;letter-spacing:2px;padding:12px 22px;border-radius:999px">{e(p.get("label", "БЪЛГАРИЯ"))}</div>
{f'<div style="position:absolute;top:62px;right:64px;font-size:20px;font-weight:600;color:rgba(255,255,255,.9);background:rgba(14,18,34,.6);padding:10px 18px;border-radius:999px;max-width:520px;text-align:right">{e(credit)}</div>' if credit else ''}
<div style="position:absolute;left:64px;right:64px;bottom:200px;display:flex;flex-direction:column;gap:28px">
<h1 style="margin:0;font-family:Unbounded,sans-serif;font-weight:700;font-size:{c.get("size", 88)}px;line-height:1.05;color:#fff">{e(c["title"])}</h1>
<p style="margin:0;font-size:38px;line-height:1.35;font-weight:500;color:rgba(255,255,255,.92)">{e(c.get("subtitle", ""))}</p>
</div>
<div style="position:absolute;left:64px;right:64px;bottom:64px;display:flex;align-items:center;justify-content:space-between">
<div style="display:flex;align-items:center;gap:18px">{sun(64, "#FFFFFF")}
<div><div style="font-family:Unbounded,sans-serif;font-weight:700;font-size:30px;color:#fff">Светлата страна</div>
<div style="font-size:22px;font-weight:600;color:rgba(255,255,255,.8)">Има и добро</div></div></div>
<div style="font-size:26px;font-weight:700;color:#fff">Плъзни →</div>
</div></div>'''


def content(s, num, total):
    parts = [f'<div style="font-size:26px;font-weight:700;letter-spacing:3px;color:{KICK}">{e(s.get("kicker", "")).upper()}</div>',
             f'<h2 style="margin:0;font-family:Unbounded,sans-serif;font-weight:700;font-size:{s.get("size", 70)}px;line-height:1.12">{e(s["title"])}</h2>']
    if s.get("body"):
        parts.append(f'<p style="margin:0;font-size:40px;line-height:1.45;font-weight:500">{e(s["body"])}</p>')
    if s.get("stats"):
        cards = "".join(
            f'<div style="background:#fff;border-radius:28px;padding:36px 28px;display:flex;flex-direction:column;gap:12px">'
            f'<div style="width:36px;height:36px;border-radius:999px;background:{st.get("color", SUN)}"></div>'
            f'<div style="font-family:Unbounded,sans-serif;font-weight:700;font-size:{st.get("size", 84)}px;line-height:1">{e(st["value"])}</div>'
            f'<div style="font-size:30px;font-weight:600">{e(st["label"])}</div></div>' for st in s["stats"])
        parts.append(f'<div style="display:grid;grid-template-columns:repeat({len(s["stats"])},minmax(0,1fr));gap:24px">{cards}</div>')
    if s.get("box"):
        b = s["box"]
        parts.append(f'<div style="background:{NAVY};color:#fff;border-radius:32px;padding:48px 52px;display:flex;flex-direction:column;gap:20px">'
                     f'<div style="font-family:Unbounded,sans-serif;font-weight:700;font-size:44px;line-height:1.2;color:{SUN}">{e(b["title"])}</div>'
                     f'<p style="margin:0;font-size:36px;line-height:1.4;font-weight:500">{e(b.get("text", ""))}</p></div>')
    parts.append('<div style="flex-grow:1"></div>')
    if s.get("note"):
        parts.append(f'<div style="display:flex;align-items:center;gap:28px;background:#fff;border-radius:32px;padding:44px 48px">'
                     f'<div style="flex-shrink:0">{sun(88, NAVY)}</div>'
                     f'<p style="margin:0;font-family:Unbounded,sans-serif;font-weight:600;font-size:40px;line-height:1.25">{e(s["note"])}</p></div>')
    parts.append(f'<div style="display:flex;align-items:center;justify-content:space-between">'
                 f'<div style="display:flex;align-items:center;gap:14px">{sun(48, NAVY)}'
                 f'<div style="font-family:Unbounded,sans-serif;font-weight:700;font-size:24px">Светлата страна</div></div>'
                 f'<div style="font-size:24px;font-weight:700;color:#4A5370">{num} / {total}</div></div>')
    return (f'<div style="width:{W}px;height:{H}px;box-sizing:border-box;padding:96px 80px 64px;background:{CREAM};'
            f'font-family:Manrope,sans-serif;color:{NAVY};display:flex;flex-direction:column;gap:44px">{"".join(parts)}</div>')


def ending(p, total):
    return f'''
<div style="width:{W}px;height:{H}px;box-sizing:border-box;padding:96px 80px 64px;background:{NAVY};font-family:Manrope,sans-serif;color:#fff;display:flex;flex-direction:column;align-items:center;gap:40px;text-align:center">
<div style="flex-grow:1"></div>{sun(200, "#FFFFFF", 3)}
<h2 style="margin:0;font-family:Unbounded,sans-serif;font-weight:700;font-size:88px;line-height:1.05">Светлата страна</h2>
<div style="font-family:Unbounded,sans-serif;font-weight:600;font-size:48px;color:{SUN}">Има и добро.</div>
<p style="margin:0;max-width:760px;font-size:38px;line-height:1.45;font-weight:500;color:rgba(255,255,255,.9)">Всеки ден по една добра новина от България и света.</p>
<div style="background:{SUN};color:{NAVY};font-weight:700;font-size:34px;padding:24px 48px;border-radius:999px">Последвай ни</div>
<div style="flex-grow:1"></div>
<div style="display:flex;flex-direction:column;gap:8px;align-items:center;font-size:24px;font-weight:600;color:rgba(255,255,255,.75)">
<div>Източник: {e(p.get("source", ""))}</div><div>{total} / {total}</div></div></div>'''


async def main(post_dir, fonts):
    post_dir, fonts = pathlib.Path(post_dir).resolve(), pathlib.Path(fonts).resolve()
    p = json.loads((post_dir / "post.json").read_text(encoding="utf-8"))
    photo = post_dir / "photo.jpg"
    photo_uri = ("data:image/jpeg;base64," + base64.b64encode(photo.read_bytes()).decode()) if photo.exists() else None
    total = len(p.get("slides", [])) + 2
    pages = [cover(p, photo_uri)] + [content(s, i + 2, total) for i, s in enumerate(p.get("slides", []))] + [ending(p, total)]
    fu = fonts.as_uri()
    head = "".join(f'<link rel="stylesheet" href="{fu}/{f}/{w}.css">' for f, ws in (("unbounded", (600, 700)), ("manrope", (500, 600, 700))) for w in ws)
    out = post_dir / "out"
    out.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        b = await pw.chromium.launch(args=["--allow-file-access-from-files"])
        for i, body in enumerate(pages, 1):
            f = out / f"_{i}.html"
            f.write_text(f'<!doctype html><html lang="bg"><head><meta charset="utf-8">{head}<style>body{{margin:0}}</style></head><body>{body}</body></html>', encoding="utf-8")
            pg = await b.new_page(viewport={"width": W, "height": H})
            await pg.goto(f.as_uri())
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(300)
            await pg.screenshot(path=str(out / f"{i}.jpg"), type="jpeg", quality=90)
            f.unlink()
        await b.close()
    print(f"{total} Folien in {out}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2]))
