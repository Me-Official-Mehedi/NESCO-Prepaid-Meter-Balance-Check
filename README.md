# ⚡ NESCO Prepaid Meter Balance Checker  

Automate your **NESCO prepaid electricity meter balance checking** using **Python** and **Telegram**. Receive your daily meter balance directly on Telegram without manual checking.  

## 📚 Table of Contents
1. [🧠 Concept Overview](#-concept-overview)
2. [📁 Folder Contents](#-folder-contents)
3. [🧩 Script Types](#-script-types)
4. [📌 Features](#-features)  
5. [🚀 Requirements](#-requirements)  
6. [📝 Step 1: Create GitHub Repository](#-step-1-create-github-repository)  
7. [🔒 Step 2: Secure Your Secrets with GitHub](#-step-2-secure-your-secrets-with-github)  
8. [🖥 Step 3: Update Script to Use Environment Variables](#-step-3-update-script-to-use-environment-variables)  
9. [⚙ Step 4: Set Up GitHub Actions Workflow](#-step-4-set-up-github-actions-workflow)  
10. [🧪 Step 5: Test the Workflow](#-step-5-test-the-workflow)  
11. [📂 Project Structure](#-project-structure)  
12. [🖥️ Output](#️-output)
13. [🧭 Choose Your Mode](#-choose-your-mode)
14. [💡 Tips](#-tips)  
15. [❤️ Support](#️-support)  
16. [👨‍💻 Dev Contact](#-dev-contact)

## 🧠 Concept Overview

There are two modes of operation depending on your need:

🔁 1. Multiple Time Update Per Day

> Sends 3 updates per day if balance ≤ 50

> Sends 1 update per day if balance > 50

Useful for frequent balance monitoring (for example, multiple meters at home)


☀️ 2. Single Time Update Per Day

> Sends only one update per day, regardless of balance

> Suitable for simple daily balance summary

## 📁 Folder Contents

Each folder contains four files — two Python scripts and two matching workflow files:

```
<table>
  <thead>
    <tr>
      <th>📂 Folder Name</th>
      <th>🧾 File Name</th>
      <th>⚙️ Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="4"><b>Multiple Time Update Per Day/</b></td>
      <td><code>single_meter.py</code></td>
      <td>Sends updates <b>3 times a day</b> if balance ≤ 50, otherwise once per day — for <b>single meter</b>.</td>
    </tr>
    <tr>
      <td><code>multiple_meter.py</code></td>
      <td>Same rule as above but for <b>multiple meters</b>.</td>
    </tr>
    <tr>
      <td><code>single_meter_workflow</code></td>
      <td>Workflow file for single meter mode.</td>
    </tr>
    <tr>
      <td><code>multiple_meter_workflow</code></td>
      <td>Workflow file for multiple meter mode.</td>
    </tr>

    <tr>
      <td rowspan="4"><b>Single Time Update Per Day/</b></td>
      <td><code>single_meter.py</code></td>
      <td>Sends update <b>only once per day</b>, regardless of balance — for <b>single meter</b>.</td>
    </tr>
    <tr>
      <td><code>multiple_meter.py</code></td>
      <td>Same rule as above but for <b>multiple meters</b>.</td>
    </tr>
    <tr>
      <td><code>single_meter_workflow</code></td>
      <td>Workflow file for single meter mode.</td>
    </tr>
    <tr>
      <td><code>multiple_meter_workflow</code></td>
      <td>Workflow file for multiple meter mode.</td>
    </tr>
  </tbody>
</table>
```


## 🧩 Script Types

Each mode contains two versions of scripts:

| 🧾 Script Name | ⚙️ Description |
|----------------|----------------|
| `single_meter.py` | Use this if you have **only one meter**. |
| `multiple_meter.py` | Use this if you have **more than one meter**. |

Each version also has a corresponding **workflow file** to match it.

## 📌 Features

- ✅ Automatic daily meter balance check  
- ✅ Sends results directly to your Telegram account  
- ✅ Configurable via **GitHub Actions**  
- ✅ Secure storage of sensitive data (Bot token, Chat ID, Consumer Number) using **GitHub Secrets**  
- ✅ Fully customizable schedule  


## 🚀 Requirements

Before setup, you need:

1. **Telegram Bot** – Create one using [BotFather](https://t.me/BotFather) and get your **Bot Token**.  
2. **Telegram Chat ID** – Get your personal chat ID (where bot sends messages).  
3. **GitHub Account** – To host the script and run workflows.  
4. **Prepaid Meter Consumer Number** – Your NESCO meter consumer number.  
5. **Python 3.12+** installed locally (for local testing, optional).  

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
        run: python script.py// Change as per project structure
```
> This workflow runs your script daily at the specified UTC time. Use crontab.guru
 to customize schedule.

## 🧪 Step 5: Test the Workflow

Go to Actions tab in your repository.

Select Daily NESCO Balance Check from the left panel.

Click Run workflow to test immediately.

Check your Telegram — your bot should send the balance message.

## 📂 Project Structure
<img width="796" height="591" alt="image" src="https://github.com/user-attachments/assets/5bd8e1b5-93a8-4f9f-a2a2-17e62b94b36c" />


## 🖥️ Output
![WhatsApp Image 2025-10-21 at 11 01 20_1cb5bdbd](https://github.com/user-attachments/assets/2372d1b4-de71-4464-b944-c513b515b3bd)

## 🧭 Choose Your Mode

Depending on your needs, replace the files as follows:

✅ For Single Meter + Single Time Update

```
script.py → Single Time Update Per Day/single_meter.py
.github/workflows/daily-run.yml → Single Time Update Per Day/single_meter_workflow
```
✅ For Multiple Meters + Single Time Update
```
script.py → Single Time Update Per Day/multiple_meter.py
.github/workflows/daily-run.yml → Single Time Update Per Day/multiple_meter_workflow
```
✅ For Single Meter + Multiple Time Update
```
script.py → Multiple Time Update Per Day/single_meter.py
.github/workflows/daily-run.yml → Multiple Time Update Per Day/single_meter_workflow
```
✅ For Multiple Meters + Multiple Time Update
```
script.py → Multiple Time Update Per Day/multiple_meter.py
.github/workflows/daily-run.yml → Multiple Time Update Per Day/multiple_meter_workflow
```

## 💡 Tips

Make your repo private if you store secrets for extra safety.

Check GitHub Actions logs for errors if messages are not sent.

Customize Python script to add more functionality like notifications for low balance.

## ❤️ Support

For issues, please open a GitHub Issue in the repository.

## 👨‍💻 Dev Contact-
Name: Md. Mehedi Hasan

Designation : Sub Assistant Engineer (Circle-2, NESCO, Rangpur)

Email: hasanmehedi04286@gamil.com

HRO: HRO-8168
