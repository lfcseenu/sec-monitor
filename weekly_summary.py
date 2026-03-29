import requests, smtplib, os, json
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TICKERS = {
    "MSLE": "0001840425", "FDMT": "0001406796", "CORT": "0001088825",
    "SGMO": "0001001233", "NTLA": "0001654531", "QURE": "0001537527"
}
EMAIL_TO = "lfcseenu@gmail.com"
GMAIL_USER = "lfcseenu@gmail.com"
GMAIL_PASS = os.environ.get('GMAIL_PASSWORD')
HEADERS = {'User-Agent': 'Pacifica Weekly Summary lfcseenu@gmail.com'}

def get_weekly_report():
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    summary_data = []

    for ticker, cik in TICKERS.items():
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                filings = r.json()['filings']['recent']
                for i in range(len(filings['filingDate'])):
                    f_date = filings['filingDate'][i]
                    if f_date >= seven_days_ago:
                        form = filings['form'][i]
                        acc = filings['accessionNumber'][i]
                        # Professional link for the table
                        link = f"https://www.sec.gov/cgi-bin/viewer.cgi?action=view&cik={cik}&accession_number={acc}"
                        summary_data.append({'ticker': ticker, 'form': form, 'date': f_date, 'link': link})
                    else:
                        break # Stop looking once filings are older than 7 days
        except Exception:
            continue

    if summary_data:
        send_summary_email(summary_data)

def send_summary_email(data):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"📊 Weekly Biotech Recap: {datetime.now().strftime('%b %d')}"
    msg['From'], msg['To'] = GMAIL_USER, EMAIL_TO

    # Building a nice HTML table for your phone
    table_rows = "".join([f"<tr><td>{d['ticker']}</td><td>{d['form']}</td><td>{d['date']}</td><td><a href='{d['link']}'>View</a></td></tr>" for d in data])
    
    html = f"""
    <html>
      <body>
        <h2>Weekly SEC Filing Summary</h2>
        <table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">
          <tr style="background-color: #f2f2f2;"><th>Ticker</th><th>Form</th><th>Date</th><th>Link</th></tr>
          {table_rows}
        </table>
        <p><i>Context: Adverum CVR ($1.78/$7.13) | FDMT Durability Watch</i></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)

if __name__ == "__main__":
    get_weekly_report()
