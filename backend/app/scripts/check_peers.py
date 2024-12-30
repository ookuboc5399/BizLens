from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Create database connection
engine = create_engine(os.getenv('DATABASE_URL'))
Session = sessionmaker(bind=engine)
session = Session()

def check_peer_companies():
    # Query companies in Consumer Electronics industry
    result = session.execute(
        text('SELECT name, ticker, industry FROM company WHERE industry = :industry'),
        {'industry': 'Consumer Electronics'}
    )
    companies = result.fetchall()

    print('\nCompanies in Consumer Electronics industry:')
    for company in companies:
        print(f'Name: {company.name}, Ticker: {company.ticker}, Industry: {company.industry}')

    # Also check unique industries to see what we have
    industries = session.execute(text('SELECT DISTINCT industry FROM company'))
    print('\nAll unique industries in database:')
    for industry in industries:
        print(industry[0])

if __name__ == '__main__':
    check_peer_companies()
