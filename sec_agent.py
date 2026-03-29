import requests, smtplib, os, json, sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 🎯 THE MASTER WATCHLIST (Update Here Only)
# ==========================================
TICKERS = {
    "MSLE": "0001421642", "DTIL": "0001357874", "FDMT": "0001650648", 
    "CORT": "0001088856", "SGMO": "0001001233", "NTLA": "0001652130", 
    "QURE": "0001590560", "ADVM": "0001381434"
}

EMAIL_TO = "lfcseenu@gmail.com"
GMAIL_USER = "lfcseenu@gmail.com"
GMAIL_PASS = os.environ.get('GMAIL_PASSWORD')
HEADERS = {'User-Agent': 'Pacifica Investment Agent lfcseenu@gmail.com'}
CVR_NOTE = "Note: Adverum CVR milestones: $1.78 / $7.13 | FDMT Durability Watch"

def send_mail(subject, body, is_html=False):
    msg = MIMEMultipart('alternative') if is_html else MIMEText(body)
    if is_html: msg.attach(MIMEText(body, 'html'))
    msg['Subject'], msg['From'], msg['To'] = subject, GMAIL_USER, EMAIL_TO
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

def daily_monitor():
    last_seen = json.load(open('last_seen.json')) if os.path.exists('last_seen.json') else {}
    for ticker, cik in TICKERS.items():
        try:
            r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                f = r.json()['filings']['recent']
                form, date, acc = f['form'][0], f['filingDate'][0], f['accessionNumber'][0]
                if last_seen.get(ticker) != acc:
                    if form != "4" and any(x in form for x in ["8-K", "10-Q", "10-K", "13D", "13G", "13F"]):
                        link = f"https://www.sec.gov/cgi-bin/viewer.cgi?action=view&cik={cik}&accession_number={acc}"
                        send_mail(f"🚨 SEC: {ticker} - {form}", f"New filing for {ticker}\nForm: {form}\nDate: {date}\n\nLink: {link}\n\n{CVR_NOTE}")
                    last_seen[ticker] = acc
        except Exception: pass
    with open('last_seen.json', 'w') as f: json.dump(last_seen, f)

def weekly_summary():
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    rows = ""
    for ticker, cik in TICKERS.items():
        try:
            r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                f = r.json()['filings']['recent']
                for i in range(min(5, len(f['filingDate']))):
                    if f['filingDate'][i] >= seven_days_ago:
                        link = f"https://www.sec.gov/cgi-bin/viewer.cgi?action=view&cik={cik}&accession_number={f['accessionNumber'][i]}"
                        rows += f"<tr><td>{ticker}</td><td>{f['form'][i]}</td><td>{f['filingDate'][i]}</td><td><a href='{link}'>View</a></td></tr>"
        except Exception: continue
    if rows:
        html = f"<html><body><h2>Weekly SEC Summary</h2><table border='1' cellpadding='5' style='border-collapse: collapse;'><tr><th>Ticker</th><th>Form</th><th>Date</th><th>Link</th></tr>{rows}</table><p>{CVR_NOTE}</p></body></html>"
        send_mail(f"📊 Weekly Recap: {datetime.now().strftime('%b %d')}", html, is_html=True)

if __name__ == "__main__":
    if "--weekly" in sys.argv: weekly_summary()
    else: daily_monitor()
