from datetime import datetime
from sqlalchemy.orm import Session
from app.models.company import Base, Company
from app.services.database import engine

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)

    # Add sample companies
    with Session(engine) as session:
        companies = [
            Company(
                id="AAPL_US",  # 明示的にIDを設定
                name="Apple Inc.",
                ticker="AAPL",
                country="USA",
                sector="Technology",
                industry="Consumer Electronics",
                description="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                employees=164000,
                established_date=datetime.strptime("1977-01-03", "%Y-%m-%d").date()
            ),
            Company(
                id="SONY_JP",  # 明示的にIDを設定
                name="Sony Group Corporation",
                ticker="SONY",
                country="Japan",
                sector="Technology",
                industry="Consumer Electronics",
                description="Sony Group Corporation designs, develops, produces, and sells electronic equipment, instruments, and devices worldwide.",
                employees=109700,
                established_date=datetime.strptime("1946-05-07", "%Y-%m-%d").date()
            ),
            Company(
                id="005930_KR",  # 明示的にIDを設定
                name="Samsung Electronics Co., Ltd.",
                ticker="005930.KS",
                country="South Korea",
                sector="Technology",
                industry="Consumer Electronics",
                description="Samsung Electronics Co., Ltd. engages in the consumer electronics, information technology and mobile communications, and device solutions businesses worldwide.",
                employees=267937,
                established_date=datetime.strptime("1969-01-13", "%Y-%m-%d").date()
            )
        ]

        session.add_all(companies)
        session.commit()

    print("Database tables recreated and sample data added successfully")

if __name__ == "__main__":
    reset_database()
