#!/usr/bin/env python3
"""Cross-browser smoke test for the release fonts.

    python3 build/browser_test.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SPECIMEN = os.path.join(ROOT, "specimen.html")

WOFF2_HTML = """<!doctype html>
<html><head><meta charset="utf-8"><title>WOFF2 test</title>
<style>
@font-face { font-family: "TTD"; src: url("dist/TribalTotemDisplay-Black.woff2") format("woff2"); }
body { margin: 0; background: #A52714; color: #F2C511; font-family: "TTD", sans-serif; }
p { font-size: 96px; padding: 24px; margin: 0; }
</style></head><body><p>AVATAR To. (A) &amp; @ € Ø 123</p></body></html>
"""


def main():
    from playwright.sync_api import sync_playwright

    woff2_path = os.path.join(ROOT, "woff2-test.html")
    with open(woff2_path, "w") as fh:
        fh.write(WOFF2_HTML)

    failures = []
    with sync_playwright() as p:
        for name in ("chromium", "firefox", "webkit"):
            try:
                browser = getattr(p, name).launch()
                page = browser.new_page(viewport={"width": 1200, "height": 900},
                                        device_scale_factor=1)
                page.goto("file://" + SPECIMEN)
                page.wait_for_timeout(900)
                loaded = page.evaluate(
                    "document.fonts.check('64px \"Tribal Totem Display\"')")
                page.screenshot(path=os.path.join(ROOT, f"browser-{name}.png"),
                                full_page=False)
                browser.close()
                print(f"{name}: specimen font loaded={loaded}")
                if not loaded:
                    failures.append(name)
            except Exception as exc:  # pragma: no cover
                failures.append(name)
                print(f"{name}: ERROR {str(exc).splitlines()[0]}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 200})
        page.goto("file://" + woff2_path)
        page.wait_for_timeout(600)
        loaded = page.evaluate("document.fonts.check('96px TTD')")
        page.screenshot(path=os.path.join(ROOT, "browser-woff2.png"))
        browser.close()
        print(f"woff2: loaded={loaded}")
        if not loaded:
            failures.append("woff2")

    print("\nfailures:", failures or "none")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
