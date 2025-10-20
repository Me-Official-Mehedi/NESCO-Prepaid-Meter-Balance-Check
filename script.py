import re
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os

BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
URL = "https://customer.nesco.gov.bd/pre/panel"

# Comma-separated customer numbers (e.g., "11900874,12345678,87654321")
CUST_NUMBERS = os.environ.get('CUST_NO', '11900873,11900874').split(',')

bot = Bot(token=BOT_TOKEN)
session = requests.Session()

def get_balance_and_time(cust_no):
    resp = session.get(URL, timeout=20)
    soup = BeautifulSoup(resp.text, "html.parser")
    token_input = soup.find("input", {"name": "_token"})
    token = token_input["value"] if token_input else None
    if not token:
        return None, None

    data = {"_token": token, "cust_no": cust_no, "submit": "রিচার্জ হিস্ট্রি"}
    post = session.post(URL, data=data, timeout=20)
    soup = BeautifulSoup(post.text, "html.parser")

    inputs = soup.find_all("input", attrs={"disabled": True})
    balance = None
    if inputs:
        val = (inputs[-1].get("value") or "").strip().replace("\xa0", "").replace(",", "")
        try:
            balance = float(val)
        except ValueError:
            balance = None

    time_info = None
    labels = soup.find_all("label")
    for lab in labels:
        if "অবশিষ্ট ব্যালেন্স" in lab.get_text():
            span = lab.find("span")
            if span:
                time_info = span.get_text(strip=True)
            break

    return balance, time_info or "N/A"

async def send_summary(results):
    message = (
        "💡 *NESCO Multi-Meter Summary*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    for cust_no, balance, time_info in results:
        if balance is None:
            message += f"❌ *Meter:* `{cust_no}`\n🔸 *Status:* Could not fetch balance\n\n"
        elif balance <= 50:
            message += (
                f"⚠️ *Meter:* `{cust_no}`\n"
                f"💰 *Balance:* {balance:.2f} Taka (Low!)\n"
                f"🕒 *Updated:* {time_info}\n\n"
            )
        else:
            message += (
                f"✅ *Meter:* `{cust_no}`\n"
                f"💰 *Balance:* {balance:.2f} Taka\n"
                f"🕒 *Updated:* {time_info}\n\n"
            )
    message += "━━━━━━━━━━━━━━━━━━━━━━━\n📅 *Auto Updated by NESCO Bot*"
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")


def main():
    results = []
    for cust in CUST_NUMBERS:
        cust = cust.strip()
        if cust:
            bal, time_info = get_balance_and_time(cust)
            results.append((cust, bal, time_info))
    asyncio.run(send_summary(results))

if __name__ == "__main__":
    main()
