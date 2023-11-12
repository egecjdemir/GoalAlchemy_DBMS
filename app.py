import mysql.connector
from mysql.connector import Error
import configparser

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

    create_table_queries = '''
        CREATE TABLE appearances (
        appearance_id INT PRIMARY KEY,
        game_id INT NOT NULL,
        player_id INT NOT NULL,
        player_club_id INT,
        player_current_club_id INT,
        date DATE,
        player_name VARCHAR(255),
        competition_id INT,
        yellow_cards INT,
        red_cards INT,
        goals INT,
        assists INT,
        minutes_played INT,  
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (game_id) REFERENCES games(game_id));
        
        CREATE TABLE club_games (
        game_id INT NOT NULL,
        club_id INT NOT NULL,
        own_goals INT,
        own_position INT,
        own_manager_name VARCHAR(255),
        opponent_id INT,
        opponent_goals INT,
        opponent_position INT,
        opponent_manager_name VARCHAR(255),
        hosting VARCHAR(50),
        is_win BOOLEAN,
        FOREIGN KEY (game_id) REFERENCES games(game_id),
        FOREIGN KEY (club_id) REFERENCES clubs(club_id)
        );
        
        CREATE TABLE competitions (
        competition_id VARCHAR(50) PRIMARY KEY,
        competition_code VARCHAR(50) NOT NULL,
        name VARCHAR(255),
        sub_type VARCHAR(50),
        type VARCHAR(50),
        country_id INT,
        country_name VARCHAR(50),
        domestic_league_code VARCHAR(50),
        confederation VARCHAR(50),
        url VARCHAR(255)
        )
    '''

    cursor.execute(create_table_queries)
    print('Tables created.')

except Error as e:
    print(f'Error: {e}')

finally:
    cursor.close()
    connection.close()