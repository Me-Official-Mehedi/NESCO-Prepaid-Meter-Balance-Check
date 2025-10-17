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
# ====================

bot = Bot(token=BOT_TOKEN)
session = requests.Session()

def load_state():
    """Load previous balance state from file"""
    if path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                # Ensure last_notification time exists and is recent
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
    print(f"State saved: {state}")

def should_send_notification(state, is_low_balance, current_time):
    """Determine if we should send a notification based on balance and timing"""
    last_notif = state.get('last_notification')
    
    if last_notif is None:
        return True  # First run, always send
    
    last_notif_time = datetime.fromisoformat(last_notif)
    
    # For low balance: send every 12 hours (twice daily)
    if is_low_balance:
        time_diff = current_time - last_notif_time
        return time_diff >= timedelta(hours=12)
    
    # For normal balance: send every 24 hours (once daily)
    else:
        time_diff = current_time - last_notif_time
        return time_diff >= timedelta(hours=24)

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
    else:
        balance = "N/A"

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

    # Prepare message
    message = (
        f"💡 NESCO Meter Info\n\n"
        f"🔢 Customer No: {CUST_NO}\n"
        f"💰 Balance: {balance} Taka\n"
        f"🕒 Time: {time_info}"
    )

    if is_low_balance:
        message += f"\n\n{LOW_BALANCE_MESSAGE}"

    # Send notification if conditions are met
    async def send_telegram():
        sent = False
        if should_notify:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            sent = True
            print("Notification sent!")
            
            # Send state change alert if balance crossed threshold
            if state_changed:
                status = "LOW ⚠️" if is_low_balance else "NORMAL ✅"
                alert_msg = f"📊 Balance Status Changed to: {status}\n\nMonitoring frequency adjusted:\n• {'Twice daily' if is_low_balance else 'Once daily'}"
                await bot.send_message(chat_id=CHAT_ID, text=alert_msg, parse_mode="Markdown")
                print(f"State change alert sent: {status}")
        
        # Save state with notification timestamp only if we sent a message
        last_notif_time = current_time if sent else prev_state.get('last_notification')
        save_state(balance_float, is_low_balance, last_notif_time)
        
        if not should_notify:
            print("Skipping notification - recent update already sent")

    asyncio.run(send_telegram())

except Exception as e:
    error_msg = f"❌ Error checking balance: {str(e)}"
    print(error_msg)
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=error_msg))
    raise




name: NESCO Balance Monitor

on:
  schedule:
    # Run twice daily at 8AM and 8PM UTC (adjust for your timezone)
    - cron: '0 8,20 * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  monitor-balance:
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
        python -m pip install --upgrade pip
        pip install requests beautifulsoup4 python-telegram-bot
        
    - name: Create state directory
      run: mkdir -p .github/state
      
    - name: Run balance check
      env:
        BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
        CHAT_ID: ${{ secrets.CHAT_ID }}
        CUST_NO: ${{ secrets.CUST_NO }}
      run: python nesco_monitor.py  # Replace with your script filename
      
    - name: Commit state file (optional - for persistence)
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add nesco_state.json
        if git diff --staged --quiet; then
          echo "No changes to commit"
        else
          git commit -m "Update NESCO state [skip ci]"
          git push
        fi
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      continue-on-error: true
