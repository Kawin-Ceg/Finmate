from datetime import date, timedelta

#  amount sign convention (see routes/transactions.py upload parser):
#  positive amount => credit (income), negative amount => debit (expense)
SAMPLE_CSV = """date,merchant,amount
01/01/2025,SWIGGY ONLINE ORDER,-450.00
03/01/2025,UBER TRIP BOOKING,-180.50
05/01/2025,AMAZON MARKETPLACE,-1200.00
10/01/2025,SALARY CREDIT MONTHLY,50000.00
15/01/2025,NETFLIX SUBSCRIPTION,-499.00
"""


def recent_sample_csv():
    """
    Same five transactions as SAMPLE_CSV but dated within the last 30 days.
    Mate's build_context() computes 'overview'/'top_merchants'/'categories'
    over a rolling 30-day window, so fixed 2025 dates would always fall
    outside it — use this helper for any test that exercises that window.
    """
    today = date.today()

    def d(days_ago):
        return (today - timedelta(days=days_ago)).strftime("%d/%m/%Y")

    return (
        "date,merchant,amount\n"
        f"{d(2)},SWIGGY ONLINE ORDER,-450.00\n"
        f"{d(5)},UBER TRIP BOOKING,-180.50\n"
        f"{d(8)},AMAZON MARKETPLACE,-1200.00\n"
        f"{d(10)},SALARY CREDIT MONTHLY,50000.00\n"
        f"{d(12)},NETFLIX SUBSCRIPTION,-499.00\n"
    )


def upload_sample_csv(client, headers, csv_text=SAMPLE_CSV, filename="statement.csv"):
    return client.post(
        "/transactions/upload",
        headers=headers,
        files={"file": (filename, csv_text, "text/csv")},
    )
