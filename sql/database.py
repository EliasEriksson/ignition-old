import json
from pathlib import Path
from sqlalchemy import create_engine, DDL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


with Path(__file__).parent.joinpath(".credentials.json").open("r") as file:
    cred = json.load(file)

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{cred['role']}:{cred['password']}@"
    f"{cred['host']}:{cred['port']}/{cred['db']}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
