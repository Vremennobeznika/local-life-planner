#!/usr/bin/env python3
"""Capture real, anonymous UI screenshots for the repository README."""
import os
from pathlib import Path

from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

KIND = os.environ.get("SCREENSHOT_KIND", "planner")
BASE_URL = "http://127.0.0.1:8765/"
OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=True, args=["--no-sandbox"])
    for mode, width, height in (("desktop", 1280, 840), ("mobile", 390, 844)):
        mobile = mode == "mobile"
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
            is_mobile=mobile,
            has_touch=mobile,
            reduced_motion="reduce",
            locale="ru-RU",
        )
        page = context.new_page()
        url = BASE_URL + ("career.html" if KIND == "evosif" and mobile else "")
        response = page.goto(url, wait_until="networkidle", timeout=30000)
        if not response or response.status >= 400:
            raise RuntimeError(f"Failed to load {url}: {response.status if response else 'no response'}")
        page.locator("h1").first.wait_for(state="visible", timeout=10000)
        if KIND == "planner" and mobile:
            page.get_by_role("button", name="Покупки", exact=True).click(timeout=10000)
            page.locator("#page-shopping").wait_for(state="visible", timeout=10000)
        page.wait_for_timeout(350)
        raw = OUT / f".{mode}.png"
        page.screenshot(path=str(raw), animations="disabled", full_page=False)
        with Image.open(raw) as shot:
            shot = shot.convert("RGB")
            deviation = max(ImageStat.Stat(shot.resize((64, 64))).stddev)
            if deviation < 4:
                raise RuntimeError(f"Screenshot looks blank: {mode} (stddev {deviation:.2f})")
            shot.save(OUT / f"{mode}.webp", "WEBP", quality=76, method=6)
        raw.unlink()
        print(f"{mode}: {width}x{height}, {(OUT / f'{mode}.webp').stat().st_size} bytes")
        context.close()
    browser.close()
