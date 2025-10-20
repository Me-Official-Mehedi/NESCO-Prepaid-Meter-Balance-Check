import re
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os
from datetime import datetime
import time

# ====== Configuration ======
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
URL = "https://customer.nesco.gov.bd/pre/panel"

# Comma-separated customer numbers (e.g., "11900874,12345678,87654321")
CUST_NUMBERS = os.environ.get('CUST_NO', '11900873,11900874').split(',')

bot = Bot(token=BOT_TOKEN)
session = requests.Session()

# ====== Utility to escape MarkdownV2 ======
def escape_md(text):
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

# ====== Fetch balance and update time with retry ======
def get_balance_and_time(cust_no, retries=3, delay=5):
    for attempt in range(retries):
        try:
            resp = session.get(URL, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            token_input = soup.find("input", {"name": "_token"})
            token = token_input["value"] if token_input else None
            if not token:
                raise ValueError("Token not found")

            data = {"_token": token, "cust_no": cust_no, "submit": "রিচার্জ হিস্ট্রি"}
            post = session.post(URL, data=data, timeout=20)
            soup = BeautifulSoup(post.text, "html.parser")

            # Extract balance
            inputs = soup.find_all("input", attrs={"disabled": True})
            balance = None
            if inputs:
                val = (inputs[-1].get("value") or "").strip().replace("\xa0", "").replace(",", "")
                balance = float(val)

            # Extract last update info
            time_info = "N/A"
            labels = soup.find_all("label")
            for lab in labels:
                if "অবশিষ্ট ব্যালেন্স" in lab.get_text():
                    span = lab.find("span")
                    if span:
                        raw_time = span.get_text(strip=True)
                        try:
                            dt = datetime.strptime(raw_time, "%d %B %Y %I:%M:%S %p")
                            time_info = dt.strftime("%d %b %I:%M %p")
                        except Exception:
                            time_info = raw_time
                    break

            return balance, time_info

        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {cust_no}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return None, None

# ====== Send formatted Telegram summary ======
async def send_summary(results):
    message = (
        "*💡 NESCO Multi-Meter Summary*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

    low_balance_list = []

    for cust_no, balance, time_info in results:
        cust_md = escape_md(cust_no)
        time_md = escape_md(time_info)

        if balance is None:
            message += (
                f"❌ *Meter:* `{cust_md}`\n"
                f"🔸 *Status:* Could not fetch balance.\n\n"
            )
        elif balance <= 50:
            low_balance_list.append((cust_md, balance, time_md))
            message += (
                f"⚠️ *Meter:* `{cust_md}`\n"
                f"💰 *Balance:* *{balance:.2f} Taka — LOW! ⚠️*\n"
                f"🕒 *Updated:* {time_md}\n\n"
            )
        else:
            message += (
                f"✅ *Meter:* `{cust_md}`\n"
                f"💰 *Balance:* {balance:.2f} Taka\n"
                f"🕒 *Updated:* {time_md}\n\n"
            )

    message += "🤖 Auto Update via [Mehedi's](https://www.facebook.com/Me.OfficialMehedi) Bot"

    # Send main summary
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="MarkdownV2")

    # Send extra low balance alert
    if low_balance_list:
        alert_msg = "*🚨 LOW BALANCE ALERT!*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        for cust_no, balance, time_info in low_balance_list:
            alert_msg += (
                f"⚠️ *Meter:* `{cust_no}`\n"
                f"💰 *Current Balance:* *{balance:.2f} Taka*\n"
                f"🕒 *Updated:* {time_info}\n\n"
            )
        alert_msg += "❌ Please recharge soon to avoid power cut ⚡"

        await bot.send_message(chat_id=CHAT_ID, text=alert_msg, parse_mode="MarkdownV2")


# ====== Main Runner ======
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
