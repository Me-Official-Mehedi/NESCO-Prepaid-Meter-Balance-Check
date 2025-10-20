import re
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os  # Add this import for environment variables

# ====== Config ======
BOT_TOKEN = os.environ['BOT_TOKEN']  # Reads from GitHub secret
CHAT_ID = os.environ['CHAT_ID']      # Reads from GitHub secret
CUST_NO = os.environ.get('CUST_NO', '11900874')  # Use secret if set, else default
URL = "https://customer.nesco.gov.bd/pre/panel"
# ====================

bot = Bot(token=BOT_TOKEN)
session = requests.Session()

# 1) GET page to obtain CSRF token
resp = session.get(URL, timeout=20)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

token_input = soup.find("input", {"name": "_token"})
token = token_input["value"] if token_input else None
if not token:
    print("Couldn't find CSRF token on the page.")
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text="⚠ Could not retrieve CSRF token!"))
    raise SystemExit

# 2) POST with customer number
data = {
    "_token": token,
    "cust_no": CUST_NO,
    "submit": "রিচার্জ হিস্ট্রি"
}
post = session.post(URL, data=data, timeout=20)
post.raise_for_status()
soup = BeautifulSoup(post.text, "html.parser")

# 3) Extract balance: take the last disabled <input> on the page
balance = None
inputs = soup.find_all("input", attrs={"disabled": True})

if inputs:
    last_input = inputs[-1]  # last disabled input
    val = (last_input.get("value") or "").strip().replace("\xa0", "").replace(",", "")
    try:
        balance = float(val)
        balance = f"{balance:.2f}"
    except ValueError:
        balance = "N/A"
else:
    balance = "N/A"


# 4) Extract time: find label that contains "অবশিষ্ট ব্যালেন্স" and then its inner <span>
time_info = None
labels = soup.find_all("label")
for lab in labels:
    text = lab.get_text(separator=" ").strip()
    if "অবশিষ্ট ব্যালেন্স" in text:
        span = lab.find("span")
        if span:
            time_info = span.get_text(separator=" ").strip()
        else:
            # maybe the date is in the label text itself
            # try regex date-like extract
            m = re.search(r'\d{1,2}\s+\w+\s+\d{4}.\d{1,2}:\d{2}:\d{2}\s(AM|PM)?', text)
            if m:
                time_info = m.group(0)
        break

# Fallbacks if not found
if not balance:
    balance = "N/A (couldn't parse numeric balance)"
if not time_info:
    # try any span that looks like a datetime
    spans = soup.find_all("span")
    for sp in spans:
        t = sp.get_text(strip=True)
        if re.search(r'\d{4}|\d{1,2}\s+\w+\s+\d{4}', t):
            time_info = t
            break
    if not time_info:
        time_info = "N/A"

# 5) Prepare and send message asynchronously
async def send_telegram():
    message = (
        f"💡 NESCO Prepaid Meter Info\n\n"
        f"🔢 Customer No: {CUST_NO}\n"
        f"💰 Balance: {balance} Taka\n"
        f"🕒 Balance Update Date & Time: \n {time_info}"
    )
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

asyncio.run(send_telegram())

# optional: print for local debugging
print("Customer:", CUST_NO)
print("Balance:", balance)
print("Time:", time_info)


# Workflow code

name: Daily NESCO Balance Check

on:
  workflow_dispatch:  # Keep for manual tests
  schedule:
    - cron: '0 4 * * *'  # Runs at 4:00 AM UTC daily (which is 10:00 AM BST).

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4 python-telegram-bot

      - name: Debug info
        run: |
          echo "UTC Time: $(date)"
          echo "Workflow triggered by: ${{ github.event_name }}"

      - name: Run the script
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
          CUST_NO: ${{ secrets.CUST_NO }}
        run: python script.py
