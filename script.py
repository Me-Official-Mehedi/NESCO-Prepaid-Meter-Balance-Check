import re
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os
from datetime import datetime
import asyncio

# ====== Configuration ======
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
URL = "https://customer.nesco.gov.bd/pre/panel"

# Single customer number
CUST_NO = os.environ.get('CUST_NO', '11900873')

bot = Bot(token=BOT_TOKEN)
session = requests.Session()


# ====== Fetch balance and update time ======
def get_balance_and_time(cust_no):
    try:
        resp = session.get(URL, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        token_input = soup.find("input", {"name": "_token"})
        token = token_input["value"] if token_input else None
        if not token:
            return None, None

        data = {"_token": token, "cust_no": cust_no, "submit": "রিচার্জ হিস্ট্রি"}
        post = session.post(URL, data=data, timeout=20)
        soup = BeautifulSoup(post.text, "html.parser")

        # Extract balance
        inputs = soup.find_all("input", attrs={"disabled": True})
        balance = None
        if inputs:
            val = (inputs[-1].get("value") or "").strip().replace("\xa0", "").replace(",", "")
            try:
                balance = float(val)
            except ValueError:
                balance = None

        # Extract last update info
        time_info = None
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

        return balance, time_info or "N/A"

    except Exception as e:
        print(f"Error for {cust_no}: {e}")
        return None, None


# ====== Send formatted Telegram summary ======
async def send_summary(cust_no, balance, time_info):
    message = "💡 *NESCO Single Meter Summary*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    low_balance_alert = False

    if balance is None:
        message += (
            f"❌ *Meter:* {cust_no}\n"
            f"🔸 *Status:* Could not fetch balance.\n\n"
        )
    elif balance <= 50:
        low_balance_alert = True
        message += (
            f"⚠️ *Meter:* {cust_no}\n"
            f"💰 *Balance:* *{balance:.2f} Taka — LOW! ⚠️*\n"
            f"🕒 *Updated:* {time_info}\n\n"
        )
    else:
        message += (
            f"✅ *Meter:* {cust_no}\n"
            f"💰 *Balance:* {balance:.2f} Taka\n"
            f"🕒 *Updated:* {time_info}\n\n"
        )

    message += "🤖 Auto Update via [Mehedi's](https://www.facebook.com/Me.OfficialMehedi) Bot"
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

    # Separate LOW BALANCE ALERT message
    if low_balance_alert:
        alert_msg = (
            "🚨 *LOW BALANCE ALERT!*\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Meter:* {cust_no}\n"
            f"💰 *Current Balance:* *{balance:.2f} Taka*\n"
            f"🕒 *Updated:* {time_info}\n\n"
            "❌ Please recharge soon to avoid power cut ⚡"
        )
        await bot.send_message(chat_id=CHAT_ID, text=alert_msg, parse_mode="Markdown")


# ====== Main Runner ======
def main():
    balance, time_info = get_balance_and_time(CUST_NO)
    asyncio.run(send_summary(CUST_NO, balance, time_info))


if __name__ == "__main__":
    main()