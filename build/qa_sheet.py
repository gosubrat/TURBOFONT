#!/usr/bin/env python3
"""Large-size QA sheet for the M2 alphabet.

One row per letter, one column per artwork variant plus the flat fallback.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import letters

HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>Tribal Totem Display - QA sheet</title>
<style>
  @font-face {{ font-family: "TTD"; src: url("dist/TribalTotemDisplay-Black.otf") format("opentype"); }}
  @font-face {{ font-family: "TTDF"; src: url("dist/TribalTotemDisplayFlat-Black.otf") format("opentype"); }}
  body {{ margin: 0; background: #A52714; color: #F2C511; font-family: "TTD", sans-serif; }}
  .wrap {{ padding: 30px 40px 50px; }}
  h1 {{ font-family: ui-monospace, monospace; font-size: 14px; letter-spacing: .14em;
        font-weight: 400; color: #F2C511; opacity: .8; margin: 0 0 12px; }}
  table {{ border-collapse: collapse; }}
  th {{ font-family: ui-monospace, monospace; font-size: 10px; letter-spacing: .12em;
        font-weight: 400; opacity: .55; padding: 0 0 6px; text-align: center; }}
  td {{ width: 190px; height: 188px; text-align: center; vertical-align: middle; }}
  .g {{ font-size: 158px; line-height: 1; }}
  .flat {{ font-family: "TTDF", sans-serif; color: #1a1a1a; background: #F2C511;
           display: inline-block; padding: 0 5px; }}
  .tag {{ font-family: ui-monospace, monospace; font-size: 13px; opacity: .5; width: 26px; }}
  .ss01 {{ font-feature-settings: "ss01"; }}
  .ss02 {{ font-feature-settings: "ss02"; }}
  .ss03 {{ font-feature-settings: "ss03"; }}
</style></head>
<body><div class="wrap">
<h1>TRIBAL TOTEM DISPLAY &mdash; 1.000 M3 &mdash; 158 PXmdash; 158 PX</h1>
<table>
<tr><th></th><th>BASE</th><th>SS01</th><th>SS02</th><th>SS03</th><th>FLAT</th></tr>
{rows}
</table>
</div></body></html>
"""

CELLS = [
    '<td class="g">{ch}</td>',
    '<td class="g ss01">{ch}</td>',
    '<td class="g ss02">{ch}</td>',
    '<td class="g ss03">{ch}</td>',
    '<td class="g flat">{ch}</td>',
]


GROUPS = {
    "letters": letters.LETTER_CHARS,
    "accents": letters.ACCENT_CHARS,
    "digits": letters.DIGIT_CHARS,
    "punct": letters.PUNCT_CHARS,
    "symbols": letters.DIGIT_CHARS + letters.PUNCT_CHARS,
    "typographic": letters.SYMBOL_CHARS,
    "all": letters.CHARS,
}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "letters"
    chars = GROUPS.get(arg, arg)
    out_name = sys.argv[2] if len(sys.argv) > 2 else (
        "sheet.png" if arg == "letters" else f"sheet-{arg}.png")
    rows = []
    for ch in chars:
        cells = "".join(c.format(ch=ch) for c in CELLS)
        rows.append(f'<tr><td class="tag">{ch}</td>{cells}</tr>')
    html = HTML.format(rows="\n".join(rows))
    path = os.path.join(ROOT, out_name.replace(".png", ".html"))
    with open(path, "w") as fh:
        fh.write(html)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        print("screenshot skipped:", exc)
        return
    out = os.path.join(ROOT, out_name)
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1080, "height": 1200},
                          device_scale_factor=1.5)
        page.goto("file://" + path)
        page.wait_for_timeout(900)
        page.screenshot(path=out, full_page=True)
        b.close()
    print("wrote", out)


if __name__ == "__main__":
    main()
