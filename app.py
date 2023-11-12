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
        game_id INT PRIMARY KEY,
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
        FOREIGN KEY (opponent_id) REFERENCES games(club_id),
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

        CREATE TABLE games (
            game_id INT PRIMARY KEY, 

            competition_id VARCHAR(50) NOT NULL, 
            season INT, 
            round VARCHAR(50), 
            date DATE, 
            home_club_id INT NOT NULL,
            away_club_id INT NOT NULL, 
            home_club_goals INT, 
            away_club_goals INT,
            home_club_position INT, 
            away_club_position INT, 
            home_club_manager_name VARCHAR(50),
            away_club_manager_name VARCHAR(50), 
            stadium VARCHAR(50), 
            attendance INT, 
            referee VARCHAR(50), 
            url VARCHAR(255),
            home_club_name VARCHAR(50), 
            away_club_name VARCHAR(50), 
            aggregate VARCHAR(50), 
            competition_type VARCHAR(50)

            FOREIGN KEY (competition_id) REFERENCES competitions(competition_id),
            FOREIGN KEY (home_club_id) REFERENCES clubs(club_id)
            FOREIGN KEY (away_club_id) REFERENCES clubs(club_id)
        );

        CREATE TABLE clubs (
            club_id INT PRIMARY KEY, 

            club_code VARCHAR(50), 
            name VARCHAR(50), 
            domestic_competition_id INT NOT NULL,
            total_market_value VARCHAR(50), 
            squad_size INT, 
            average_age DECIMAL(3,1), 
            foreigners_number INT,
            foreigners_percentage DECIMAL(3,1), 
            national_team_players INT, 
            stadium_name VARCHAR(50),
            stadium_seats INT, 
            net_transfer_record VARCHAR(50), 
            coach_name VARCHAR(50), 
            last_season INT,
            url VARCHAR(255)

            FOREIGN KEY (domestic_competition_id) REFERENCES competitions(competition_id),
        );
    '''

    cursor.execute(create_table_queries)
    print('Tables created.')

except Error as e:
    print(f'Error: {e}')

finally:
    cursor.close()
    connection.close()
