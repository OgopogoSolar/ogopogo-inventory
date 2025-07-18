# data/access_dao.py

import datetime
from dataclasses import dataclass
import pyodbc
from data.database import DatabaseManager


@dataclass
class User:
    user_id: int
    company_id: int
    supervisor_id: int | None    # ← new field
    last_name: str
    first_name: str
    user_type: str
    created_at: datetime.datetime


class UserDAO:
    """
    • authenticate_admin(username, password) returns the first ADMIN row,
      ignoring the passed credentials (since login is now by barcode).
    • get_by_id(uid) fetches any user by numeric ID.
    All SQL is parameterized where appropriate.
    """

    @classmethod
    def authenticate_admin(cls, _username: str, _password: str) -> User | None:
        sql = """
            SELECT TOP 1
                UserID,
                CompanyID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            FROM Users
            WHERE UserType='ADMIN'
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql)
        row = cur.fetchone()
        return User(*row) if row else None

    @classmethod
    def get_by_id(cls, uid: int) -> User | None:
        sql = """
            SELECT
                UserID,
                CompanyID,
                SupervisorID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            FROM Users
            WHERE UserID=?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (uid,))
        row = cur.fetchone()
        return User(*row) if row else None


class EmployeeDAO:
    """
    CRUD operations for Users table when managed as employees.
    """

    @classmethod
    def fetch_all(cls) -> list[User]:
        sql = """
            SELECT
                UserID,
                CompanyID,
                SupervisorID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            FROM Users
           ORDER BY UserID
        """
        cur = DatabaseManager.access_connection().cursor()
        return [
            User(
                r.UserID, r.CompanyID, r.SupervisorID,
                r.LastName, r.FirstName, r.UserType, r.CreatedAt
            )
            for r in cur.execute(sql)
        ]

    @classmethod
    def fetch_by_id(cls, uid: int) -> User | None:
        sql = """
            SELECT
                UserID,
                CompanyID,
                SupervisorID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            FROM Users
            WHERE UserID=?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (uid,))
        r = cur.fetchone()
        return (
            User(
                r.UserID, r.CompanyID, r.SupervisorID,
                r.LastName, r.FirstName, r.UserType, r.CreatedAt
            )
            if r else None
        )

    @classmethod
    def fetch_by_supervisor(cls, supervisor_id: int) -> list[User]:
        """
        Return all Users whose SupervisorID = supervisor_id.
        """
        sql = """
            SELECT
                UserID,
                CompanyID,
                SupervisorID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            FROM Users
            WHERE SupervisorID = ?
            ORDER BY UserID
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (supervisor_id,))
        return [User(*r) for r in cur.fetchall()]

    @classmethod
    def insert(cls,
               last: str,
               first: str,
               utype: str,
               supervisor_id: int | None
    ) -> None:
        sql = """
            INSERT INTO Users (
                CompanyID,
                SupervisorID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        now = datetime.datetime.now()
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            1,
            supervisor_id,
            last,
            first,
            utype,
            now
        ))

    @classmethod
    def update(cls, emp: User) -> None:
        sql = """
            UPDATE Users SET
                SupervisorID=?,
                LastName=?,
                FirstName=?,
                UserType=?
            WHERE UserID=?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            emp.supervisor_id,
            emp.last_name,
            emp.first_name,
            emp.user_type,
            emp.user_id
        ))

    @classmethod
    def delete(cls, uid: int) -> None:
        sql = "DELETE FROM Users WHERE UserID=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (uid,))

@dataclass
class Item:
    item_id: str
    category_code: str
    subcategory_code: str
    description: str | None
    quantity: int
    status: str
    holder_id: int | None     # 对应 Access 表里的 HolderID 列
    location: str
    manual_path: str | None
    sop_path: str | None
    image_path: str | None
    price: float | None

class InventoryDAO:
    """CRUD for Items 表"""

    @classmethod
    def fetch_all(cls) -> list[Item]:
        sql = """
            SELECT
                ItemID,
                CategoryCode,
                SubCategoryCode,
                Description,
                Quantity,
                Status,
                HolderID,
                Location,
                ManualPath,
                SOPPath,
                ImagePath,
                Price
            FROM Items
            ORDER BY ItemID
        """
        cur = DatabaseManager.access_connection().cursor()
        return [Item(*row) for row in cur.execute(sql)]
    
    @classmethod
    def fetch_by_supervisor(cls, supervisor_id: int) -> list[User]:
        """
        Fetch all users who report to a specific supervisor.
        """
        sql = """
            SELECT
                UserID,
                CompanyID,
                SupervisorID,
                LastName,
                FirstName,
                UserType,
                CreatedAt
            FROM Users
            WHERE SupervisorID = ?
            ORDER BY UserID
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (supervisor_id,))
        return [User(*row) for row in cur.fetchall()]


    @classmethod
    def fetch_by_id(cls, item_id: str) -> Item | None:
        sql = """
            SELECT
                ItemID,
                CategoryCode,
                SubCategoryCode,
                Description,
                Quantity,
                Status,
                HolderID,
                Location,
                ManualPath,
                SOPPath,
                ImagePath,
                Price
            FROM Items
            WHERE ItemID = ?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (item_id,))
        row = cur.fetchone()
        return Item(*row) if row else None

    @classmethod
    def insert(cls, itm: Item) -> None:
        sql = """
            INSERT INTO Items (
                ItemID,
                CategoryCode,
                SubCategoryCode,
                Description,
                Quantity,
                Status,
                HolderID,
                Location,
                ManualPath,
                SOPPath,
                ImagePath,
                Price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            itm.item_id,
            itm.category_code,
            itm.subcategory_code,
            itm.description,
            itm.quantity,
            itm.status,
            itm.holder_id,
            itm.location,
            itm.manual_path,
            itm.sop_path,
            itm.image_path,
            itm.price
        ))

    @classmethod
    def update(cls, itm: Item) -> None:
        sql = """
            UPDATE Items SET
                CategoryCode    = ?,
                SubCategoryCode = ?,
                Description = ?,
                Quantity    = ?,
                Status      = ?,
                HolderID    = ?,
                Location    = ?,
                ManualPath  = ?,
                SOPPath     = ?,
                ImagePath   = ?,
                Price       = ?
            WHERE ItemID = ?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            itm.category_code,
            itm.subcategory_code,
            itm.description,
            itm.quantity,
            itm.status,
            itm.holder_id,
            itm.location,
            itm.manual_path,
            itm.sop_path,
            itm.image_path,
            itm.price,
            itm.item_id
        ))

    @classmethod
    def delete(cls, item_id: str):
        db = DatabaseManager.access_connection()
        cur = db.cursor()

        # Step 1: delete related safety requirements
        cur.execute("DELETE FROM ItemSafetyRequirements WHERE ItemID = ?", (item_id,))

        # Step 2: delete the item itself from Items table
        cur.execute("DELETE FROM Items WHERE ItemID = ?", (item_id,))




# ——— 模型定义 —————————————————————————————————————————————————————————
@dataclass
class Category:
    code: str
    description: str

@dataclass
class SubCategory:
    code: str
    category_code: str
    description: str

@dataclass
class Parameter:
    subcategory_code: str
    position: int
    name: str

# ——— CategoryDAO ——————————————————————————————————————————————————————
class CategoryDAO:
    @classmethod
    def fetch_all(cls) -> list[Category]:
        sql = """
            SELECT
                [CategoryCode],
                [CategoryDescription]  AS Description
            FROM [Categories]
            ORDER BY [CategoryCode]
        """
        cur = DatabaseManager.access_connection().cursor()
        return [Category(*row) for row in cur.execute(sql)]

    @classmethod
    def fetch_by_code(cls, code: str) -> Category | None:
        sql = """
            SELECT
                [CategoryCode],
                [CategoryDescription] AS Description
            FROM [Categories]
            WHERE [CategoryCode]=?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (code,))
        row = cur.fetchone()
        return Category(row.CategoryCode, row.Description) if row else None

    @classmethod
    def insert(cls, code: str, desc: str) -> None:
        sql = "INSERT INTO [Categories] ([CategoryCode],[CategoryDescription]) VALUES (?, ?)"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (code, desc))

    @classmethod
    def update(cls, code: str, desc: str) -> None:
        sql = "UPDATE [Categories] SET [CategoryDescription]=? WHERE [CategoryCode]=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (desc, code))

    @classmethod
    def delete(cls, code: str) -> None:
        sql = "DELETE FROM [Categories] WHERE [CategoryCode]=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (code,))


# ——— SubCategoryDAO ————————————————————————————————————————————————————
class SubCategoryDAO:
    @classmethod
    def fetch_by_category(cls, cat_code: str) -> list[SubCategory]:
        sql = """
            SELECT
                [SubCategoryCode],
                [CategoryCode],
                [SubCategoryDescription]   AS Description
            FROM [SubCategories]
            WHERE [CategoryCode]=?
            ORDER BY [SubCategoryCode]
        """
        cur = DatabaseManager.access_connection().cursor()
        return [
            SubCategory(r.SubCategoryCode, r.CategoryCode, r.Description)
            for r in cur.execute(sql, (cat_code,))
        ]

    @classmethod
    def fetch_by_code(cls, code: str) -> SubCategory | None:
        sql = """
            SELECT
                [SubCategoryCode],
                [CategoryCode],
                [SubCategoryDescription]   AS Description
            FROM [SubCategories]
            WHERE [SubCategoryCode]=?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (code,))
        row = cur.fetchone()
        return SubCategory(row.SubCategoryCode, row.CategoryCode, row.Description) if row else None

    @classmethod
    def insert(cls, code: str, cat_code: str, desc: str) -> None:
        sql = "INSERT INTO [SubCategories] ([SubCategoryCode],[CategoryCode],[SubCategoryDescription]) VALUES (?,?,?)"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (code, cat_code, desc))

    @classmethod
    def update(cls, code: str, cat_code: str, desc: str) -> None:
        sql = "UPDATE [SubCategories] SET [CategoryCode]=?,[SubCategoryDescription]=? WHERE [SubCategoryCode]=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (cat_code, desc, code))

    @classmethod
    def delete(cls, code: str) -> None:
        sql = "DELETE FROM [SubCategories] WHERE [SubCategoryCode]=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (code,))


class ParameterDAO:
    @classmethod
    def fetch_by_subcategory(cls, sub_code: str) -> list[Parameter]:
        sql = """
            SELECT
                [SubCategoryCode],
                [ParamPos]       AS Position,
                [ParameterName]  AS Name
            FROM [Parameters]
            WHERE [SubCategoryCode]=?
            ORDER BY [ParamPos]
        """
        cur = DatabaseManager.access_connection().cursor()
        return [
            Parameter(r.SubCategoryCode, r.Position, r.Name)
            for r in cur.execute(sql, (sub_code,))
        ]
    
    @classmethod
    def insert(cls, sub_code: str, pos: int, name: str) -> None:
        sql = """
            INSERT INTO [Parameters]
                ([SubCategoryCode],[ParamPos],[ParameterName])
            VALUES (?, ?, ?)
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (sub_code, pos, name))

    @classmethod
    def update(cls,
               sub_code: str,
               old_pos: int,
               new_pos: int,
               name: str
    ) -> None:
        conn = DatabaseManager.access_connection()
        cur  = conn.cursor()
        # shift intervening rows to avoid duplicates
        if new_pos < old_pos:
            cur.execute("""
              UPDATE [Parameters]
                 SET [ParamPos] = [ParamPos] + 1
               WHERE [SubCategoryCode]=?
                 AND [ParamPos] BETWEEN ? AND ?
            """, (sub_code, new_pos, old_pos - 1))
        elif new_pos > old_pos:
            cur.execute("""
              UPDATE [Parameters]
                 SET [ParamPos] = [ParamPos] - 1
               WHERE [SubCategoryCode]=?
                 AND [ParamPos] BETWEEN ? AND ?
            """, (sub_code, old_pos + 1, new_pos))
        # now move the edited parameter
        cur.execute("""
          UPDATE [Parameters]
             SET [ParamPos]=?, [ParameterName]=?
           WHERE [SubCategoryCode]=? AND [ParamPos]=?
        """, (new_pos, name, sub_code, old_pos))
        conn.commit()

    @classmethod
    def delete(cls, sub_code: str, pos: int) -> None:
        sql = "DELETE FROM [Parameters] WHERE [SubCategoryCode]=? AND [ParamPos]=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (sub_code, pos))

# ——— InventoryDAO 延展：检查物品依赖 ——————————————————————————————
from data.access_dao import InventoryDAO

def _count(sql: str, params: tuple) -> int:
    cur = DatabaseManager.access_connection().cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else 0

InventoryDAO.has_items_in_category = classmethod(lambda cls, cat:
    _count("SELECT COUNT(*) FROM Items WHERE ItemID LIKE ?", (f"{cat}-%",)) > 0
)

InventoryDAO.has_items_in_subcategory = classmethod(lambda cls, cat, sub:
    _count(
        "SELECT COUNT(*) FROM Items WHERE ItemID LIKE ?",
        (f"{cat}-{sub}-%",)
    ) > 0
)

def _has_items_using_param(cls, sub: str, pos: int) -> bool:
    # 取出所有该子类别的 ItemID，然后按 '-' 切分检查是否有第 pos+1 段存在
    sql = "SELECT ItemID FROM Items WHERE ItemID LIKE ?"
    cur = DatabaseManager.access_connection().cursor()
    cur.execute(sql, (f"%-{sub}-%",))
    for (itemid,) in cur.fetchall():
        parts = itemid.split('-')
        # parts[0]=cat, parts[1]=sub, parts[2]=param1,...
        if len(parts) > pos+1 and parts[pos+1]:
            return True
    return False

InventoryDAO.has_items_using_param = classmethod(_has_items_using_param)

# ——— Models for safety module ———————————————————————————————————————
@dataclass
class SafetyPermissionType:
    permission_id: int
    name: str

@dataclass
class UserSafetyPermit:
    employee_id: int
    permit_id: int
    permit_name: str
    issue_date: datetime.datetime
    expire_date: datetime.datetime
    issuer_id: int
    issuer_first: str
    issuer_last: str

# ——— SafetyDAO —————————————————————————————————————————————————————
class SafetyDAO:
    @classmethod
    def fetch_all_types(cls) -> list[SafetyPermissionType]:
        sql = "SELECT SafetyPermissionID, PermissionName FROM SafetyPermissions"
        cur = DatabaseManager.access_connection().cursor()
        return [
            SafetyPermissionType(r.SafetyPermissionID, r.PermissionName)
            for r in cur.execute(sql)
        ]

    @classmethod
    def fetch_by_user(cls, user_id: int) -> list[UserSafetyPermit]:
        # Access requires parentheses around JOINs and explicit INNER JOIN
        sql = """
        SELECT
            esp.EmployeeID,
            esp.SafetyPermissionID,
            sp.PermissionName,
            esp.IssueDate,
            esp.ExpireDate,
            esp.IssuerEmployeeID,
            u2.FirstName AS IssuerFirst,
            u2.LastName  AS IssuerLast
        FROM
            (EmployeeSafetyPermissions AS esp
             INNER JOIN SafetyPermissions AS sp
               ON esp.SafetyPermissionID = sp.SafetyPermissionID)
        LEFT JOIN Users AS u2
          ON esp.IssuerEmployeeID = u2.UserID
        WHERE esp.EmployeeID = ?
        ORDER BY esp.IssueDate DESC
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (user_id,))
        rows = cur.fetchall()
        return [
            UserSafetyPermit(
                r.EmployeeID,
                r.SafetyPermissionID,
                r.PermissionName,
                r.IssueDate,
                r.ExpireDate,
                r.IssuerEmployeeID,
                r.IssuerFirst,
                r.IssuerLast
            )
            for r in rows
        ]

    @classmethod
    def add_permit(
        cls,
        employee_id: int,
        safety_permission_id: int,
        issuer_employee_id: int,
        issue_date: datetime.datetime,
        expire_date: datetime.datetime
    ) -> None:
        sql = """
        INSERT INTO EmployeeSafetyPermissions
            (EmployeeID, SafetyPermissionID,
             IssueDate, IssuerEmployeeID, ExpireDate)
        VALUES (?, ?, ?, ?, ?)
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            employee_id,
            safety_permission_id,
            issue_date,
            issuer_employee_id,
            expire_date
        ))

    @classmethod
    def update_permit(
        cls,
        employee_id: int,
        safety_permission_id: int,
        issue_date: datetime.datetime,
        new_expire_date: datetime.datetime
    ) -> None:
        sql = """
        UPDATE EmployeeSafetyPermissions
           SET ExpireDate = ?
         WHERE EmployeeID = ?
           AND SafetyPermissionID = ?
           AND IssueDate = ?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            new_expire_date,
            employee_id,
            safety_permission_id,
            issue_date
        ))

    @classmethod
    def delete_permit(
        cls,
        employee_id: int,
        safety_permission_id: int,
        issue_date: datetime.datetime
    ) -> None:
        sql = """
        DELETE FROM EmployeeSafetyPermissions
         WHERE EmployeeID = ?
           AND SafetyPermissionID = ?
           AND IssueDate = ?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (
            employee_id,
            safety_permission_id,
            issue_date
        ))

    @classmethod
    def fetch_by_supervisor(cls, supervisor_id: int) -> list[User]:
        """
        Return all Users whose SupervisorID = supervisor_id.
        """
        sql = """
        SELECT
            UserID, CompanyID, LastName,
            FirstName, UserType, CreatedAt
        FROM Users
        WHERE SupervisorID = ?
        """
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (supervisor_id,))
        return [User(*r) for r in cur.fetchall()]
    
    @classmethod
    def add_type(cls, name: str) -> None:
        sql = "INSERT INTO SafetyPermissions (PermissionName) VALUES (?)"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (name,))

    @classmethod
    def update_type(cls, permission_id: int, name: str) -> None:
        sql = "UPDATE SafetyPermissions SET PermissionName = ? WHERE SafetyPermissionID = ?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (name, permission_id))

    @classmethod
    def delete_type(cls, permission_id: int) -> None:
        db = DatabaseManager.access_connection()
        cur = db.cursor()
        try:
            # Start transaction
            db.begin()

            # 1) Delete all user-permit assignments
            cur.execute(
                "DELETE FROM EmployeeSafetyPermissions WHERE SafetyPermissionID = ?",
                (permission_id,)
            )

            # 2) Delete all item-requirements
            from data.access_dao import ItemSafetyRequirementDAO
            ItemSafetyRequirementDAO.delete_by_permission(permission_id)

            # 3) Delete the permission type itself
            cur.execute(
                "DELETE FROM SafetyPermissions WHERE SafetyPermissionID = ?",
                (permission_id,)
            )

            db.commit()
        except Exception as e:
            db.rollback()
            raise e


@dataclass
class ItemSafetyRequirement:
    item_id: str
    safety_permission_id: int

class ItemSafetyRequirementDAO:
    @classmethod
    def fetch_by_item(cls, item_id: str) -> list[int]:
        sql = "SELECT SafetyPermissionID FROM ItemSafetyRequirements WHERE ItemID = ?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (item_id,))
        return [row.SafetyPermissionID for row in cur.fetchall()]

    @classmethod
    def add_requirement(cls, item_id: str, pid: int) -> None:
        sql = "INSERT INTO ItemSafetyRequirements (ItemID, SafetyPermissionID) VALUES (?, ?)"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (item_id, pid))

    @classmethod
    def delete_requirement(cls, item_id: str, pid: int) -> None:
        sql = "DELETE FROM ItemSafetyRequirements WHERE ItemID=? AND SafetyPermissionID=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (item_id, pid))

    @classmethod
    def delete_by_permission(cls, pid: int) -> None:
        sql = "DELETE FROM ItemSafetyRequirements WHERE SafetyPermissionID=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (pid,))

    @classmethod
    def update_permission_id(cls, old_pid: int, new_pid: int) -> None:
        sql = "UPDATE ItemSafetyRequirements SET SafetyPermissionID=? WHERE SafetyPermissionID=?"
        cur = DatabaseManager.access_connection().cursor()
        cur.execute(sql, (new_pid, old_pid))

