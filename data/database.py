# data/database.py

import pyodbc
import pymysql
from pymysql.constants import CLIENT
from utils.config import (
    access_conn_str,
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE,
)

class DatabaseManager:
    """Singleton holder for local Access & remote MySQL connections."""

    _access_cnx = None
    _mysql_cnx  = None

    @classmethod
    def access_connection(cls) -> pyodbc.Connection:
        """
        Returns a live pyodbc.Connection to the local Access DB.
        Uses access_conn_str() from utils.config.
        """
        if cls._access_cnx is None:
            conn_str = access_conn_str()
            cls._access_cnx = pyodbc.connect(conn_str, autocommit=True)
        return cls._access_cnx

    @classmethod
    def mysql_connection(cls) -> pymysql.Connection:
        """
        Returns a live pymysql.Connection to the remote MySQL DB.
        """
        if cls._mysql_cnx is None:
            cls._mysql_cnx = pymysql.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                client_flag=CLIENT.MULTI_STATEMENTS,
                autocommit=True,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )
        return cls._mysql_cnx
