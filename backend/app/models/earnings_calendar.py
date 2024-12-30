from google.cloud import bigquery

earnings_calendar_schema = [
    bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("company_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("fiscal_year", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("fiscal_quarter", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("announcement_date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
] 