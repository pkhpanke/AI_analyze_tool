import mysql.connector
from mysql.connector import Error

def connect_to_database(host,port, user, password, database):
    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        print("Successfully connected to the database")
        return connection
    except Error as e:
        print(f"Error connecting to the database: {e}")
        return None

def execute_sql_file(sql_file_path, connection):
    with open(sql_file_path, 'r') as file:
        sql_statements = file.read()

    # Split the SQL file into individual statements
    statements = sql_statements.split(';')

    cursor = connection.cursor()
    for statement in statements:
        if statement.strip():
            try:
                cursor.execute(statement)
                connection.commit()
                print("Executed SQL statement successfully")
            except Error as e:
                print(f"Error executing SQL statement: {e}")

def query_database(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM user_information")
        rows = cursor.fetchall()
        print("Database content:")
        for row in rows:
            print(row)
    except Error as e:
        print(f"Error querying the database: {e}")

def main():
    # Connect to the new database where you want to import the data
    new_db_config = {
        'host':'aitoolsql-aitoolsql.g.aivencloud.com',
        'port': '21968',
        'user':'avnadmin',
        'password':'AVNS_cnTwp6q_no-QkuZoNmW',
        'database':'defaultdb'
    }
    new_db_connection = connect_to_database(**new_db_config)

    if new_db_connection:
        # Path to your .sql file
        sql_file_path = 'panke.sql'
        
        # Execute the SQL statements from the file
        execute_sql_file(sql_file_path, new_db_connection)
        
        # Query the database to verify the import
        query_database(new_db_connection)
        
        # Close the database connection
        new_db_connection.close()

if __name__ == '__main__':
    main()