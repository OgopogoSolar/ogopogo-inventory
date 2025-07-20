# data/license_service.py
from datetime import date
import pymysql
from data.database import DatabaseManager

class LicenceService:
    """Very light wrapper – query once at login time."""
    @staticmethod
    def is_company_licence_valid(company_id: int) -> bool:
        # Use a parameterized query to prevent SQL injection
        sql = "SELECT LicenceExpireDate FROM Companies WHERE CompanyID=%s"
        conn = DatabaseManager.mysql_connection()
        with conn.cursor() as cur:
            cur.execute(sql, (company_id,))
            row = cur.fetchone()
        if not row:
            return False
        expire: date = row["LicenceExpireDate"]
        return date.today() <= expire
    
    @staticmethod
    def get_device_id() -> str:
        # Unique per‐machine: use MAC address
        import uuid
        return hex(uuid.getnode())

    @classmethod
    def activate_license(cls, licence_code: str) -> bool:
        """
        1) Fetch CompanyID by licence_code.
        2) If no record, invalid license.
        3) If DeviceActivations already has a row for this Company:
              return (DeviceID matches this machine).
           Else:
              insert new DeviceActivation(DeviceID).
        """
        conn = DatabaseManager.mysql_connection()
        device = cls.get_device_id()
        with conn.cursor() as cur:
            # 1) lookup
            cur.execute("""
                SELECT CompanyID
                  FROM Companies
                 WHERE LicenceCode=%s
            """, (licence_code,))
            row = cur.fetchone()
            if not row:
                return False
            cid = row["CompanyID"]

            # 2) check existing activation
            cur.execute("""
                SELECT DeviceID FROM DeviceActivations
                 WHERE CompanyID=%s
            """, (cid,))
            act = cur.fetchone()
            if act:
                return act["DeviceID"] == device

            # 3) record new activation
            cur.execute("""
                INSERT INTO DeviceActivations (CompanyID, DeviceID)
                VALUES (%s, %s)
            """, (cid, device))
            return True
