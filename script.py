import re
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os
from datetime import datetime, timezone, timedelta

# ====== Config ======
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
CUST_NO = os.environ.get('CUST_NO', '11900874')
URL = "https://customer.nesco.gov.bd/pre/panel"
# ====================

bot = Bot(token=BOT_TOKEN)
session = requests.Session()

def get_balance_and_time(cust_no):
    """Fetch balance and time info for a customer number"""
    resp = session.get(URL, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    token_input = soup.find("input", {"name": "_token"})
    token = token_input["value"] if token_input else None
    if not token:
        raise Exception("CSRF token not found")

    data = {"_token": token, "cust_no": cust_no, "submit": "রিচার্জ হিস্ট্রি"}
    post = session.post(URL, data=data, timeout=20)
    post.raise_for_status()
    soup = BeautifulSoup(post.text, "html.parser")

    # Extract balance
    balance = None
    inputs = soup.find_all("input", attrs={"disabled": True})
    if inputs:
        val = (inputs[-1].get("value") or "").strip().replace("\xa0", "").replace(",", "")
        try:
            balance = float(val)
        except ValueError:
            balance = None

    # Extract time
    time_info = None
    labels = soup.find_all("label")
    for lab in labels:
        if "অবশিষ্ট ব্যালেন্স" in lab.get_text():
            span = lab.find("span")
            if span:
                time_info = span.get_text(strip=True)
            break

    if not time_info:
        spans = soup.find_all("span")
        for sp in spans:
            t = sp.get_text(strip=True)
            if re.search(r'\d{4}|\d{1,2}\s+\w+\s+\d{4}', t):
                time_info = t
                break

    return balance, time_info or "N/A"

async def send_message(balance, time_info):
    """Send Telegram message with appropriate alert"""
    if balance is None:
        text = f"⚠ Could not fetch balance for Customer {CUST_NO}."
    elif balance <= 50:
        text = (
            "⚠️ *Low Balance Alert!*\n\n"
            f"💡 *NESCO Prepaid Meter Info*\n\n"
            f"🔢 Customer No: `{CUST_NO}`\n"
            f"💰 *Balance:* {balance:.2f} Taka\n"
            f"🕒 *Last Updated:* {time_info}\n\n"
            f"🚨 Please Recharge Soon!"
        )
    else:
        text = (
            f"💡 *NESCO Prepaid Meter Info*\n\n"
            f"🔢 Customer No: `{CUST_NO}`\n"
            f"💰 Balance: {balance:.2f} Taka\n"
            f"🕒 Balance Update Date & Time: {time_info}"
        )

    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")

def main():
    balance, time_info = get_balance_and_time(CUST_NO)
    asyncio.run(send_message(balance, time_info))
    print(f"Customer: {CUST_NO}\nBalance: {balance}\nTime: {time_info}")

if __name__ == "__main__":
    main()
