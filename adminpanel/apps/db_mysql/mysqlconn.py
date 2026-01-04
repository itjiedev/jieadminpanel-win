import MySQLdb
from contextlib import contextmanager


class MysqlConnectionManager:
    """
    MySQL 连接管理工具类
    从 Django Session 获取 MySQL 连接信息
    """

    def __init__(self, request):
        """
        初始化连接参数

        Args:
            request: Django请求对象
        """
        if not hasattr(request, 'session'):
            raise ValueError("Request object must have session attribute")

        self.host = request.session.get('host', 'localhost')
        self.port = int(request.session.get('port', 3306))
        self.user = request.session.get('user', 'root')
        self.password = request.session.get('password', '')
        self.database = request.session.get('database', '')
        self.charset = request.session.get('charset', 'utf8mb4')

    def get_connection_params(self):
        """获取连接参数"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset
        }

    @contextmanager
    def get_connection(self):
        """
        上下文管理器，自动管理数据库连接
        从 session 获取连接参数并建立连接
        """
        conn = None
        try:
            params = self.get_connection_params()

            if params['database']:
                conn = MySQLdb.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    passwd=params['password'],
                    db=params['database'],
                    charset=params['charset']
                )
            else:
                conn = MySQLdb.connect(
                    host=params['host'],
                    port=params['port'],
                    user=params['user'],
                    passwd=params['password'],
                    charset=params['charset']
                )
            yield conn
        except MySQLdb.Error as e:
            raise Exception(f'数据库连接失败: {e}')
        finally:
            if conn: conn.close()

    def test_connection(self):
        """
        测试数据库连接是否正常

        Returns:
            tuple: (success: bool, message: str) 成功状态和消息
        """

        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                print("数据库连接成功")
                return True, "数据库连接正常"
            except Exception as e:
                return False, f"数据库连接失败: {e}"

    def execute_query(self, sql, params=None):
        """
        执行查询语句

        Args:
            sql: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            try:
                cursor.execute(sql, params or ())
                results = cursor.fetchall()
                return results
            except MySQLdb.Error as e:
                print(f"执行失败: {e}, SQL: {sql}")
                raise Exception(f"{e}, SQL: {sql}")
            finally:
                cursor.close()

    def execute_update(self, sql, params=None):
        """
        执行更新语句（INSERT, UPDATE, DELETE）

        Args:
            sql: SQL更新语句
            params: 更新参数

        Returns:
            int: 受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params or ())
                conn.commit()
                affected_rows = cursor.rowcount
                print(f"更新执行成功: {sql}, 受影响行数: {affected_rows}")
                return affected_rows
            except MySQLdb.Error as e:
                conn.rollback()
                print(f"更新执行失败: {e}, SQL: {sql}")
                raise
            finally:
                cursor.close()

    def execute_many(self, sql, params_list):
        """
        批量执行SQL语句

        Args:
            sql: SQL语句
            params_list: 参数列表

        Returns:
            int: 受影响的总行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(sql, params_list)
                conn.commit()
                affected_rows = cursor.rowcount
                print(f"批量执行成功: {sql}, 总影响行数: {affected_rows}")
                return affected_rows
            except MySQLdb.Error as e:
                conn.rollback()
                print(f"批量执行失败: {e}, SQL: {sql}")
                raise
            finally:
                cursor.close()

    def insert(self, table, data):
        """
        插入数据

        Args:
            table: 表名
            data: 插入的数据字典

        Returns:
            int: 插入的行ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, tuple(data.values()))
                conn.commit()
                last_id = cursor.lastrowid
                print(f"数据插入成功: 表 {table}, ID: {last_id}")
                return last_id
            except MySQLdb.Error as e:
                conn.rollback()
                print(f"数据插入失败: {e}, SQL: {sql}")
                raise
            finally:
                cursor.close()

    def update(self, table, data, where_clause, where_params=None):
        """
        更新数据

        Args:
            table: 表名
            data: 要更新的数据字典
            where_clause: WHERE条件子句
            where_params: WHERE条件参数

        Returns:
            int: 受影响的行数
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + (where_params or ())

        return self.execute_update(sql, params)

    def delete(self, table, where_clause, where_params=None):
        """
        删除数据

        Args:
            table: 表名
            where_clause: WHERE条件子句
            where_params: WHERE条件参数

        Returns:
            int: 受影响的行数
        """
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        return self.execute_update(sql, where_params)

    def select(self, table, fields='*', where_clause=None, where_params=None, order_by=None, limit=None):
        """
        查询数据

        Args:
            table: 表名
            fields: 查询字段
            where_clause: WHERE条件子句
            where_params: WHERE条件参数
            order_by: 排序子句
            limit: 限制数量

        Returns:
            查询结果
        """
        if isinstance(fields, list):
            fields_str = ', '.join(fields)
        else:
            fields_str = fields

        sql = f"SELECT {fields_str} FROM {table}"

        if where_clause:
            sql += f" WHERE {where_clause}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        if limit:
            sql += f" LIMIT {limit}"

        return self.execute_query(sql, where_params)

    def table_exists(self, table_name):
        """
        检查表是否存在

        Args:
            table_name: 表名

        Returns:
            bool: 表是否存在
        """
        params = self.get_connection_params()
        sql = "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = %s AND table_name = %s"
        result = self.execute_query(sql, (params['database'], table_name))
        return result[0]['count'] > 0 if result else False

    def get_table_columns(self, table_name):
        """
        获取表的列信息

        Args:
            table_name: 表名

        Returns:
            列信息列表
        """
        params = self.get_connection_params()
        sql = """
        SELECT 
            COLUMN_NAME as name,
            DATA_TYPE as type,
            IS_NULLABLE as nullable,
            COLUMN_DEFAULT as default_value,
            COLUMN_KEY as key_type,
            EXTRA as extra
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(sql, (params['database'], table_name))

    def get_all_tables(self):
        """
        获取数据库中所有表名

        Returns:
            表名列表
        """
        sql = "SHOW TABLES"
        results = self.execute_query(sql)
        return [list(row.values())[0] for row in results]

    def get_all_databases(self):
        """
        获取数据库中所有数据库名

        Returns:
            数据库名列表
        """
        sql = """
SELECT 
    s.SCHEMA_NAME AS `db_name`,
    IFNULL(ROUND(SUM(t.DATA_LENGTH + t.INDEX_LENGTH) / 1024 / 1024, 2), 0) AS `size`,
    IFNULL(COUNT(CASE WHEN t.TABLE_TYPE = 'BASE TABLE' THEN 1 END), 0) AS `table_count`,
    IFNULL(COUNT(CASE WHEN t.TABLE_TYPE = 'VIEW' THEN 1 END), 0) AS `view_count`,
    IFNULL(COUNT(DISTINCT r.ROUTINE_NAME), 0) AS `function_count`,
    IFNULL(COUNT(DISTINCT p.ROUTINE_NAME), 0) AS `procedure_count`,
    IFNULL(COUNT(DISTINCT tr.TRIGGER_NAME), 0) AS `trigger_count`,
    IFNULL(COUNT(DISTINCT e.EVENT_NAME), 0) AS `event_count`,
    s.DEFAULT_CHARACTER_SET_NAME AS `character_set`,
    s.DEFAULT_COLLATION_NAME AS `collation_name`
FROM information_schema.SCHEMATA s
LEFT JOIN information_schema.TABLES t 
    ON s.SCHEMA_NAME = t.TABLE_SCHEMA
LEFT JOIN information_schema.ROUTINES r 
    ON s.SCHEMA_NAME = r.ROUTINE_SCHEMA
    AND r.ROUTINE_TYPE = 'FUNCTION'
LEFT JOIN information_schema.ROUTINES p 
    ON s.SCHEMA_NAME = p.ROUTINE_SCHEMA
    AND p.ROUTINE_TYPE = 'PROCEDURE'
LEFT JOIN information_schema.TRIGGERS tr 
    ON s.SCHEMA_NAME = tr.TRIGGER_SCHEMA
LEFT JOIN information_schema.EVENTS e 
    ON s.SCHEMA_NAME = e.EVENT_SCHEMA
WHERE 
    s.SCHEMA_NAME NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
GROUP BY 
    s.SCHEMA_NAME, s.DEFAULT_CHARACTER_SET_NAME, s.DEFAULT_COLLATION_NAME
ORDER BY 
    `db_name`;
"""
        results = self.execute_query(sql)
        return results

    def get_character_sets(self):
        """
        获取 MySQL 支持的所有字符集

        Returns:
            字符集列表，每个元素包含字符集名称、描述和默认排序规则
        """
        sql = """
        SELECT 
            CHARACTER_SET_NAME as charset_name,
            DEFAULT_COLLATE_NAME as default_collation,
            DESCRIPTION as description,
            MAXLEN as max_length
        FROM information_schema.CHARACTER_SETS
        ORDER BY CHARACTER_SET_NAME
        """
        results = self.execute_query(sql)
        return results


    def get_collations(self, charset_name=None):
        """
        获取 MySQL 支持的所有排序规则

        Args:
            charset_name: 字符集名称，可选参数，如果指定则只返回该字符集的排序规则

        Returns:
            排序规则列表，每个元素包含排序规则名称、字符集名称和是否区分大小写等信息
        """
        sql = """
        SELECT 
            COLLATION_NAME as collation_name,
            CHARACTER_SET_NAME as charset_name,
            IS_DEFAULT as is_default,
            IS_COMPILED as is_compiled,
            SORTLEN as sort_length
        FROM information_schema.COLLATIONS
        """

        params = None
        if charset_name:
            sql += " WHERE CHARACTER_SET_NAME = %s"
            params = (charset_name,)

        sql += " ORDER BY COLLATION_NAME"

        results = self.execute_query(sql, params)
        return results

    def get_charset_collation_pairs(self):
        """
        获取字符集与排序规则配对信息

        Returns:
            包含字符集和其默认排序规则的列表
        """
        sql = """
        SELECT 
            cs.CHARACTER_SET_NAME as charset_name,
            cs.DEFAULT_COLLATE_NAME as default_collation,
            cs.DESCRIPTION as description,
            c.COLLATION_NAME as collation_name,
            c.IS_DEFAULT as is_default_collation
        FROM information_schema.CHARACTER_SETS cs
        LEFT JOIN information_schema.COLLATIONS c
            ON cs.CHARACTER_SET_NAME = c.CHARACTER_SET_NAME
        ORDER BY cs.CHARACTER_SET_NAME, c.IS_DEFAULT DESC, c.COLLATION_NAME
        """
        results = self.execute_query(sql)
        return results

    def get_collations_by_charset(self, charset_name):
        """
        获取特定字符集的所有排序规则

        Args:
            charset_name: 字符集名称

        Returns:
            指定字符集的排序规则列表
        """
        sql = """
        SELECT 
            COLLATION_NAME as collation_name,
            CHARACTER_SET_NAME as charset_name,
            IS_DEFAULT as is_default,
            IS_COMPILED as is_compiled,
            SORTLEN as sort_length
        FROM information_schema.COLLATIONS
        WHERE CHARACTER_SET_NAME = %s
        ORDER BY IS_DEFAULT DESC, COLLATION_NAME
        """
        results = self.execute_query(sql, (charset_name,))
        return results

    def get_charset_settings(self):
        """
        获取 MySQL 所有字符集相关的设置

        Returns:
            dict: 包含所有字符集设置的信息
        """
        sql = """
        SELECT 
            @@character_set_client AS client_charset,
            @@character_set_connection AS connection_charset,
            @@character_set_database AS database_charset,
            @@character_set_filesystem AS filesystem_charset,
            @@character_set_results AS results_charset,
            @@character_set_server AS server_charset,
            @@character_set_system AS system_charset,
            @@collation_connection AS connection_collation,
            @@collation_database AS database_collation,
            @@collation_server AS server_collation
        """
        results = self.execute_query(sql)
        if results:
            return {
                'client_charset': results[0]['client_charset'],
                'connection_charset': results[0]['connection_charset'],
                'database_charset': results[0]['database_charset'],
                'filesystem_charset': results[0]['filesystem_charset'],
                'results_charset': results[0]['results_charset'],
                'server_charset': results[0]['server_charset'],
                'system_charset': results[0]['system_charset'],
                'connection_collation': results[0]['connection_collation'],
                'database_collation': results[0]['database_collation'],
                'server_collation': results[0]['server_collation']
            }
        return {}

    def get_database_charset_collation(self, database_name):
        """
        获取指定数据库的字符集和排序规则

        Args:
            database_name: 数据库名称

        Returns:
            dict: 包含数据库字符集和排序规则的信息
        """
        sql = """
              SELECT DEFAULT_CHARACTER_SET_NAME AS charset, \
                     DEFAULT_COLLATION_NAME AS collation
              FROM information_schema.SCHEMATA
              WHERE SCHEMA_NAME = %s \
              """
        results = self.execute_query(sql, (database_name,))
        if results:
            return {
                'charset': results[0]['charset'],
                'collation': results[0]['collation']
            }
        return {}
