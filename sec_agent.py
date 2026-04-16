import requests, smtplib, os, json, sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TICKERS = {
    "MSLE": "0001421642", "FDMT": "0001406796", "CORT": "0001088825",
    "SGMO": "0001001233", "NTLA": "0001654531", "QURE": "0001537527"
}
EMAIL_TO = "lfcseenu@gmail.com"
GMAIL_USER = "lfcseenu@gmail.com"
GMAIL_PASS = os.environ.get('GMAIL_PASSWORD')
HEADERS = {'User-Agent': 'Pacifica Research Agent lfcseenu@gmail.com'}

def make_edgar_link(cik, acc):
    acc_clean = acc.replace('-', '')
    cik_int = str(int(cik))
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_clean}/{acc}-index.htm"

def send_mail(subject, body, is_html=False):
    msg = MIMEMultipart('alternative') if is_html else MIMEText(body)
    if is_html:
        msg.attach(MIMEText(body, 'html'))
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = EMAIL_TO
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
                        link = make_edgar_link(cik, acc)
                        send_mail(f"SEC: {ticker} - {form}", f"New filing for {ticker}\nForm: {form}\nDate: {date}\n\nLink: {link}")
                    last_seen[ticker] = acc
        except Exception:
            pass
    with open('last_seen.json', 'w') as f:
        json.dump(last_seen, f)

def summary(hours=13):
    cutoff = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d')
    rows = ""
    print(f"--- STARTING SCAN (last {hours}h) ---")
    print(f"Looking for filings since {cutoff}...")
    for ticker, cik in TICKERS.items():
        try:
            r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                f = r.json()['filings']['recent']
                for i in range(min(10, len(f['filingDate']))):
                    if f['filingDate'][i] >= cutoff:
                        link = make_edgar_link(cik, f['accessionNumber'][i])
                        rows += f"<tr><td>{ticker}</td><td>{f['form'][i]}</td><td>{f['filingDate'][i]}</td><td><a href='{link}'>View</a></td></tr>"
        except Exception:
            continue
    if not rows:
        print("No new filings found. Sending heartbeat email...")
        rows = "<tr><td colspan='4' style='text-align:center; padding: 20px;'>No major filings detected in this period.</td></tr>"
    html = f"<html><body><h2>SEC Filing Update</h2><table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'><thead><tr style='background-color: #f2f2f2;'><th>Ticker</th><th>Form</th><th>Date</th><th>Link</th></tr></thead><tbody>{rows}</tbody></table></body></html>"
    send_mail(f"SEC Update: {datetime.now().strftime('%b %d %I:%M %p')}", html, is_html=True)
    print("SUCCESS: Summary email sent.")

if __name__ == "__main__":
    if "--summary" in sys.argv:
        summary()
    elif "--weekly" in sys.argv:
        summary(hours=168)
    else:
        daily_monitor()
