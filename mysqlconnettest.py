import mysql.connector
from mysql.connector import errorcode

# Obtain connection string information from the portal

#     'host': 'aianalysis.mysql.database.azure.com',     # 数据库服务器地址
#     'port':'3306',
#     'user': 'ZDHH25U',         # 数据库用户名
#     'password': 'Pp2766466225.',         # 数据库密码
#     'database': 'pso_voc_tool'   # 数据库名
config = {
    'host': 'aianalysis.mysql.database.azure.com',     # 数据库服务器地址
    'user': '<ZDHH25U>',         # 数据库用户名
    'password': '<Pp2766466225.>',         # 数据库密码
    'database': '<pso_voc_tool>'   # 数据库名
}

# Construct connection string
conn = mysql.connector.connect(**config)
try:
   conn = mysql.connector.connect(**config)
   print("Connection established")
except mysql.connector.Error as err:
  if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    print("Something is wrong with the user name or password")
  elif err.errno == errorcode.ER_BAD_DB_ERROR:
    print("Database does not exist")
  else:
    print(err)
else:
  cursor = conn.cursor()

# Drop previous table of same name if one exists
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS inventory;")
print("Finished dropping table (if existed).")

# Create table
cursor.execute("CREATE TABLE inventory (id serial PRIMARY KEY, name VARCHAR(50), quantity INTEGER);")
print("Finished creating table.")

# Insert some data into table
cursor.execute("INSERT INTO inventory (name, quantity) VALUES (%s, %s);", ("banana", 150))
print("Inserted",cursor.rowcount,"row(s) of data.")
cursor.execute("INSERT INTO inventory (name, quantity) VALUES (%s, %s);", ("orange", 154))
print("Inserted",cursor.rowcount,"row(s) of data.")
cursor.execute("INSERT INTO inventory (name, quantity) VALUES (%s, %s);", ("apple", 100))
print("Inserted",cursor.rowcount,"row(s) of data.")

# Cleanup
conn.commit()
cursor.close()
conn.close()
print("Done.")
# # 数据库配置
# db_config = {
#     'host': 'aianalysis.mysql.database.azure.com',     # 数据库服务器地址
#     'port':'3306',
#     'user': 'ZDHH25U',         # 数据库用户名
#     'password': 'Pp2766466225.',         # 数据库密码
#     'database': 'pso_voc_tool'   # 数据库名
# }

# # 连接数据库
# def connect_to_db():
#     connection = None
#     try:
#         connection = mysql.connector.connect(**db_config)
#         print("Database connection successful.")
#     except mysql.connector.Error as e:
#         print(f"Error: {e}")
#     return connection

# # 创建表
# def create_table(connection):
#     cursor = connection.cursor()
#     create_table_query = """
#     CREATE TABLE IF NOT EXISTS users (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         username VARCHAR(255) NOT NULL,
#         email VARCHAR(255)
#     );
#     """
#     try:
#         cursor.execute(create_table_query)
#         connection.commit()
#         print("Table created successfully.")
#     except mysql.connector.Error as e:
#         print(f"Error creating table: {e}")

# # 插入数据
# def insert_user(connection, username, email):
#     cursor = connection.cursor()
#     insert_query = "INSERT INTO users (username, email) VALUES (%s, %s)"
#     try:
#         cursor.execute(insert_query, (username, email))
#         connection.commit()
#         print("User inserted successfully.")
#     except mysql.connector.Error as e:
#         print(f"Error inserting user: {e}")

# # 查询数据
# def query_users(connection):
#     cursor = connection.cursor()
#     select_query = "SELECT * FROM users"
#     try:
#         cursor.execute(select_query)
#         users = cursor.fetchall()
#         for user in users:
#             print(f"User ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
#     except mysql.connector.Error as e:
#         print(f"Error querying users: {e}")

# if __name__ == '__main__':
#     # 连接数据库
#     connection = connect_to_db()
    
#     # 创建表
#     if connection:
#         create_table(connection)
        
#         # 插入数据
#         insert_user(connection, 'testuser', 'test@example.com')
        
#         # 查询数据
#         query_users(connection)
        
#         # 关闭数据库连接
#         connection.close()