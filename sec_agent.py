def weekly_summary():
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    rows = ""
    print(f"Searching for filings since {seven_days_ago}...")
    for ticker, cik in TICKERS.items():
        try:
            r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HEADERS, timeout=10)
            if r.status_code == 200:
                f = r.json()['filings']['recent']
                for i in range(min(10, len(f['filingDate']))):
                    if f['filingDate'][i] >= seven_days_ago:
                        link = f"https://www.sec.gov/cgi-bin/viewer.cgi?action=view&cik={cik}&accession_number={f['accessionNumber'][i]}"
                        rows += f"<tr><td>{ticker}</td><td>{f['form'][i]}</td><td>{f['filingDate'][i]}</td><td><a href='{link}'>View</a></td></tr>"
        except Exception: continue
    
    # This part forces an email even if no filings were found
    if not rows:
        rows = "<tr><td colspan='4' style='text-align:center; padding: 20px;'>No major filings detected in the last 7 days.</td></tr>"
        
    html = f"<html><body><h2>Weekly SEC Summary</h2><table border='1' cellpadding='8' style='border-collapse: collapse; width: 100%;'><thead><tr style='background-color: #f2f2f2;'><th>Ticker</th><th>Form</th><th>Date</th><th>Link</th></tr></thead><tbody>{rows}</tbody></table><p>System Status: Active.</p></body></html>"
    send_mail(f"📊 Weekly Recap: {datetime.now().strftime('%b %d')}", html, is_html=True)
    print("Weekly summary email sent successfully.") # This line will appear in your logs
