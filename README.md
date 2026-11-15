# Reklama5 auto-renew

Скрипта што се најавува на reklama5.mk и го обновува огласот (1x дневно е лимитот, а работи на секој 2 ден).

## Поставување на GitHub
1. Направи (приватно) repo и качи ги овие фајлови.
2. Settings → Secrets and variables → Actions → New repository secret:
   - `R5_EMAIL` = е-поштата за најава
   - `R5_PASSWORD` = лозинката
3. Actions → "Renew reklama5 ad" → Run workflow за прв тест.

## Локален тест
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && playwright install chromium
export R5_EMAIL='...' R5_PASSWORD='...'
HEADLESS=0 python renew_ad.py
```
Ако не го најде копчето за обнова, види `debug/` и постави `R5_RENEW_SELECTOR` (пр. `a:has-text("Обнови")`).
