import requests, smtplib, os, json
from email.mime.text import MIMEText

# Your 2026 Biotech Watchlist
TICKERS = {
    "MSLE": "0001840425", "FDMT": "0001406796", "CORT": "0001088825",
    "SGMO": "0001001233", "NTLA": "0001654531", "QURE": "0001537527"
}
EMAIL_TO = "lfcseenu@gmail.com"
GMAIL_USER = "lfcseenu@gmail.com"
GMAIL_PASS = os.environ.get('GMAIL_PASSWORD') 
HEADERS = {'User-Agent': 'Pacifica Research Agent lfcseenu@gmail.com'}

def monitor():
    # 1. Load memory: check what we've seen in the past
    if os.path.exists('last_seen.json'):
        with open('last_seen.json', 'r') as f:
            last_seen = json.load(f)
    else:
        last_seen = {}

    print("Checking SEC for updates...")

    for ticker, cik in TICKERS.items():
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                recent = r.json()['filings']['recent']
                form, date, acc = recent['form'][0], recent['filingDate'][0], recent['accessionNumber'][0]
                
                # If this filing is NEW and NOT a noisy 'Form 4'
                if last_seen.get(ticker) != acc:
                    # Filter for substantive filings only
                    if form != "4" and any(x in form for x in ["8-K", "10-Q", "10-K", "13D", "13G", "13F"]):
                        print(f"!!! New filing found for {ticker}: {form}")
                        send_mail(ticker, form, date, cik, acc)
                    
                    # Update our memory variable
                    last_seen[ticker] = acc
            else:
                print(f"SEC limit or error for {ticker}: {r.status_code}")
        except Exception as e:
            print(f"Skipping {ticker} due to connection error: {e}")

    # 2. ALWAYS save the file at the end so the GitHub Action "Save Memory" step succeeds
    with open('last_seen.json', 'w') as f:
        json.dump(last_seen, f)
    print("Monitor cycle complete.")

def send_mail(ticker, form, date, cik, acc):
    # Professional SEC Viewer link for easy reading on your phone
    xbrl_url = f"https://www.sec.gov/cgi-bin/viewer.cgi?action=view&cik={cik}&accession_number={acc}"
    
    body = f"Alert for {ticker}\nForm: {form}\nDate: {date}\n\nMobile Link: {xbrl_url}\n\nNote: Adverum CVR milestones: $1.78 / $7.13"
    msg = MIMEText(body)
    msg['Subject'] = f"🚨 SEC: {ticker} - {form}"
    msg['From'], msg['To'] = GMAIL_USER, EMAIL_TO
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        print(f"Email sent for {ticker}")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    monitor()
