# init_remote_db.py
import pymysql
from pymysql.constants import CLIENT

def main():
    conn = pymysql.connect(
        host="82.197.82.52",
        user="u569981245_LMS_Admin",
        password="Rfmtl2024!admin",
        database="u569981245_LMS",
        client_flag=CLIENT.MULTI_STATEMENTS,
        autocommit=True
    )
    with conn.cursor() as cur:
        # 先删旧表（如果存在）
        cur.execute("DROP TABLE IF EXISTS VerificationCodes;")
        cur.execute("DROP TABLE IF EXISTS Companies;")

        # 1) 公司表
        cur.execute("""
        CREATE TABLE Companies (
            CompanyID            INT            AUTO_INCREMENT PRIMARY KEY,
            CompanyName          VARCHAR(255)   NOT NULL,
            CompanyAddress       VARCHAR(255)   NOT NULL,
            LicenceCode          VARCHAR(255)   NOT NULL,
            LicenceStartDate     DATE           NOT NULL,
            LicenceExpireDate    DATE           NOT NULL,
            LicenceType          VARCHAR(50)    NOT NULL,
            rootAdminUsername    VARCHAR(50)    NOT NULL UNIQUE,
            rootAdminEmail       VARCHAR(100)   NOT NULL UNIQUE,
            rootAdminPassword    CHAR(32)       NOT NULL  -- MD5 散列
        );
        """)

        # 2) 验证码表
        cur.execute("""
        CREATE TABLE VerificationCodes (
            CodeID     CHAR(8)       PRIMARY KEY,   -- 8 位随机数字
            ExpireAt   DATETIME      NOT NULL,
            CompanyID  INT           NOT NULL,
            FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID)
        );
        """)

        # 3) DeviceActivations: lock one device per Company
        cur.execute("""
        CREATE TABLE IF NOT EXISTS DeviceActivations (
            ActivationID     INT        AUTO_INCREMENT PRIMARY KEY,
            CompanyID        INT        NOT NULL,
            DeviceID         VARCHAR(255) NOT NULL UNIQUE,
            ActivatedAt      DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (CompanyID) REFERENCES Companies(CompanyID)
        );
        """)

    print("✔ Remote MySQL schema reset complete.")

if __name__ == "__main__":
    main()
