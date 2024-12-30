from google.cloud import bigquery
from datetime import datetime

def insert_earnings_data(date: str, companies: list):
    client = bigquery.Client()
    
    # earnings_calendar テーブルへの挿入
    calendar_row = {
        "date": date,
        "company_count": len(companies),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    # earnings_companies テーブルへの挿入用データ
    companies_rows = []
    for company in companies:
        companies_rows.append({
            "id": f"{date}_{company['code']}",
            "date": date,
            "company_code": company["code"],
            "company_name": company["name"],
            "market": company.get("market"),
            "fiscal_year": company.get("fiscal_year"),
            "quarter": company.get("quarter"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

    # データ挿入
    try:
        client.insert_rows_json("your-project.BuffetCodeClone.earnings_calendar", [calendar_row])
        client.insert_rows_json("your-project.BuffetCodeClone.earnings_companies", companies_rows)
        return True
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False 