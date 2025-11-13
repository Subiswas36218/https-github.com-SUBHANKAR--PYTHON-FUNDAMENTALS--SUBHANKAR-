from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = "mariadb+mariadbconnector://root:samindia@127.0.0.1:3307/Python_DE"


engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20
)

class Base(DeclarativeBase):
    pass

Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

