import mysql.connector
from config import Config
# MySQL 라이브러리에 있는내용이다
def get_connection():
    connection = mysql.connector.connect(
        host = Config.HOST,
        database = Config.DATABASE,
        user = Config.DB_USER,
        password = Config.DB_PASSWORD
    )
    return connection