# ⚡ NESCO Prepaid Meter Balance Checker  

Automate your **NESCO prepaid electricity meter balance checking** using **Python** and **Telegram**. Receive your daily meter balance directly on Telegram without manual checking.  

---

## 📌 Features

- ✅ Automatic daily meter balance check  
- ✅ Sends results directly to your Telegram account  
- ✅ Configurable via **GitHub Actions**  
- ✅ Secure storage of sensitive data (Bot token, Chat ID, Consumer Number) using **GitHub Secrets**  
- ✅ Fully customizable schedule  

---

## 🚀 Requirements

Before setup, you need:

1. **Telegram Bot** – Create one using [BotFather](https://t.me/BotFather) and get your **Bot Token**.  
2. **Telegram Chat ID** – Get your personal chat ID (where bot sends messages).  
3. **GitHub Account** – To host the script and run workflows.  
4. **Prepaid Meter Consumer Number** – Your NESCO meter consumer number.  
5. **Python 3.12+** installed locally (for local testing, optional).  

---

## 📝 Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and log in.  
2. Click **"+" > New repository**.  
3. Name your repo, e.g., `nesco-balance-checker`.  
4. (Optional) Check **Add a README file**.  
5. Click **Create repository**.  
6. On your repo page, click **Add file > Create new file**.  
7. Name it `script.py` and paste your Python script.  
8. Click **Commit new file**.  

> Your script is now safely in the repository.

---

## 🔒 Step 2: Secure Your Secrets with GitHub

Do **not** store sensitive info directly in your code. Use **GitHub Secrets**:  

1. Go to **Settings > Secrets and variables > Actions**.  
2. Click **New repository secret**.  
3. Add the following secrets:  

| Secret Name | Value | Description |
|------------|-------|------------|
| `BOT_TOKEN` | Your Telegram Bot Token | e.g., `8208090466:AAHfPXa64FYmR_OHJxV_S5Xcfhftfydty` |
| `CHAT_ID` | Your Telegram Chat ID | e.g., `1609615864` |
| `CUST_NO` | Your Prepaid Meter Consumer Number | e.g., `11900874` |

> Secrets are encrypted and accessible only during GitHub Actions runs.

---

## 🖥 Step 3: Update Script to Use Environment Variables

Replace sensitive values in your Python script with:

```
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
CUST_NO = os.environ.get('CUST_NO')
```
> This ensures your secrets remain safe.

## ⚙ Step 4: Set Up GitHub Actions Workflow

In your repo, click Add file > Create new file.

Name it .github/workflows/daily-run.yml (create folders in path).

Paste the following YAML:
```
name: Daily NESCO Balance Check

on:
  workflow_dispatch:  # Manual trigger for testing
  schedule:
    - cron: '0 4 * * *' # Runs at 4:00 AM UTC daily (adjust as needed)

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

      - name: Run the script
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
          CUST_NO: ${{ secrets.CUST_NO }}
        run: python script.py
```
> This workflow runs your script daily at the specified UTC time. Use crontab.guru
 to customize schedule.

## 🧪 Step 5: Test the Workflow

Go to Actions tab in your repository.

Select Daily NESCO Balance Check from the left panel.

Click Run workflow to test immediately.

Check your Telegram — your bot should send the balance message.

## 📂 Project Structure
<img width="355" height="224" alt="image" src="https://github.com/user-attachments/assets/c16af960-fc60-4481-96b0-760b25633694" />

## 🖥️ Output
![WhatsApp Image 2025-10-18 at 11 19 46_5517e4ad](https://github.com/user-attachments/assets/eaf203af-334d-47c1-ab6b-ad9348cac7f8)

## 💡 Tips

Make your repo private if you store secrets for extra safety.

Check GitHub Actions logs for errors if messages are not sent.

Customize Python script to add more functionality like notifications for low balance.

## ❤️ Support

For issues, please open a GitHub Issue in the repository...
