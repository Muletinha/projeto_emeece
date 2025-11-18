import sqlalchemy
from sqlalchemy import create_engine, text
import os

# conexão com o sql root sem senha
MYSQL_USER = os.getenv("DB_USER", "root")
MYSQL_PASS = os.getenv("DB_PASS", "")
MYSQL_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "projeto_emeece")

# conectando ao servidor SQL
server_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}@{MYSQL_HOST}/"
engine_server = create_engine(server_url, future=True)

def recreate_database():
    with engine_server.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        # drop database se existir e cria novamente
        conn.execute(text(f"DROP DATABASE IF EXISTS `{DB_NAME}`;"))
        conn.execute(text(f"CREATE DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
        print(f"Database `{DB_NAME}` recreated.")

if __name__ == "__main__":
    recreate_database()
