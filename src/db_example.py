from sqlalchemy import create_engine, text;


DATABASE_URL = "mariadb+mariadbconnector://root:samindia@127.0.0.1:3307/Python_DE"

engine = create_engine(
    DATABASE_URL,
    echo=True, # Log SQL queries
    pool_size=10, # Connection pool size
    max_overflow=20 # Additional connections
)

# Test connection
with engine.connect() as connection:
    with connection.begin():
        sql = text("INSERT INTO users (username, email) VALUES (:username, :email)")
        params = {"username": "john", "email": "john@example.com"}
        result = connection.execute(sql, params)