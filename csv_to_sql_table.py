import mysql.connector
from mysql.connector import Error
import config
import csv

user = config.db_user
password = config.db_password
host = config.db_host
database = config.db_database

try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    cursor = connection.cursor()

    def csv_to_sql_table(csv_file, table_name):
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)

                header = next(reader)  # Skip the header row
                num_columns = len(header)

                # Adjust placeholders based on the presence of 'null'
                placeholders = ', '.join(['%s' if 'null' not in value.lower() else 'NULL' for value in header])
                query = f"INSERT INTO {table_name} VALUES ({placeholders})"

                for row in reader:
                    # Convert empty values to actual Python None values
                    row = [None if value.strip() == '' or 'null' in value.lower() else value for value in row]
                    cursor.execute(query, tuple(row))

                connection.commit()

        except Error as e:
            print(f"Error: {e}")

        
    csv_to_sql_table('data/competitions.csv', 'competitions')
    csv_to_sql_table('data/clubs.csv', 'clubs')
    csv_to_sql_table('data/players.csv', 'players')
    csv_to_sql_table('data/games_cleaned.csv', 'games')
    csv_to_sql_table('data/appearances_cleaned.csv', 'appearances') 
    csv_to_sql_table('data/club_games_cleaned.csv', 'club_games')
    
except Error as e:
    print(f'Error: {e}')

finally:
    cursor.close()
    connection.close()
