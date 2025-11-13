from sqlalchemy import create_engine, text, select
from sqlalchemy import (
    MetaData, Table, Column,
    Integer, String, DateTime,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime

DATABASE_URL = "mariadb+mariadbconnector://root:samindia@127.0.0.1:3307/Python_DE"

engine = create_engine(
    DATABASE_URL,
    echo=True, # Log SQL queries
    pool_size=10, # Connection pool size
    max_overflow=20 # Additional connections
)

# metadata = MetaData()

# users_table = Table(
#    'users',
#    metadata,
#    Column('id', Integer, primary_key=True),
#    Column('username', String(50), nullable=False, unique=True),
#    Column('email', String(120), nullable=False),
#    Column('created_at', DateTime, default=datetime.utcnow)
# )

# comments_table = Table(
#    'comments',
#    metadata,
#    Column('id', Integer, primary_key=True),
#    Column('user_id', Integer, nullable=False),
#    Column('content', String(500), nullable=False),
#    Column('created_at', DateTime, default=datetime.utcnow)
# )


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
#    id = Column(Integer, primary_key=True)
#    username = Column(String(50), nullable=False, unique=True)
#    email = Column(String(120), nullable=False)
#    created_at = Column(DateTime, default=datetime.utcnow)
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

with Session() as session:
        query = select(User).where(User.username == "bob")
        result = session.execute(query)
        user = result.scalars().first()

        if user is None:
            print("No user found with username 'bob'")
        else:
            print(user.username, user.email)
            user.email = "bob123@yahoo.com"
            session.commit()