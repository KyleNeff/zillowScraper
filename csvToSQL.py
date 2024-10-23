import pandas as pd
import mysql.connector
from mysql.connector import Error

def csvToSQLDatabase(location):
    print("Starting")
    csv_file = f'{location}.csv'
    data = pd.read_csv(csv_file)

    # Replace hyphens with underscores to avoid issues
    table_name = location.replace('-', '_')

    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',          
            user='root',                
            password='MusicRecPassword', 
            database='zillowscraping'   
        )

        if connection.is_connected():
            print(f"Successfully connected to the database. Using table '{table_name}'.")

            cursor = connection.cursor()

            create_table_query = f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,  -- Auto-incrementing primary key
                latitude DECIMAL(10, 6),            -- Latitude with precision to 6 decimal places
                longitude DECIMAL(10, 6),           -- Longitude with precision to 6 decimal places
                address VARCHAR(255),                -- String for the address, max length of 255 characters
                floorSize INT,                       -- Integer for floor size in square feet
                url TEXT,                            -- Text for the URL (since URLs can be long)
                price INT                            -- Decimal for price
            );
            '''
            cursor.execute(create_table_query)

            for index, row in data.iterrows():
                insert_query = f'''
                INSERT INTO {table_name} (latitude, longitude, address, floorSize, url, price)
                VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cursor.execute(insert_query, tuple(row))

            connection.commit()
            print(f"Successfully committed data to table '{table_name}'.")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")

