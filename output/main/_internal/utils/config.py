# utils/config.py

from pathlib import Path
from dotenv import load_dotenv
import os

# Optional: load .env for sensitive values instead of hard-coding
load_dotenv()

# Root of the project (one level up from utils/)
ROOT_DIR = Path(__file__).resolve().parents[1]

# Local Access DB file
ACCESS_DB_PATH = ROOT_DIR / "data" / "LMS_DB.accdb"

# Remote MySQL credentials
MYSQL_HOST     = os.getenv("LMS_MYSQL_HOST",    "82.197.82.52")
MYSQL_USER     = os.getenv("LMS_MYSQL_USER",    "u569981245_LMS_Admin")
MYSQL_PASSWORD = os.getenv("LMS_MYSQL_PASSWORD","Rfmtl2024!admin")
MYSQL_DATABASE = os.getenv("LMS_MYSQL_DB",      "u569981245_LMS")

def access_conn_str() -> str:
    """
    Return the ODBC connection string for the local Access DB.
    """
    return (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={ACCESS_DB_PATH};"
    )
