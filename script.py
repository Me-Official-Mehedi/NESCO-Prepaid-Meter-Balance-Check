import re
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Bot
import os
import json
from datetime import datetime, timedelta
import os.path as path

# ====== Config ======
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
CUST_NO = os.environ.get('CUST_NO', '11900874')
URL = "https://customer.nesco.gov.bd/pre/panel"
LOW_BALANCE_THRESHOLD = 50.0
LOW_BALANCE_MESSAGE = "⚠️ Warning: Balance is below 50 Taka! Please recharge soon."
STATE_FILE = "nesco_state.json"

# Timing config for Bangladesh Time (UTC+6)
# 10:00 AM BDT = 4:00 AM UTC
# Low balance: 10AM, 4PM, 10PM BDT = 4AM, 10AM, 4PM UTC
# Normal balance: 10AM BDT = 4AM UTC
LOW_BALANCE_INTERVAL = timedelta(hours=6)  # Every 6 hours for 3x daily
NORMAL_BALANCE_INTERVAL = timedelta(hours=24)  # Every 24 hours for 1x daily
# ====================

bot = Bot(token=BOT_TOKEN)
session = requests.Session()

def load_state():
    """Load previous balance state from file"""
    if path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                if 'last_notification' not in state:
                    state['last_notification'] = None
                return state
        except Exception as e:
            print(f"Error loading state: {e}")
            return {}
    return {}

def save_state(balance_float, is_low, last_notif_time):
    """Save current balance state to file"""
    state = {
        "last_balance": balance_float,
        "is_low_balance": is_low,
        "last_updated": datetime.now().isoformat(),
        "last_notification": last_notif_time.isoformat() if last_notif_time else None
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, default=str)
    print(f"State saved: low_balance={is_low}, last_notif={last_notif_time}")

def should_send_notification(state, is_low_balance, current_time):
    """Determine if we should send a notification based on balance and timing"""
    last_notif = state.get('last_notification')
    
    if last_notif is None:
        print("First run - sending notification")
        return True
    
    last_notif_time = datetime.fromisoformat(last_notif)
    time_diff = current_time - last_notif_time
    
    if is_low_balance:
        # Low balance: send every 6 hours (3 times daily)
        should_send = time_diff >= LOW_BALANCE_INTERVAL
        print(f"Low balance check: {time_diff} >= 6h? {should_send}")
        return should_send
    else:
        # Normal balance: send every 24 hours (once daily)
        should_send = time_diff >= NORMAL_BALANCE_INTERVAL
        print(f"Normal balance check: {time_diff} >= 24h? {should_send}")
        return should_send

def get_schedule_info(is_low):
    """Get human-readable schedule info"""
    if is_low:
        return "3 times daily (10AM, 4PM, 10PM BDT)"
    else:
        return "once daily (10AM BDT)"

# Load previous state
prev_state = load_state()
was_low_balance = prev_state.get("is_low_balance", False)
current_time = datetime.now()

print(f"Current time: {current_time}")
print(f"Previous low balance: {was_low_balance}")

# 1) GET page to obtain CSRF token
try:
    resp = session.get(URL, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    token_input = soup.find("input", {"name": "_token"})
    token = token_input["value"] if token_input else None
    if not token:
        raise Exception("Couldn't find CSRF token on the page.")

    # 2) POST with customer number
    data = {
        "_token": token,
        "cust_no": CUST_NO,
        "submit": "রিচার্জ হিস্ট্রি"
    }
    post = session.post(URL, data=data, timeout=20)
    post.raise_for_status()
    soup = BeautifulSoup(post.text, "html.parser")

    # 3) Extract balance
    balance = None
    balance_float = None
    inputs = soup.find_all("input", attrs={"disabled": True})

    if inputs:
        last_input = inputs[-1]
        val = (last_input.get("value") or "").strip().replace("\xa0", "").replace(",", "")
        try:
            balance_float = float(val)
            balance = f"{balance_float:.2f}"
        except ValueError:
            balance = "N/A"
            balance_float = None
    else:
        balance = "N/A"
        balance_float = None

    # 4) Extract time
    time_info = None
    labels = soup.find_all("label")
    for lab in labels:
        text = lab.get_text(separator=" ").strip()
        if "অবশিষ্ট ব্যালেন্স" in text:
            span = lab.find("span")
            if span:
                time_info = span.get_text(separator=" ").strip()
            else:
                m = re.search(r'\d{1,2}\s+\w+\s+\d{4}.\d{1,2}:\d{2}:\d{2}\s(AM|PM)?', text)
                if m:
                    time_info = m.group(0)
            break

    if not time_info:
        spans = soup.find_all("span")
        for sp in spans:
            t = sp.get_text(strip=True)
            if re.search(r'\d{4}|\d{1,2}\s+\w+\s+\d{4}', t):
                time_info = t
                break
        if not time_info:
            time_info = "N/A"

    # Determine current status
    is_low_balance = balance_float is not None and balance_float < LOW_BALANCE_THRESHOLD
    state_changed = is_low_balance != was_low_balance
    
    # Check if we should send notification
    should_notify = should_send_notification(prev_state, is_low_balance, current_time)
    
    print(f"Current balance: {balance_float}")
    print(f"Is low balance: {is_low_balance}")
    print(f"Should send notification: {should_notify}")
    print(f"State changed: {state_changed}")
    print(f"Monitoring: {get_schedule_info(is_low_balance)}")

    # Prepare message
    message = (
        f"💡 NESCO Meter Info\n\n"
        f"🔢 Customer No: `{CUST_NO}`\n"
        f"💰 Balance: `{balance}` Taka\n"
        f"🕒 Time: {time_info}\n"
        f"📅 Checked: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    if is_low_balance:
        message += f"\n\n{LOW_BALANCE_MESSAGE}"
        message += f"\n\n⏰ Monitoring: {get_schedule_info(True)}"

    # Send notification if conditions are met
    async def send_telegram():
        sent = False
        if should_notify:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            sent = True
            print("✅ Notification sent!")
            
            # Send state change alert if balance crossed threshold
            if state_changed:
                status = "LOW ⚠️" if is_low_balance else "NORMAL ✅"
                schedule_info = get_schedule_info(is_low_balance)
                alert_msg = (
                    f"📊 *Balance Status Changed*\n\n"
                    f"Status: {status}\n"
                    f"Balance: {balance} Taka\n\n"
                    f"🔄 Monitoring frequency: {schedule_info}\n"
                    f"{'⚠️ Please recharge soon!' if is_low_balance else '✅ Balance is safe'}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=alert_msg, parse_mode="Markdown")
                print(f"🚨 State change alert sent: {status}")
        
        # Save state with notification timestamp only if we sent a message
        last_notif_time = current_time if sent else prev_state.get('last_notification')
        if last_notif_time:
            last_notif_time = datetime.fromisoformat(last_notif_time) if isinstance(last_notif_time, str) else last_notif_time
        
        save_state(balance_float, is_low_balance, last_notif_time)
        
        if not should_notify:
            print("⏭️ Skipping notification - recent update already sent")

    asyncio.run(send_telegram())

except Exception as e:
    error_msg = f"❌ Error checking NESCO balance: {str(e)}\n\nPlease check manually."
    print(f"Error: {error_msg}")
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=error_msg, parse_mode="Markdown"))
    except:
        pass
    raise
