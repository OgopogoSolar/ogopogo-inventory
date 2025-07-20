"""
init_access_db.py
-----------------
Create or recreate **all** local tables inside LMS_DB.accdb.

Run once; if tables already exist, they will be dropped and recreated
to match the desired schema (no Username/PasswordHash).
"""

import datetime
import sys
import pyodbc
from pathlib import Path

# -------------------------------------------------------------------
# Configuration – point to your Access file (must already exist)
# -------------------------------------------------------------------
DB_PATH = Path(__file__).with_name("LMS_DB.accdb")
if not DB_PATH.exists():
    print(f"[ERROR] Access file '{DB_PATH}' not found.")
    print("Create an empty .accdb first, then re-run this script.")
    sys.exit(1)

CONN_STR = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    f"DBQ={DB_PATH};"
)

# -------------------------------------------------------------------
# DDL statements in dependency order
# -------------------------------------------------------------------
DDL_STATEMENTS = [

    # 1. Drop old tables (ignore errors)
    "DROP TABLE EmployeeSafetyPermissions",
    "DROP TABLE Items",
    "DROP TABLE Parameters",
    "DROP TABLE SubCategories",
    "DROP TABLE Categories",
    "DROP TABLE SafetyPermissions",
    "DROP TABLE Users",
    "DROP TABLE Companies",

    # 2. Recreate Companies
    """
    CREATE TABLE Companies (
        CompanyID    LONG      PRIMARY KEY,
        CompanyName  TEXT(255),
        Address      TEXT(255)
    );
    """,

    # 3. Recreate Users (no Username/PasswordHash)
    """
    CREATE TABLE Users (
        UserID        COUNTER     PRIMARY KEY,
        CompanyID     LONG        NOT NULL,
        SupervisorID  LONG        NULL,
        LastName      TEXT(255),
        FirstName     TEXT(255),
        UserType      TEXT(20)    NOT NULL,
        CreatedAt     DATETIME    NOT NULL,
        FOREIGN KEY (CompanyID)    REFERENCES Companies(CompanyID),
        FOREIGN KEY (SupervisorID) REFERENCES Users(UserID)
    );
    """,

    # 4. SafetyPermissions
    """
    CREATE TABLE SafetyPermissions (
        SafetyPermissionID  COUNTER   PRIMARY KEY,
        PermissionName      TEXT(255) NOT NULL
    );
    """,

    # 5. Categories
    """
    CREATE TABLE Categories (
        CategoryCode        TEXT(10)   PRIMARY KEY,
        CategoryDescription TEXT(255)  NOT NULL
    );
    """,

    # 6. SubCategories
    """
    CREATE TABLE SubCategories (
        SubCategoryCode        TEXT(10)   PRIMARY KEY,
        CategoryCode           TEXT(10)   NOT NULL,
        SubCategoryDescription TEXT(255),
        FOREIGN KEY (CategoryCode) REFERENCES Categories(CategoryCode)
    );
    """,

    # 7. Parameters (ParamPos instead of Position)
    """
    CREATE TABLE Parameters (
        ParameterID     COUNTER     PRIMARY KEY,
        SubCategoryCode TEXT(10)    NOT NULL,
        ParamPos        BYTE        NOT NULL,
        ParameterName   TEXT(50)    NOT NULL,
        UNIQUE (SubCategoryCode, ParamPos),
        FOREIGN KEY (SubCategoryCode) REFERENCES SubCategories(SubCategoryCode)
    );
    """,

    # 8. Items
    """
    CREATE TABLE Items (
        ItemID              TEXT(255) PRIMARY KEY,
        CategoryCode        TEXT(10)  NOT NULL,
        SubCategoryCode     TEXT(10)  NOT NULL,
        Param1              TEXT(50), Param2 TEXT(50), Param3 TEXT(50),
        Param4              TEXT(50), Param5 TEXT(50),
        Description         MEMO,
        Quantity            LONG      NOT NULL,
        Status              TEXT(20)  NOT NULL,
        HolderID            LONG,
        Location            TEXT(255),
        ManualPath          TEXT(255),
        SOPPath             TEXT(255),
        ImagePath           TEXT(255),
        Price               DOUBLE,
        SafetyRequirements  TEXT(255),
        FOREIGN KEY (CategoryCode)    REFERENCES Categories(CategoryCode),
        FOREIGN KEY (SubCategoryCode) REFERENCES SubCategories(SubCategoryCode),
        FOREIGN KEY (HolderID)        REFERENCES Users(UserID)
    );
    """,

    # 9. Items
    """
    CREATE TABLE ItemSafetyRequirements (
        ItemID             TEXT(255) NOT NULL,
        SafetyPermissionID LONG        NOT NULL,
        PRIMARY KEY (ItemID, SafetyPermissionID),
        FOREIGN KEY (ItemID)             REFERENCES Items(ItemID),
        FOREIGN KEY (SafetyPermissionID) REFERENCES SafetyPermissions(SafetyPermissionID)
    );
    """,

    # 10. EmployeeSafetyPermissions
    """
    CREATE TABLE EmployeeSafetyPermissions (
        EmployeeID         LONG     NOT NULL,
        SafetyPermissionID LONG     NOT NULL,
        IssueDate          DATETIME NOT NULL,
        IssuerEmployeeID   LONG,
        ExpireDate         DATETIME,
        PRIMARY KEY (EmployeeID, SafetyPermissionID, IssueDate),
        FOREIGN KEY (EmployeeID)         REFERENCES Users(UserID),
        FOREIGN KEY (SafetyPermissionID) REFERENCES SafetyPermissions(SafetyPermissionID),
        FOREIGN KEY (IssuerEmployeeID)   REFERENCES Users(UserID)
    );
    """
]

# -------------------------------------------------------------------
# Helper to execute and skip errors if "does not exist"
# -------------------------------------------------------------------
def execute_ddl(cursor, sql: str) -> None:
    cleaned = " ".join(sql.split())
    try:
        cursor.execute(sql)
        print(f"[ OK ] {cleaned[:60]}...")
    except pyodbc.Error as e:
        msg = str(e).lower()
        if "does not exist" in msg or "already exists" in msg:
            print(f"[SKIP] {msg.splitlines()[0]}")
        else:
            raise

def seed_admin(last, first, address, username, email, pwd_hash):
    conn = pyodbc.connect(CONN_STR, autocommit=True)
    cur  = conn.cursor()
    # Find the one and only CompanyID in local DB
    cur.execute("SELECT CompanyID FROM Companies")
    cid = cur.fetchone()[0]
    now = datetime.datetime.now()
    cur.execute("""
        INSERT INTO Users
          (CompanyID, SupervisorID, LastName, FirstName, UserType, CreatedAt)
        VALUES (?, NULL, ?, ?, 'ADMIN', ?)
    """, (cid, last, first, now))
    conn.commit()

# -------------------------------------------------------------------
def main():
    with pyodbc.connect(CONN_STR, autocommit=True) as conn:
        cur = conn.cursor()
        for ddl in DDL_STATEMENTS:
            execute_ddl(cur, ddl)
    print("\nLocal Access schema reset complete.")

if __name__ == "__main__":
    main()
