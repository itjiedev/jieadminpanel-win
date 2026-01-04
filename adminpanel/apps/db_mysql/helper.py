import json
from pathlib import Path

def get_installed(id=None):
    from .config import installed_file_path
    if not installed_file_path.exists():
        installed_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(installed_file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        return {}
    with open(installed_file_path, 'r', encoding='utf-8') as f:
        installed = json.load(f)
    if id: return installed[id]
    return installed

def get_config():
    from .config import config_file_path
    if not config_file_path.exists():
        config_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump({'install_folder': ''}, f, ensure_ascii=False, indent=4)
            return {'install_folder': ''}
    with open(config_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_version(version=None):
    from .config import version_file
    with open(version_file, 'r', encoding='utf-8') as f:
        versions = json.load(f)
    if version:
        return versions.get(version)
    return versions


def parse_mysql_version(version_string):
    """解析MySQL版本号，支持5.7和8.0格式"""
    import re
    # MySQL 8.0: mysql  Ver 8.0.33 for Win64 on x86_64
    # MySQL 5.7: mysql.exe  Ver 14.14 Distrib 5.7.44, for Win64 (x86_64)
    # 优先匹配包含"Distrib"的5.7格式
    distrib_pattern = r'Distrib\s+([\d\.]+)'
    match = re.search(distrib_pattern, version_string)
    if match:
        return match.group(1)

    # 匹配8.0格式的版本号 (第二个Ver)
    ver_patterns = list(re.finditer(r'Ver\s+([\d\.]+)', version_string))
    if ver_patterns:
        # 如果有多个Ver匹配，取最后一个（通常是实际版本号）
        if len(ver_patterns) > 1:
            return ver_patterns[-1].group(1)
        else:
            return ver_patterns[0].group(1)

    # 通用格式匹配
    general_pattern = r'(\d+\.\d+\.\d+)'
    match = re.search(general_pattern, version_string)
    if match:
        return match.group(1)

    return None

#
# # apps/db_mysql/mysql_client.py
# import MySQLdb
# from contextlib import contextmanager
#
#
# class MySQLClient:
#     """
#     基于 mysqlclient 的 MySQL 通用操作类
#     """
#
#     def __init__(self, host=None, port=None, user=None,
#                  password=None, database=None, charset='utf8mb4'):
#         """
#         初始化数据库连接参数
#
#         Args:
#             host: 数据库主机地址
#             port: 数据库端口
#             user: 数据库用户名
#             password: 数据库密码
#             database: 数据库名称
#             charset: 字符集
#         """
#         # 如果提供配置ID，则尝试从配置文件获取，否则使用参数初始化,使用时二者必要提供一个
#         self.host = host
#         self.port = port
#         self.user = user
#         self.password = password
#         self.database = database
#         self.charset = charset
#         self.connection = None
#
#     def connect(self):
#         """
#         建立数据库连接
#
#         Returns:
#             MySQLdb.Connection: 数据库连接对象
#         """
#         try:
#             self.connection = MySQLdb.connect(
#                 host=self.host,
#                 port=self.port,
#                 user=self.user,
#                 passwd=self.password,
#                 db=self.database,
#                 charset=self.charset
#             )
#             print(f"成功连接到MySQL数据库: {self.host}:{self.port}/{self.database}")
#             return self.connection
#         except MySQLdb.Error as e:
#             raise f"连接MySQL数据库失败: {e}"
#
#     def disconnect(self):
#         """
#         关闭数据库连接
#         """
#         if self.connection:
#             self.connection.close()
#             self.connection = None
#             print("数据库连接已关闭")
#
#     @contextmanager
#     def get_connection(self):
#         """
#         上下文管理器，自动管理数据库连接
#         """
#         conn = None
#         try:
#             conn = self.connect()
#             yield conn
#         finally:
#             if conn:
#                 conn.close()
#
#     def execute_query(self, sql, params=None):
#         """
#         执行查询语句
#
#         Args:
#             sql: SQL查询语句
#             params: 查询参数
#
#         Returns:
#             查询结果列表
#         """
#         with self.get_connection() as conn:
#             cursor = conn.cursor(MySQLdb.cursors.DictCursor)
#             try:
#                 cursor.execute(sql, params or ())
#                 results = cursor.fetchall()
#                 print(f"查询执行成功: {sql}")
#                 return results
#             except MySQLdb.Error as e:
#                 print(f"查询执行失败: {e}, SQL: {sql}")
#                 raise
#             finally:
#                 cursor.close()
#
#     def execute_update(self, sql, params=None):
#         """
#         执行更新语句（INSERT, UPDATE, DELETE）
#
#         Args:
#             sql: SQL更新语句
#             params: 更新参数
#
#         Returns:
#             int: 受影响的行数
#         """
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             try:
#                 cursor.execute(sql, params or ())
#                 conn.commit()
#                 affected_rows = cursor.rowcount
#                 print(f"更新执行成功: {sql}, 受影响行数: {affected_rows}")
#                 return affected_rows
#             except MySQLdb.Error as e:
#                 conn.rollback()
#                 print(f"更新执行失败: {e}, SQL: {sql}")
#                 raise
#             finally:
#                 cursor.close()
#
#     def execute_many(self, sql, params_list):
#         """
#         批量执行SQL语句
#
#         Args:
#             sql: SQL语句
#             params_list: 参数列表
#
#         Returns:
#             int: 受影响的总行数
#         """
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             try:
#                 cursor.executemany(sql, params_list)
#                 conn.commit()
#                 affected_rows = cursor.rowcount
#                 print(f"批量执行成功: {sql}, 总影响行数: {affected_rows}")
#                 return affected_rows
#             except MySQLdb.Error as e:
#                 conn.rollback()
#                 print(f"批量执行失败: {e}, SQL: {sql}")
#                 raise
#             finally:
#                 cursor.close()
#
#     def insert(self, table, data):
#         """
#         插入数据
#
#         Args:
#             table: 表名
#             data: 插入的数据字典
#
#         Returns:
#             int: 插入的行ID
#         """
#         columns = ', '.join(data.keys())
#         placeholders = ', '.join(['%s'] * len(data))
#         sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
#
#         with self.get_connection() as conn:
#             cursor = conn.cursor()
#             try:
#                 cursor.execute(sql, tuple(data.values()))
#                 conn.commit()
#                 last_id = cursor.lastrowid
#                 print(f"数据插入成功: 表 {table}, ID: {last_id}")
#                 return last_id
#             except MySQLdb.Error as e:
#                 conn.rollback()
#                 print(f"数据插入失败: {e}, SQL: {sql}")
#                 raise
#             finally:
#                 cursor.close()
#
#     def update(self, table, data, where_clause, where_params=None):
#         """
#         更新数据
#
#         Args:
#             table: 表名
#             data: 要更新的数据字典
#             where_clause: WHERE条件子句
#             where_params: WHERE条件参数
#
#         Returns:
#             int: 受影响的行数
#         """
#         set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
#         sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
#         params = tuple(data.values()) + (where_params or ())
#
#         return self.execute_update(sql, params)
#
#     def delete(self, table, where_clause, where_params=None):
#         """
#         删除数据
#
#         Args:
#             table: 表名
#             where_clause: WHERE条件子句
#             where_params: WHERE条件参数
#
#         Returns:
#             int: 受影响的行数
#         """
#         sql = f"DELETE FROM {table} WHERE {where_clause}"
#         return self.execute_update(sql, where_params)
#
#     def select(self, table, fields='*', where_clause=None, where_params=None, order_by=None, limit=None):
#         """
#         查询数据
#
#         Args:
#             table: 表名
#             fields: 查询字段
#             where_clause: WHERE条件子句
#             where_params: WHERE条件参数
#             order_by: 排序子句
#             limit: 限制数量
#
#         Returns:
#             查询结果
#         """
#         if isinstance(fields, list):
#             fields_str = ', '.join(fields)
#         else:
#             fields_str = fields
#
#         sql = f"SELECT {fields_str} FROM {table}"
#
#         if where_clause:
#             sql += f" WHERE {where_clause}"
#
#         if order_by:
#             sql += f" ORDER BY {order_by}"
#
#         if limit:
#             sql += f" LIMIT {limit}"
#
#         return self.execute_query(sql, where_params)
#
#     def table_exists(self, table_name):
#         """
#         检查表是否存在
#
#         Args:
#             table_name: 表名
#
#         Returns:
#             bool: 表是否存在
#         """
#         sql = "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = %s AND table_name = %s"
#         result = self.execute_query(sql, (self.database, table_name))
#         return result[0]['count'] > 0 if result else False
#
#     def get_table_columns(self, table_name):
#         """
#         获取表的列信息
#
#         Args:
#             table_name: 表名
#
#         Returns:
#             列信息列表
#         """
#         sql = """
#         SELECT
#             COLUMN_NAME as name,
#             DATA_TYPE as type,
#             IS_NULLABLE as nullable,
#             COLUMN_DEFAULT as default_value,
#             COLUMN_KEY as key_type,
#             EXTRA as extra
#         FROM information_schema.COLUMNS
#         WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
#         ORDER BY ORDINAL_POSITION
#         """
#         return self.execute_query(sql, (self.database, table_name))
#
#     def get_all_tables(self):
#         """
#         获取数据库中所有表名
#
#         Returns:
#             表名列表
#         """
#         sql = "SHOW TABLES"
#         results = self.execute_query(sql)
#         return [list(row.values())[0] for row in results]
