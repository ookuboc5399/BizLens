from google.cloud import bigquery

earnings_companies_schema = [
    bigquery.SchemaField("code", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("company_name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
] 