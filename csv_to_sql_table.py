import mysql.connector
from mysql.connector import Error
import configparser
import csv

config = configparser.ConfigParser()
config.read('config.py')

user = config.get('database', 'user')
password = config.get('database', 'password')
host = config.get('database', 'host')
database = config.get('database', 'database')

try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    cursor = connection.cursor()

    def csv_to_sql_table(file_path, table_name):
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)

            header = next(reader)
            num_columns = len(header)

            placeholders = ', '.join(['%s'] * num_columns)

            for row in reader:
                cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", tuple(row))

        connection.commit()

    csv_to_sql_table('data/clubs.csv', 'clubs')
    csv_to_sql_table('data/games.csv', 'games')
    csv_to_sql_table('data/players.csv', 'players')
    csv_to_sql_table('data/appearances.csv', 'appearances')
    csv_to_sql_table('data/competitions.csv', 'competitions')
    csv_to_sql_table('data/clubgames.csv', 'club games')
    
except Error as e:
    print(f'Error: {e}')

finally:
    cursor.close()
    connection.close()
