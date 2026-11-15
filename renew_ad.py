#!/usr/bin/env python3
"""Автоматско обновување (renew) на оглас на reklama5.mk.

Env променливи:
  R5_EMAIL        (задолжително) е-пошта за најава
  R5_PASSWORD     (задолжително) лозинка
  R5_AD_ID        (опционално)   ID на огласот, пр. 5892482 (default)
  R5_RENEW_SELECTOR (опционално) CSS/Playwright селектор за копчето за обнова,
                                 ако автоматското препознавање не работи
  HEADLESS        (опционално)   "0" за да го гледаш прелистувачот локално
"""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

BASE = "https://reklama5.mk"
AD_ID = os.environ.get("R5_AD_ID", "5892482")
DEBUG_DIR = Path("debug")

# Зборови што може да се појават на копчето за обнова
RENEW_RE = re.compile(r"обнови|освежи|обнова|renew|refresh|bump", re.I)


def save_debug(page, name):
    DEBUG_DIR.mkdir(exist_ok=True)
    try:
        page.screenshot(path=str(DEBUG_DIR / f"{name}.png"), full_page=True)
        (DEBUG_DIR / f"{name}.html").write_text(page.content(), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] не успеав да зачувам debug: {e}")


def login(page, email, password):
    page.goto(f"{BASE}/Register", wait_until="domcontentloaded")
    page.fill("#loginEmail", email)
    page.fill("#loginPassword", password)
    page.click("#btnSubmit")
    page.wait_for_load_state("networkidle")
    if "/Register" in page.url and page.locator("#loginPassword").count():
        save_debug(page, "login_failed")
        sys.exit("Најавата не успеа (провери R5_EMAIL / R5_PASSWORD или има CAPTCHA/блок).")
    print("[ok] најавен")


def find_renew_button(page):
    custom = os.environ.get("R5_RENEW_SELECTOR")
    if custom:
        loc = page.locator(custom)
        return loc.first if loc.count() else None

    # Најди го редот/картичката на огласот во Dashboard, па копче со "обнови"
    ad_scope = page.locator(f"*:has(a[href*='ad={AD_ID}'])").last
    for scope in (ad_scope, page):
        for role in ("button", "link"):
            loc = scope.get_by_role(role, name=RENEW_RE)
            if loc.count():
                return loc.first
        loc = scope.locator("a, button, input[type=button], input[type=submit]").filter(has_text=RENEW_RE)
        if loc.count():
            return loc.first
    return None


def renew(page):
    page.goto(f"{BASE}/Dashboard", wait_until="networkidle")
    btn = find_renew_button(page)
    if btn is None:
        # пробај и од страната на огласот
        page.goto(f"{BASE}/AdDetails/Index?ad={AD_ID}", wait_until="networkidle")
        btn = find_renew_button(page)
    if btn is None:
        save_debug(page, "no_renew_button")
        sys.exit("Не го најдов копчето за обнова. Види debug/ или постави R5_RENEW_SELECTOR.")

    print(f"[info] копче: {btn.inner_text().strip()!r}")
    # потврда во диалог, ако има
    page.on("dialog", lambda d: d.accept())
    btn.click()
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except PWTimeout:
        pass
    # некои сајтови прикажуваат модал со "Да/Потврди"
    confirm = page.get_by_role("button", name=re.compile(r"^(да|потврди|ок|ok|yes)$", re.I))
    if confirm.count():
        confirm.first.click()
        page.wait_for_load_state("networkidle")

    save_debug(page, "after_renew")
    print("[ok] обновата е испратена (провери debug/after_renew.png)")


def main():
    email = os.environ.get("R5_EMAIL")
    password = os.environ.get("R5_PASSWORD")
    if not email or not password:
        sys.exit("Недостасуваат R5_EMAIL / R5_PASSWORD.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=os.environ.get("HEADLESS", "1") != "0")
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            locale="mk-MK",
            viewport={"width": 1366, "height": 900},
        )
        page = ctx.new_page()
        try:
            login(page, email, password)
            renew(page)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
