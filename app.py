from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
import config
from flask_mysqldb import MySQL
from datetime import datetime

app = Flask(__name__, template_folder='templates')

user = config.db_user
password = config.db_password
host = config.db_host
database = config.db_database

db = mysql.connector.connect(
    host=host,
    user=user,
    password=password,
    database=database
)

cursor = db.cursor()

mysql = MySQL(app)

PER_PAGE = 10  # Number of rows per page

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/view_clubs')
def view_clubs():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    # Fetch clubs for the current page
    query = """SELECT c.*, 
            REPLACE(comp.name, '-', ' ') AS competition_name
            FROM clubs c
            LEFT JOIN competitions comp 
            ON c.domestic_competition_id = comp.domestic_league_code
            WHERE comp.type LIKE 'domestic_league'
            ORDER BY club_id ASC
            LIMIT %s OFFSET %s"""
    
    #query = "SELECT * FROM clubs LIMIT %s OFFSET %s"

    cursor.execute(query, (PER_PAGE, offset))
    clubs = cursor.fetchall()

    # Fetch total number of clubs for pagination
    cursor.execute("SELECT COUNT(*) FROM clubs")
    total_clubs= cursor.fetchone()[0]

    # Calculate total pages based on the number of clubs and per-page limit
    total_pages = (total_clubs + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_clubs.html', clubs=clubs, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)

@app.route('/sort_filter_clubs')
def sort_filter_clubs():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    # Get sorting and filtering parameters from the query string
    
    filters = {
    "name" : request.args.get('name'),
    "sort_by" : request.args.get('sort_by'),
    "stadium_name" : request.args.get('stadium_name'),
    "domestic_competition_name" : request.args.get('domestic_competition_name')
    }

    # Construct the base query
    base_query = """
    FROM clubs c
    LEFT JOIN competitions comp ON c.domestic_competition_id = comp.domestic_league_code
    """
    where_clauses = []
    query_params = []

    # Add filtering conditions
    for key, value in filters.items():
        if key != 'sort_by' and value:
            where_clauses.append(f"{key} LIKE %s")
            query_params.append(f"%{value}%")

    # Complete SQL query for fetching data
    data_query = """
    SELECT c.*, REPLACE(comp.name, '-', ' ') AS competition_name
    """ + base_query
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting condition
    if filters['sort_by'] in ['stadium_seats', 'average_age', 'national_team_players', 'foreigners_percentage']:
        data_query += f" ORDER BY {filters['sort_by']} DESC"
    else:
        data_query += f" ORDER BY c.club_id ASC"
    data_query += " LIMIT %s OFFSET %s"

    # Execute the query for fetching data
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    clubs = cursor.fetchall()

    # Complete SQL query for counting total games
    count_query = f"SELECT COUNT(*) {base_query}"
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    # Execute the query for counting total games
    cursor.execute(count_query, tuple(query_params))
    total_clubs = cursor.fetchone()[0]

    # Calculate total pages and pagination window
    total_pages = (total_clubs + PER_PAGE - 1) // PER_PAGE
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('sort_filter_clubs.html', clubs=clubs, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, **filters)

@app.route('/delete_club/<string:club_id>', methods=['GET', 'POST'])
def delete_club(club_id):
    if request.method == 'POST':
        query = "DELETE FROM clubs WHERE club_id = %s"
        cursor.execute(query, (club_id,))
        db.commit()

        return redirect(url_for('view_clubs'))

    query = "SELECT * FROM clubs WHERE club_id = %s"
    cursor.execute(query, (club_id,))
    club = cursor.fetchone()

    return render_template('delete_club.html', club=club)


@app.route('/view_clubs/add_club', methods=['GET', 'POST'])
def add_club():
    if request.method == 'POST':
        club_id = request.form.get('club_id')
        club_code = request.form.get('club_code')
        name = request.form.get('name')
        domestic_competition_id = request.form.get('domestic_competition_id')
        total_market_value = request.form.get('total_market_value')
        squad_size = request.form.get('squad_size')
        average_age = request.form.get('average_age')
        foreigners_number = request.form.get('foreigners_number')
        foreigners_percentage = request.form.get('foreigners_percentage')
        national_team_players = request.form.get('national_team_players')
        stadium_name = request.form.get('stadium_name')
        stadium_seats = request.form.get('stadium_seats')
        net_transfer_record = request.form.get('net_transfer_record')
        coach_name = request.form.get('coach_name')
        last_season = request.form.get('last_season')
        url = request.form.get('url')
        

        squad_size = int(squad_size) if squad_size else None
        average_age = float(average_age) if average_age else None
        foreigners_number = int(foreigners_number) if foreigners_number else None
        foreigners_percentage = float(foreigners_percentage) if foreigners_percentage else None
        national_team_players = int(national_team_players) if national_team_players else None
        stadium_seats = int(stadium_seats) if stadium_seats else None
        last_season = int(last_season) if last_season else None

        try:
            query = """
                INSERT INTO clubs 
                (club_id, club_code, name, domestic_competition_id, total_market_value,
                 squad_size, average_age, foreigners_number, foreigners_percentage,
                 national_team_players, stadium_name, stadium_seats,
                 net_transfer_record, coach_name, last_season, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (club_id, club_code, name, domestic_competition_id, total_market_value, squad_size, average_age,
                                   foreigners_number, foreigners_percentage, national_team_players, stadium_name, stadium_seats,
                                   net_transfer_record, coach_name, last_season, url))
            db.commit()
            return redirect(url_for('view_clubs'))
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('add_club.html', error_message=error_message)

    return render_template('add_club.html')


@app.route('/update_clubs/<string:club_id>', methods=['GET', 'POST'])
def update_club(club_id):
    get_club_query = "SELECT * FROM clubs WHERE club_id = %s"
    cursor.execute(get_club_query, (club_id,))
    club_details = cursor.fetchone()
    
    if request.method == 'POST':
        try: 
            updated_club_code = request.form.get('club_code')
            updated_name = request.form.get('name')
            updated_domestic_competition_id = request.form.get('domestic_competition_id')
            updated_total_market_value = request.form.get('total_market_value')
            updated_squad_size = request.form.get('squad_size')
            updated_average_age = request.form.get('average_age')
            updated_foreigners_number = request.form.get('foreigners_number')
            updated_foreigners_percentage = request.form.get('foreigners_percentage')
            updated_national_team_players = request.form.get('national_team_players')
            updated_stadium_name = request.form.get('stadium_name')
            updated_stadium_seats = request.form.get('stadium_seats')
            updated_net_transfer_record = request.form.get('net_transfer_record')
            updated_coach_name = request.form.get('coach_name')
            updated_last_season = request.form.get('last_season')
            updated_url = request.form.get('url')
            

            updated_squad_size = int(updated_squad_size) if updated_squad_size else 0
            updated_average_age = float(updated_average_age) if updated_average_age else 0
            updated_foreigners_number = int(updated_foreigners_number) if updated_foreigners_number else 0
            updated_foreigners_percentage = float(updated_foreigners_percentage) if updated_foreigners_percentage else 0
            updated_national_team_players = int(updated_national_team_players) if updated_national_team_players else 0
            updated_stadium_seats = int(updated_stadium_seats) if updated_stadium_seats else 0
            updated_last_season = int(updated_last_season) if updated_last_season else 0

            update_query = """
                UPDATE clubs 
                SET club_code = %s, name = %s, 
                    domestic_competition_id = %s, total_market_value = %s, 
                    squad_size = %s, average_age = %s, 
                    foreigners_number = %s, 
                    foreigners_percentage = %s, national_team_players = %s, 
                    stadium_name = %s, stadium_seats = %s, 
                    net_transfer_record = %s, coach_name = %s, 
                    last_season = %s, url = %s
                WHERE club_id = %s
                """

            cursor.execute(update_query, (
                updated_club_code, updated_name, updated_domestic_competition_id,
                updated_total_market_value, updated_squad_size, updated_average_age, 
                updated_foreigners_number, updated_foreigners_percentage, updated_national_team_players, 
                updated_stadium_name, updated_stadium_seats, updated_net_transfer_record, 
                updated_coach_name, updated_last_season, updated_url, club_id
            ))

            db.commit()
            return redirect(url_for('view_clubs'))
            
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('update_club.html', error_message=error_message, club_details=club_details)
            
    if club_details:
        return render_template('update_club.html', club_details=club_details)

    return redirect(url_for('view_clubs'))


@app.route('/view_games')
def view_games():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    # Fetch games for the current page
    query = """SELECT g.*,
            REPLACE(comp.name, '-', ' ') AS competition_name,
            CONCAT(CAST(g.home_club_goals AS CHAR), '-', CAST(g.away_club_goals AS CHAR)) AS score,
            home_club.name AS home_club_name,
            away_club.name AS away_club_name
            FROM games g
            LEFT JOIN competitions comp ON g.competition_id = comp.competition_id
            LEFT JOIN clubs home_club ON g.home_club_id = home_club.club_id
            LEFT JOIN clubs away_club ON g.away_club_id = away_club.club_id
            ORDER BY g.game_id ASC
            LIMIT %s OFFSET %s
            """
    
    cursor.execute(query, (PER_PAGE, offset))
    games = cursor.fetchall()

    # Fetch total number of games for pagination
    cursor.execute("SELECT COUNT(*) FROM games")
    total_games = cursor.fetchone()[0]

    # Calculate total pages based on the number of games and per-page limit
    total_pages = (total_games + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5 
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_games.html', games=games, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)


@app.route('/sort_filter_games')
def sort_filter_games():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    # Sorting and filtering parameters
    filters = {
        'sort_by' : request.args.get('sort_by'),
        'competition_name': request.args.get('competition_name'),
        'round': request.args.get('round'),
        'home_club_manager_name': request.args.get('home_club_manager_name'),
        'away_club_manager_name': request.args.get('away_club_manager_name'),
        'home_club_name': request.args.get('home_club_name'),
        'away_club_name': request.args.get('away_club_name'),
        'aggregate': request.args.get('aggregate'),
        'competition_type': request.args.get('competition_type'),
        'referee': request.args.get('referee')
    }

    # Construct the base query
    base_query = """
    FROM games g
    LEFT JOIN competitions comp ON g.competition_id = comp.competition_id
    LEFT JOIN clubs home_club ON g.home_club_id = home_club.club_id
    LEFT JOIN clubs away_club ON g.away_club_id = away_club.club_id
    """
    where_clauses = []
    query_params = []

    # Add filtering conditions
    for key, value in filters.items():
        if key != 'sort_by' and value:
            if key == 'competition_name':
                where_clauses.append("REPLACE(comp.name, '-', ' ') LIKE %s")
                query_params.append(f"%{value}%")
            elif key == 'competition_type' and value in ['other', 'domestic_cup', 'international_cup', 'domestic_league']:
                where_clauses.append(f"comp.type = %s")
                query_params.append(value)
            else:
                where_clauses.append(f"g.{key} LIKE %s")  # Ensure to prefix with 'g.'
                query_params.append(f"%{value}%")


    data_query = """
        SELECT g.*,
        REPLACE(comp.name, '-', ' ') AS competition_name,
        CONCAT(CAST(g.home_club_goals AS CHAR), '-', CAST(g.away_club_goals AS CHAR)) AS score,
        home_club.name AS home_club_name,
        away_club.name AS away_club_name
        """ + base_query
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting condition
    if filters['sort_by'] in ['season', 'attendance', 'home_club_goals', 'away_club_goals', 'date']:
        data_query += f" ORDER BY {filters['sort_by']} DESC"
    else:
        data_query += f" ORDER BY g.game_id ASC"
    data_query += " LIMIT %s OFFSET %s"

    # Execute the query for fetching data
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    games = cursor.fetchall()

    # Complete SQL query for counting total games
    count_query = f"SELECT COUNT(*) {base_query}"
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    # Execute the query for counting total games
    cursor.execute(count_query, tuple(query_params))
    total_games = cursor.fetchone()[0]

    # Calculate total pages and pagination window
    total_pages = (total_games + PER_PAGE - 1) // PER_PAGE
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('sort_filter_games.html', games=games, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, **filters)

@app.route('/view_games/add_game', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        # Collecting form data
        game_id = request.form.get('game_id')
        competition_id = request.form.get('competition_id')
        season = request.form.get('season')
        round = request.form.get('round')
        date = request.form.get('date')
        home_club_id = request.form.get('home_club_id')
        away_club_id = request.form.get('away_club_id')
        home_club_goals = request.form.get('home_club_goals') or 0
        away_club_goals = request.form.get('away_club_goals') or 0
        home_club_position = request.form.get('home_club_position') or 0
        away_club_position = request.form.get('away_club_position') or 0
        home_club_manager_name = request.form.get('home_club_manager_name')
        away_club_manager_name = request.form.get('away_club_manager_name')
        stadium = request.form.get('stadium')
        attendance = request.form.get('attendance')
        referee = request.form.get('referee')
        url = request.form.get('url')
        home_club_name = request.form.get('home_club_name')
        away_club_name = request.form.get('away_club_name')
        aggregate = request.form.get('aggregate')
        competition_type = request.form.get('competition_type')

        season = int(season) if season else None
        home_club_goals = int(home_club_goals)
        away_club_goals = int(away_club_goals)
        attendance = int(attendance) if attendance else None
        
        try:
            query = """
                INSERT INTO games 
                (game_id, competition_id, season, round, date, home_club_id, away_club_id,
                home_club_goals, away_club_goals, home_club_position, away_club_position,
                home_club_manager_name, away_club_manager_name, stadium, attendance,
                referee, url, home_club_name, away_club_name, aggregate, competition_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                game_id, competition_id, season, round, date, home_club_id, away_club_id,
                home_club_goals, away_club_goals, home_club_position, away_club_position,
                home_club_manager_name, away_club_manager_name, stadium, attendance,
                referee, url, home_club_name, away_club_name, aggregate, competition_type
            ))
            db.commit()
            return redirect(url_for('view_games'))
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('add_game.html', error_message=error_message)

    return render_template('add_game.html')

@app.route('/update_games/<int:game_id>', methods=['GET', 'POST'])
def update_game(game_id):
    get_game_query = "SELECT * FROM games WHERE game_id = %s"
    cursor.execute(get_game_query, (game_id,))
    game_details = cursor.fetchone()

    if request.method == 'POST':
        competition_id = request.form.get('competition_id')
        season = request.form.get('season')
        round = request.form.get('round')
        date = request.form.get('date')
        home_club_id = request.form.get('home_club_id')
        away_club_id = request.form.get('away_club_id')
        home_club_goals = request.form.get('home_club_goals') or 0
        away_club_goals = request.form.get('away_club_goals') or 0
        home_club_position = request.form.get('home_club_position') or 0
        away_club_position = request.form.get('away_club_position') or 0
        home_club_manager_name = request.form.get('home_club_manager_name')
        away_club_manager_name = request.form.get('away_club_manager_name')
        stadium = request.form.get('stadium')
        attendance = request.form.get('attendance')
        referee = request.form.get('referee')
        url = request.form.get('url')
        home_club_name = request.form.get('home_club_name')
        away_club_name = request.form.get('away_club_name')
        aggregate = request.form.get('aggregate')
        competition_type = request.form.get('competition_type')

        season = int(season) if season else None
        home_club_goals = int(home_club_goals)
        away_club_goals = int(away_club_goals)
        attendance = int(attendance) if attendance else None

        try:
            update_query = """
                UPDATE games
                SET competition_id = %s, season = %s, round = %s, 
                    date = %s, home_club_id = %s, away_club_id = %s,
                    home_club_goals = %s, away_club_goals = %s, 
                    home_club_position = %s, away_club_position = %s,
                    home_club_manager_name = %s, away_club_manager_name = %s,
                    stadium = %s, attendance = %s, referee = %s,
                    url = %s, home_club_name = %s, away_club_name = %s,
                    aggregate = %s, competition_type = %s
                WHERE game_id = %s
                """
            cursor.execute(update_query, (
                competition_id, season, round, date, home_club_id, away_club_id,
                home_club_goals, away_club_goals, home_club_position, away_club_position,
                home_club_manager_name, away_club_manager_name, stadium, attendance,
                referee, url, home_club_name, away_club_name, aggregate, competition_type,
                game_id
            ))
            db.commit()
            return redirect(url_for('view_games'))

        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('update_game.html', error_message=error_message, game_details=game_details)

    if game_details:
        return render_template('update_game.html', game_details=game_details)

    return redirect(url_for('view_games'))


@app.route('/delete_game/<string:game_id>', methods=['GET', 'POST'])
def delete_game(game_id):
    if request.method == 'POST':
        query = "DELETE FROM games WHERE game_id = %s"
        cursor.execute(query, (game_id,))
        db.commit()

        return redirect(url_for('view_games'))

    query = "SELECT * FROM games WHERE game_id = %s"
    cursor.execute(query, (game_id,))
    game = cursor.fetchone()

    return render_template('delete_game.html', game=game)


@app.route('/view_appearances', methods=['GET', 'POST'])
def view_appearances():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    if request.method == 'POST':
        # If the form is submitted, retrieve the search query from the form data
        search_query = request.form.get('search_query', '')
    else:
        # If it's a GET request, retrieve the search query from the URL parameters
        search_query = request.args.get('search_query', '')
        
    # Fetch appearances for the current page
    query = """SELECT a.appearance_id, a.game_id, a.player_id, a.player_club_id, a.player_current_club_id, a.date, 
                a.player_name, a.competition_id, a.yellow_cards, a.red_cards, a.goals, a.assists, a.minutes_played, 
                c1.name as player_club_name, c2.name as player_current_club_name
                FROM  appearances a
                LEFT JOIN 
                    clubs c1 ON a.player_club_id = c1.club_id
                LEFT JOIN 
                    clubs c2 ON a.player_current_club_id = c2.club_id
                WHERE a.player_id = %s OR a.player_name LIKE %s OR a.competition_id = %s
                ORDER BY 
                    a.appearance_id DESC
                LIMIT %s OFFSET %s;
            """

    cursor.execute(query, (search_query, f'%{search_query}%', search_query, PER_PAGE, offset))
    appearances = cursor.fetchall()
    
    # Fetch total number of appearances for pagination with search filtering
    count_query = "SELECT COUNT(*) FROM appearances WHERE player_id = %s OR player_name LIKE %s OR competition_id = %s"
    cursor.execute(count_query, (search_query, f'%{search_query}%', search_query))
    total_appearances = cursor.fetchone()[0]
    
    # Calculate total pages based on the number of appearances and per-page limit
    total_pages = (total_appearances + PER_PAGE - 1) // PER_PAGE
    
    # Define the sliding window for pagination links
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('view_appearances.html', appearances=appearances, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)
    
@app.route('/view_appearances/add_appearance', methods=['GET', 'POST'])
def add_appearance():
    
    if request.method == 'POST':
        try:
            appearance_id = request.form.get('appearance_id')
            
            game_id_input = request.form.get('game_id')
            game_id = int(game_id_input) if game_id_input else None
            
            player_id_input = request.form.get('player_id')
            player_id = int(player_id_input) if player_id_input else None
            
            check_appearance_query = "SELECT appearance_id FROM appearances WHERE appearance_id = %s"
            cursor.execute(check_appearance_query, (appearance_id,))
            existing_appearance = cursor.fetchone()

            if existing_appearance:
                # appearance ID already exists, show an error message
                error_message = "Appearance ID already taken. Please choose a different ID."
                return render_template('add_appearance.html', error_message=error_message)
            
            player_club_id_input = request.form.get('player_club_id')
            player_club_id = int(player_club_id_input) if player_club_id_input else None
            
            player_current_club_id_input = request.form.get('player_current_club_id')
            player_current_club_id = int(player_current_club_id_input) if player_current_club_id_input else None
            
            date = None
            date_input = request.form.get('date')
            if date_input:
                try:
                    # Assuming the date format is '%Y-%m-%d'
                    date = datetime.strptime(date_input, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format as needed
                    pass
            
            player_name = request.form.get('player_name')
            
            competition_id = request.form.get('competition_id')
            
            yellow_cards_input = request.form.get('yellow_cards')
            yellow_cards = int(yellow_cards_input) if yellow_cards_input else None
            
            red_cards_input = request.form.get('red_cards')
            red_cards = int(red_cards_input) if red_cards_input else None
            
            goals_input = request.form.get('goals')
            goals = int(goals_input) if goals_input else None
            
            assists_input = request.form.get('assists')
            assists = int(assists_input) if assists_input else None
            
            minutes_played_input = request.form.get('minutes_played')
            minutes_played = int(minutes_played_input) if minutes_played_input else None
            
            existing_game = None
            if game_id is not None:
                # Check if the game with the given game_id exists
                check_game_query = "SELECT game_id FROM games WHERE game_id = %s"
                cursor.execute(check_game_query, (game_id,))
                existing_game = cursor.fetchone()
            
            existing_player = None
            if player_id is not None:
                # Check if the player with the given player_id exists
                check_player_query = "SELECT player_id FROM players WHERE player_id = %s"
                cursor.execute(check_player_query, (player_id,))
                existing_player = cursor.fetchone()
            
            if competition_id.isdigit() or player_name.isdigit() or appearance_id.isdigit():
                error_message = "Invalid input values. Please try again."
                return render_template('add_appearance.html', error_message=error_message)
            
            if existing_game and existing_player:
                query = """
                    INSERT INTO appearances
                    (appearance_id, game_id, player_id, player_club_id, player_current_club_id, date, player_name, competition_id, yellow_cards, red_cards, goals, assists, minutes_played)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (appearance_id, game_id, player_id, player_club_id, player_current_club_id, date, player_name, competition_id, yellow_cards, red_cards, goals, assists, minutes_played))
                db.commit()
            
                return redirect(url_for('view_appearances'))
        
            else:
                error_message = "Selected game or player does not exist. Please choose an existing game or player or add a new game or player."
                return render_template('add_appearance.html', error_message=error_message)
            
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('add_appearance.html', error_message=error_message)        
    
    return render_template('add_appearance.html')

@app.route('/update_appearance/<string:appearance_id>', methods=['GET', 'POST'])
def update_appearance(appearance_id):
    get_appearance_query = "SELECT * FROM appearances WHERE appearance_id = %s"
    cursor.execute(get_appearance_query, (appearance_id,))
    appearance_details = cursor.fetchone()
    
    if request.method == 'POST':
        try:
            updated_game_id_input = request.form.get('game_id')
            updated_game_id = int(updated_game_id_input) if updated_game_id_input else None
            
            updated_player_id_input = request.form.get('player_id')
            updated_player_id = int(updated_player_id_input) if updated_player_id_input else None
            
            updated_player_club_id_input = request.form.get('player_club_id')
            updated_player_club_id = int(updated_player_club_id_input) if updated_player_club_id_input else None
            
            updated_player_current_club_id_input = request.form.get('player_current_club_id')
            updated_player_current_club_id = int(updated_player_current_club_id_input) if updated_player_current_club_id_input else None
            
            updated_date = None
            updated_date_input = request.form.get('date')
            if updated_date_input:
                try:
                    # Assuming the date format is '%Y-%m-%d'
                    updated_date = datetime.strptime(updated_date_input, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format as needed
                    pass
                
            updated_player_name = request.form.get('player_name')
            
            updated_competition_id = request.form.get('competition_id')
            
            updated_yellow_cards_input = request.form.get('yellow_cards')
            updated_yellow_cards = int(updated_yellow_cards_input) if updated_yellow_cards_input else None
            
            updated_red_cards_input = request.form.get('red_cards')
            updated_red_cards = int(updated_red_cards_input) if updated_red_cards_input else None
            
            updated_goals_input = request.form.get('goals')
            updated_goals = int(updated_goals_input) if updated_goals_input else None
            
            updated_assists_input = request.form.get('assists')
            updated_assists = int(updated_assists_input) if updated_assists_input else None
            
            updated_minutes_played_input = request.form.get('minutes_played')
            updated_minutes_played = int(updated_minutes_played_input) if updated_minutes_played_input else None
            
            existing_game = None
            if updated_game_id is not None:
                # Check if the game with the given game_id exists
                check_game_query = "SELECT game_id FROM games WHERE game_id = %s"
                cursor.execute(check_game_query, (updated_game_id,))
                existing_game = cursor.fetchone()

            existing_player = None
            if updated_player_id is not None:
                # Check if the player with the given player_id exists
                check_player_query = "SELECT player_id FROM players WHERE player_id = %s"
                cursor.execute(check_player_query, (updated_player_id,))
                existing_player = cursor.fetchone()
                
            if updated_competition_id.isdigit() or updated_player_name.isdigit() or appearance_id.isdigit():
                error_message = "Invalid input values. Please try again."
                return render_template('update_appearance.html', error_message=error_message, appearance_details=appearance_details)
            
            if existing_game and existing_player:
                update_query = """
                    UPDATE appearances 
                    SET game_id = %s, player_id = %s, player_club_id = %s, player_current_club_id = %s, date = %s, player_name = %s, competition_id = %s, yellow_cards = %s, red_cards = %s, goals = %s, assists = %s, minutes_played = %s
                    WHERE appearance_id = %s
                    """
                cursor.execute(update_query, (updated_game_id, updated_player_id, updated_player_club_id, updated_player_current_club_id, updated_date, updated_player_name, updated_competition_id, updated_yellow_cards, updated_red_cards, updated_goals, updated_assists, updated_minutes_played, appearance_id))
                db.commit()
            
                return redirect(url_for('view_appearances'))
            
            else:
                error_message = "Selected game or player does not exist. Please choose an existing game or player or add a new game or player."
                return render_template('update_appearance.html', error_message=error_message, appearance_details=appearance_details)
            
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('update_appearance.html', error_message=error_message, appearance_details=appearance_details)
        
    if appearance_details:
        return render_template('update_appearance.html', appearance_details=appearance_details)
    
    return redirect(url_for('view_appearances'))

@app.route('/delete_appearance/<appearance_id>', methods=['GET', 'POST'])
def delete_appearance(appearance_id):
    if request.method == 'POST':
        query = "DELETE FROM appearances WHERE appearance_id = %s"
        cursor.execute(query, (appearance_id,))
        db.commit()

        return redirect(url_for('view_appearances'))

    # If it's a GET request, fetch player details and render the delete_player.html template
    query = "SELECT * FROM appearances WHERE appearance_id = %s"
    cursor.execute(query, (appearance_id,))
    appearance = cursor.fetchone()

    return render_template('delete_appearance.html', appearance=appearance)

@app.route('/sort_filter_appearances')
def sort_filter_appearances():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    # Get sorting and filtering parameters from the query string
    filters = {
        'player_name': request.args.get('player_name'),
        'player_id': request.args.get('player_id'),
        'date': request.args.get('date'),
        'competition_id': request.args.get('competition_id'),
        'sort_by': request.args.get('sort_by'),
        'yellow_cards': request.args.get('yellow_cards'),
        'red_cards': request.args.get('red_cards'),
        'assists': request.args.get('assists'),
        'goals': request.args.get('goals'),
        'minutes_played': request.args.get('minutes_played')
    }

    # Construct the base query
    base_query = "FROM appearances"
    where_clauses = []
    query_params = []

    # Add filtering conditions
    for key, value in filters.items():
        if key != 'sort_by' and value:
            where_clauses.append(f"{key} LIKE %s")
            query_params.append(f"%{value}%")

    # Complete SQL query for fetching data
    data_query = f"SELECT * {base_query}"
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting condition
    if filters['sort_by'] in ['yellow_cards', 'red_cards', 'goals', 'assists', 'minutes_played']:
        data_query += f" ORDER BY {filters['sort_by']} ASC"
    data_query += " LIMIT %s OFFSET %s"

    # Execute the query for fetching data
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    appearances = cursor.fetchall()

    # Complete SQL query for counting total games
    count_query = f"SELECT COUNT(*) {base_query}"
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    # Execute the query for counting total games
    cursor.execute(count_query, tuple(query_params))
    total_appearances = cursor.fetchone()[0]

    # Calculate total pages and pagination window
    total_pages = (total_appearances + PER_PAGE - 1) // PER_PAGE
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('sort_filter_appearances.html', appearances=appearances, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, **filters)
    

@app.route('/view_players', methods=['GET', 'POST'])
def view_players():
    if request.method == 'POST':
        # If the form is submitted, retrieve the search query from the form data
        search_query = request.form.get('search_query', '')
    else:
        # If it's a GET request, retrieve the search query from the URL parameters
        search_query = request.args.get('search_query', '')
        
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    # Fetch players for the current page
    query = f"SELECT * FROM players WHERE player_id = %s OR name = %s OR first_name LIKE %s OR last_name LIKE %s LIMIT %s OFFSET %s"
    cursor.execute(query, (search_query, search_query, f'%{search_query}%', f'%{search_query}%', PER_PAGE, offset))
    players = cursor.fetchall()

    # Fetch total number of players for pagination with search filtering
    total_query = "SELECT COUNT(*) FROM players WHERE first_name LIKE %s OR last_name LIKE %s"
    cursor.execute(total_query, (f'%{search_query}%', f'%{search_query}%'))
    total_players = cursor.fetchone()[0]

    # Calculate total pages based on the number of players and per-page limit
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_players.html', players=players, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, search_query=search_query)
    
@app.route('/player_features')
def player_features():
    return render_template('player_features.html')

@app.route('/max_goals')
def max_goals():
    query = """SELECT a.player_id, p.first_name, p.last_name, a.game_id, a.goals
                FROM appearances a
                JOIN players p ON a.player_id = p.player_id
                WHERE a.goals = (
                    SELECT MAX(goals)
                    FROM appearances)
            """
    cursor.execute(query)
    result = cursor.fetchall()
    return render_template('max_goals.html', result=result)


@app.route('/top_earners')
def top_earners(): 
    query = """SELECT player_id, name, current_club_name, market_value_in_eur, highest_market_value_in_eur
                FROM players
                ORDER BY market_value_in_eur DESC
                LIMIT 10"""
    cursor.execute(query)
    result = cursor.fetchall()
    return render_template('top_earners.html', result=result)

@app.route('/highest_goal_clubs')
def highest_goal_clubs():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    query = """SELECT c.club_id, c.name, AVG(a.goals) AS avg_goals_per_game
            FROM clubs c
            JOIN appearances a ON c.club_id = a.player_club_id
            GROUP BY c.club_id, c.name
            HAVING AVG(a.goals) > 0.15
            ORDER BY avg_goals_per_game DESC
            LIMIT %s OFFSET %s
            """
    cursor.execute(query, (PER_PAGE, offset))
    result = cursor.fetchall()
    
    total_query = """SELECT COUNT(*)
                    FROM (
                        SELECT c.club_id, c.name, AVG(a.goals) AS avg_goals_per_game
                        FROM clubs c
                        JOIN appearances a ON c.club_id = a.player_club_id
                        GROUP BY c.club_id, c.name
                        HAVING AVG(a.goals) > 0.15
                    ) AS subquery"""
                    
    cursor.execute(total_query)
    total_clubs = cursor.fetchone()[0]
    
    total_pages = (total_clubs + PER_PAGE - 1) // PER_PAGE
    
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('highest_goal_clubs.html', result=result, page=page, total_pages=total_pages,
                            start_page=start_page, end_page=end_page)
    
@app.route('/players_total_goals')
def players_total_goals():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    query = """SELECT p.player_id, p.name, SUM(a.goals) AS total_goals
            FROM players p
            LEFT JOIN appearances a ON p.player_id = a.player_id
            GROUP BY p.player_id, p.name
            ORDER BY total_goals DESC
            LIMIT %s OFFSET %s"""
            
    cursor.execute(query, (PER_PAGE, offset))
    result = cursor.fetchall()  
    
    total_query = """SELECT COUNT(*)
                    FROM (
                        SELECT p.player_id, p.first_name, p.last_name, COALESCE(SUM(a.goals), 0) AS total_goals
                        FROM players p
                        LEFT JOIN appearances a ON p.player_id = a.player_id
                        GROUP BY p.player_id, p.first_name, p.last_name
                    ) AS subquery"""
    cursor.execute(total_query)
    total_players = cursor.fetchone()[0]
    
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE
    
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('players_total_goals.html', result=result, page=page, total_pages=total_pages,
                            start_page=start_page, end_page=end_page)
    
@app.route('/players_competitions')
def players_competitions():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    query = """SELECT p.player_id, p.name, COUNT(DISTINCT a.competition_id) AS competitions
            FROM players p
            JOIN appearances a ON p.player_id = a.player_id
            GROUP BY p.player_id, p.name
            ORDER BY competitions DESC
            LIMIT %s OFFSET %s"""
    
    cursor.execute(query, (PER_PAGE, offset))
    result = cursor.fetchall()
    
    total_query = """SELECT COUNT(*)
                    FROM (
                        SELECT p.player_id, p.name, COUNT(DISTINCT a.competition_id) AS competitions
                        FROM players p
                        JOIN appearances a ON p.player_id = a.player_id
                        GROUP BY p.player_id, p.name
                    ) AS subquery"""
                    
    cursor.execute(total_query)
    total_players = cursor.fetchone()[0]
    
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE
    
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('players_competitions.html', result=result, page=page, total_pages=total_pages,
                            start_page=start_page, end_page=end_page)           

@app.route('/players/decade/<int:decade>', methods=['GET'])
def decade_players(decade):
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    start_date = f'{decade}-01-01'
    end_date = f'{decade+9}-12-31'
    
    query = """SELECT player_id, name, current_club_name, date_of_birth
                FROM players
                WHERE date_of_birth BETWEEN %s AND %s
                ORDER BY date_of_birth ASC
                LIMIT %s OFFSET %s"""
    cursor.execute(query, (start_date, end_date, PER_PAGE, offset))
    players = cursor.fetchall()
    
    total_query = """SELECT COUNT(*)
                    FROM players
                    WHERE date_of_birth BETWEEN %s AND %s"""
    cursor.execute(total_query, (start_date, end_date))
    total_players = cursor.fetchone()[0]
    
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE
    
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('decade_players.html', players=players, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, decade=decade)

@app.route('/turkish_players')
def turkish_players():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    query = """SELECT player_id, name, current_club_name, date_of_birth, city_of_birth, country_of_birth, country_of_citizenship
                FROM players
                WHERE country_of_citizenship = 'Turkey'
                LIMIT %s OFFSET %s"""
    cursor.execute(query, (PER_PAGE, offset))
    result = cursor.fetchall()
    
    count_query = """SELECT COUNT(*)
                        FROM players
                        WHERE country_of_citizenship = 'Turkey'"""
    cursor.execute(count_query)
    total_players = cursor.fetchone()[0]
    
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE
    
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('turkish_players.html', result=result, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)
    
@app.route('/view_players/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        try:
            player_id = int(request.form.get('player_id'))

            # Check if the player ID already exists
            check_player_query = "SELECT player_id FROM players WHERE player_id = %s"
            cursor.execute(check_player_query, (player_id,))
            existing_player = cursor.fetchone()

            if existing_player:
                # Player ID already exists, show an error message
                error_message = "Player ID already taken. Please choose a different ID."
                return render_template('add_player.html', error_message=error_message)

            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            
            name = first_name + ' ' + last_name
            
            last_season_input = request.form.get('last_season')
            last_season = int(last_season_input) if last_season_input else None
            
            current_club_id_input = request.form.get('current_club_id')
            current_club_id = int(current_club_id_input) if current_club_id_input else None
            
            existing_club = None
            if current_club_id is not None:
                # Check if the club with the given current_club_id exists
                check_club_query = "SELECT club_id FROM clubs WHERE club_id = %s"
                cursor.execute(check_club_query, (current_club_id,))
                existing_club = cursor.fetchone()
            
            player_code = request.form.get('player_code')
            country_of_birth = request.form.get('country_of_birth')
            city_of_birth = request.form.get('city_of_birth')
            country_of_citizenship = request.form.get('country_of_citizenship')
            sub_position = request.form.get('sub_position')
            position = request.form.get('position')
            foot = request.form.get('foot')
            
            height_in_cm_input = request.form.get('height_in_cm')
            height_in_cm = int(height_in_cm_input) if height_in_cm_input else None
            
            market_value_in_eur_input = request.form.get('market_value_in_eur')
            market_value_in_eur = int(market_value_in_eur_input) if market_value_in_eur_input else None
            
            if country_of_birth.isdigit() or country_of_citizenship.isdigit() or city_of_birth.isdigit() or player_code.isdigit() or sub_position.isdigit() or position.isdigit() or foot.isdigit():
                error_message = "Invalid input values. Please try again."
                return render_template('add_player.html', error_message=error_message)
            
            date_of_birth_input = request.form.get('date_of_birth')
            date_of_birth = None
            
            if date_of_birth_input:
                try:
                    # Assuming the date format is '%Y-%m-%d'
                    date_of_birth = datetime.strptime(date_of_birth_input, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format as needed
                    pass
            
            # Insert the new player into the 'players' table
            if existing_club or current_club_id is None:
                query = """
                    INSERT INTO players 
                    (player_id, first_name, last_name, name, last_season, current_club_id, player_code, 
                    country_of_birth, city_of_birth, country_of_citizenship, date_of_birth, sub_position, 
                    position, foot, height_in_cm, market_value_in_eur)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (player_id, first_name, last_name, name, last_season, current_club_id,
                                    player_code, country_of_birth, city_of_birth, country_of_citizenship, date_of_birth, sub_position,
                                    position, foot, height_in_cm, market_value_in_eur))
                db.commit()

                # Redirect to the view_players page after adding the player
                return redirect(url_for('view_players'))

            else:
                # Club does not exist, so we cannot add the player
                error_message = "Selected club does not exist. Please choose an existing club or add a new club."
                return render_template('add_player.html', error_message=error_message)
        except ValueError as e:
            # Handle invalid input values as needed
            error_message = "Invalid input values. Please try again."
            return render_template('add_player.html', error_message=error_message)

    # If it's a GET request, simply render the form to add a player
    return render_template('add_player.html')

@app.route('/sort_filter_players')
def sort_filter_players():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE

    # Get sorting and filtering parameters from the query string
    filters = {
        'name': request.args.get('name'),
        'country_of_birth': request.args.get('country_of_birth'),
        'country_of_citizenship': request.args.get('country_of_citizenship'),
        'current_club_name': request.args.get('current_club_name'),
        'last_season': request.args.get('last_season'),
        'sub_position': request.args.get('sub_position'),
        'position': request.args.get('position'),
        'foot': request.args.get('foot'),
        'sort_by': request.args.get('sort_by'),
    }

    # Construct the base query
    base_query = "FROM players"
    where_clauses = []
    query_params = []

    # Add filtering conditions
    for key, value in filters.items():
        if key != 'sort_by' and value:
            where_clauses.append(f"{key} LIKE %s")
            query_params.append(f"%{value}%")

    # Complete SQL query for fetching data
    data_query = f"SELECT * {base_query}"
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting condition
    if filters['sort_by'] in ['name', 'last_season', 'country_of_citizenship', 'date_of_birth', 'height_in_cm', 'market_value_in_eur', 'highest_market_value_in_eur']:
        data_query += f" ORDER BY {filters['sort_by']} ASC"
    data_query += " LIMIT %s OFFSET %s"

    # Execute the query for fetching data
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    players = cursor.fetchall()

    # Complete SQL query for counting total games
    count_query = f"SELECT COUNT(*) {base_query}"
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    # Execute the query for counting total games
    cursor.execute(count_query, tuple(query_params))
    total_players = cursor.fetchone()[0]

    # Calculate total pages and pagination window
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('sort_filter_players.html', players=players, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, **filters)

@app.route('/delete_player/<int:player_id>', methods=['GET', 'POST'])
def delete_player(player_id):
    if request.method == 'POST':
        # Delete the player from the 'players' table
        query = "DELETE FROM players WHERE player_id = %s"
        cursor.execute(query, (player_id,))
        db.commit()

        # Redirect to the view_players page after deleting the player
        return redirect(url_for('view_players'))

    # If it's a GET request, fetch player details and render the delete_player.html template
    query = "SELECT * FROM players WHERE player_id = %s"
    cursor.execute(query, (player_id,))
    player = cursor.fetchone()

    return render_template('delete_player.html', player=player)

@app.route('/player/<int:player_id>')
def player_page(player_id):
    query = "SELECT * FROM players WHERE player_id = %s"
    cursor.execute(query, (player_id,))
    player_details = cursor.fetchone()
    return render_template('player_page.html', player_id=player_id, player_details=player_details)

@app.route('/update_player/<int:player_id>', methods=['GET', 'POST'])
def update_player(player_id):
    get_player_query = "SELECT * FROM players WHERE player_id = %s"
    cursor.execute(get_player_query, (player_id,))
    player_details = cursor.fetchone()
    
    if request.method == 'POST':
        try:
            # Get updated player details from the form
            updated_first_name = request.form.get('first_name')
            updated_last_name = request.form.get('last_name')
            
            updated_name = updated_first_name + ' ' + updated_last_name
            
            last_season_input = request.form.get('last_season')
            updated_last_season = int(last_season_input) if last_season_input else None

            current_club_id_input = request.form.get('current_club_id')
            updated_current_club_id = int(current_club_id_input) if current_club_id_input else None
            
            existing_club = None
            if updated_current_club_id is not None:
                # Check if the club with the given current_club_id exists
                check_club_query = "SELECT club_id FROM clubs WHERE club_id = %s"
                cursor.execute(check_club_query, (updated_current_club_id,))
                existing_club = cursor.fetchone()
                
            updated_player_code = request.form.get('player_code')
            updated_country_of_birth = request.form.get('country_of_birth')
            updated_city_of_birth = request.form.get('city_of_birth')
            updated_country_of_citizenship = request.form.get('country_of_citizenship')
            updated_sub_position = request.form.get('sub_position')
            updated_position = request.form.get('position')
            updated_foot = request.form.get('foot')
            
            updated_height_in_cm_input = request.form.get('height_in_cm')
            updated_height_in_cm = int(updated_height_in_cm_input) if updated_height_in_cm_input else None
            
            updated_market_value_in_eur_input = request.form.get('market_value_in_eur')
            updated_market_value_in_eur = int(updated_market_value_in_eur_input) if updated_market_value_in_eur_input else None
            
            if updated_country_of_birth.isdigit() or updated_country_of_citizenship.isdigit() or updated_city_of_birth.isdigit() or updated_player_code.isdigit() or updated_sub_position.isdigit() or updated_position.isdigit() or updated_foot.isdigit():
                error_message = "Invalid input values. Please try again."
                return render_template('add_player.html', error_message=error_message)
            
            date_of_birth_input = request.form.get('date_of_birth')
            updated_date_of_birth = None
            if date_of_birth_input:
                try:
                    updated_date_of_birth = datetime.strptime(date_of_birth_input, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format as needed
                    pass
                
            if existing_club or updated_current_club_id is None:
                update_query = """
                    UPDATE players 
                    SET first_name = %s, last_name = %s, name = %s, last_season = %s, 
                        current_club_id = %s, player_code = %s, 
                        country_of_birth = %s, city_of_birth = %s, 
                        country_of_citizenship = %s, date_of_birth = %s, sub_position = %s,
                        position = %s, foot = %s, height_in_cm = %s, market_value_in_eur = %s
                    WHERE player_id = %s
                """
                cursor.execute(update_query, (updated_first_name, updated_last_name, updated_name,
                                                updated_last_season, updated_current_club_id,
                                                updated_player_code, updated_country_of_birth,
                                                updated_city_of_birth, updated_country_of_citizenship,
                                                updated_date_of_birth, updated_sub_position, updated_position, updated_foot, 
                                                updated_height_in_cm, updated_market_value_in_eur, player_id))
                db.commit()

            # Redirect to the view_players page after updating the player
                return redirect(url_for('view_players'))

            else:
                error_message = "Selected club does not exist. Please choose an existing club or add a new club."
                return render_template('update_player.html', error_message=error_message, player_details=player_details)
            
        except ValueError as e:
            # Handle invalid input values as needed
            error_message = "Invalid input values. Please try again."
            return render_template('update_player.html', error_message=error_message, player_details=player_details)

    # If it's a GET request or there's an error, retrieve the player details and render the update form
    if player_details:
        # Player found, render the update form
        return render_template('update_player.html', player_details=player_details)

    # Player not found, redirect to the view_players page
    return redirect(url_for('view_players'))


@app.route('/view_competitions', methods=['GET', 'POST'])
def view_competitions():
    
    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
    else:
        search_query = request.args.get('search_query', '')
        
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
        
    # Fetch competitions for the current page
    query = f"SELECT * FROM competitions WHERE competition_id = %s OR competition_code LIKE %s OR name LIKE %s LIMIT %s OFFSET %s"
    cursor.execute(query, (search_query, f'%{search_query}%', f'%{search_query}%', PER_PAGE, offset))
    competitions = cursor.fetchall()

    # Fetch total number of competitions for pagination
    total_query = "SELECT COUNT(*) FROM competitions WHERE competition_code LIKE %s OR name LIKE %s" 
    cursor.execute(total_query, (f'%{search_query}%', f'%{search_query}%'))
    total_competitions = cursor.fetchone()[0]

    # Calculate total pages based on the number of competitions and per-page limit
    total_pages = (total_competitions + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_competitions.html', competitions=competitions, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, search_query=search_query)

@app.route('/view_competitions/add_competition', methods=['GET', 'POST'])
def add_competition():
    if request.method == 'POST':
        try: 
            competition_id = request.form.get('competition_id')
            
            check_competition_query = "SELECT competition_id FROM competitions WHERE competition_id = %s"
            cursor.execute(check_competition_query, (competition_id,))
            existing_competition = cursor.fetchone()

            if existing_competition:
                error_message = "Competition ID already taken. Please choose a different ID."
                return render_template('add_competition.html', error_message=error_message)
            
            competition_code = request.form.get('competition_code')
            name = request.form.get('name')
            sub_type = request.form.get('sub_type')
            type = request.form.get('type')
            country_id = int(request.form.get('country_id'))
            country_name = request.form.get('country_name')
            domestic_league_code = request.form.get('domestic_league_code')
            confederation = request.form.get('confederation')
            
            query = """
                INSERT INTO competitions 
                (competition_id, competition_code, name, sub_type, type,
                country_id, country_name, domestic_league_code, confederation)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (competition_id, competition_code, name, sub_type, type, country_id, country_name, domestic_league_code, confederation))
            db.commit()
            return redirect(url_for('view_competitions'))
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('add_competition.html', error_message=error_message)
    return render_template('add_competition.html')

@app.route('/sort_filter_competitions')
def sort_filter_competitions():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    filters = {
        'competition_code': request.args.get('competition_code'),
        'name': request.args.get('name'),
        'sub_type': request.args.get('sub_type'),
        'type': request.args.get('type'),
        'country_name': request.args.get('country_name'),
        'confederation': request.args.get('confederation'),
        'sort_by': request.args.get('sort_by'),
    }
    
    base_query = "FROM competitions"
    where_clauses = []
    query_params = []

    for key, value in filters.items():
        if key != 'sort_by' and value:
            where_clauses.append(f"{key} LIKE %s")
            query_params.append(f"%{value}%")

    data_query = f"SELECT * {base_query}"
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    if filters['sort_by'] in ['competition_code', 'name', 'sub_type', 'type', 'country_name', 'confederation']:
        data_query += f" ORDER BY {filters['sort_by']} ASC"
    data_query += " LIMIT %s OFFSET %s"

    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    competitions = cursor.fetchall()

    count_query = f"SELECT COUNT(*) {base_query}"
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    cursor.execute(count_query, tuple(query_params))
    total_competitions = cursor.fetchone()[0]

    total_pages = (total_competitions + PER_PAGE - 1) // PER_PAGE
    visible_pages = 5
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('sort_filter_competitions.html', competitions=competitions, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page, **filters)
    
@app.route('/delete_competition/<string:competition_id>', methods=['GET', 'POST'])
def delete_competition(competition_id):
    if request.method == 'POST':
        query = "DELETE FROM competitions WHERE competition_id = %s"
        cursor.execute(query, (competition_id,))
        db.commit()

        return redirect(url_for('view_competitions'))

    query = "SELECT * FROM competitions WHERE competition_id = %s"
    cursor.execute(query, (competition_id,))
    competition = cursor.fetchone()

    return render_template('delete_competition.html', competition=competition)

@app.route('/update_competitions/<string:competition_id>', methods=['GET', 'POST'])
def update_competition(competition_id):
    get_competition_query = "SELECT * FROM competitions WHERE competition_id = %s"
    cursor.execute(get_competition_query, (competition_id,))
    competition_details = cursor.fetchone()
    
    if request.method == 'POST':
        try: 
            updated_competition_code = request.form.get('competition_code')
            updated_name = request.form.get('name')
            updated_sub_type = request.form.get('sub_type')
            updated_type = request.form.get('type')
            updated_country_id = int(request.form.get('country_id'))
            updated_country_name = request.form.get('country_name')
            updated_domestic_league_code = request.form.get('domestic_league_code')
            updated_confederation = request.form.get('confederation')
            
            update_query = """
                UPDATE competitions 
                SET competition_code = %s, name = %s, sub_type = %s, 
                    type = %s, country_id = %s, 
                    country_name = %s, domestic_league_code = %s, 
                    confederation = %s WHERE competition_id = %s
                    """
            
            cursor.execute(update_query, (updated_competition_code, updated_name,
                                            updated_sub_type, updated_type,
                                            updated_country_id, updated_country_name,
                                            updated_domestic_league_code, updated_confederation,
                                            competition_id))
            db.commit()
            return redirect(url_for('view_competitions'))
            
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('update_competition.html', error_message=error_message, competition_details=competition_details)
            
    if competition_details:
        return render_template('update_competition.html', competition_details=competition_details)

    return redirect(url_for('view_competitions'))

@app.route('/view_club_games', methods=['GET', 'POST']) 
def view_club_games():
    if request.method == 'POST':
        search_query = request.form.get('search_query', '') 
    else:
        search_query = request.args.get('search_query', '')
    
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    
    query = """SELECT cg.game_id, cg.club_id, c1.name, cg.own_goals, cg.own_position, cg.own_manager_name,
                        cg.opponent_id, c2.name, cg.opponent_goals, cg. opponent_position, cg.opponent_manager_name, 
                        cg.hosting, cg.is_win 
                        FROM club_games cg 
                        LEFT JOIN clubs c1 ON cg.club_id = c1.club_id
                        LEFT JOIN clubs c2 ON cg.opponent_id = c2.club_id
                        WHERE cg.game_id = %s OR cg.club_id = %s OR cg.opponent_id = %s OR c1.name LIKE %s OR c2.name LIKE %s
                        ORDER BY cg.game_id DESC LIMIT %s OFFSET %s"""
    cursor.execute(query, (search_query, search_query, search_query, f'%{search_query}%', f'%{search_query}%', PER_PAGE, offset))
    club_games = cursor.fetchall()
    
    total_query = """SELECT COUNT(*) FROM club_games cg 
                        LEFT JOIN clubs c1 ON cg.club_id = c1.club_id
                        LEFT JOIN clubs c2 ON cg.opponent_id = c2.club_id
                        WHERE cg.game_id = %s OR cg.club_id = %s OR cg.opponent_id = %s OR c1.name LIKE %s OR c2.name LIKE %s
                        ORDER BY cg.game_id DESC"""
    cursor.execute(total_query, (search_query, search_query, search_query, f'%{search_query}%', f'%{search_query}%'))  
    total_club_games = cursor.fetchone()[0]

    total_pages = (total_club_games + PER_PAGE - 1) // PER_PAGE
    
    visible_pages = 5 
    half_window = visible_pages // 2     
    start_page = max(1, page - half_window)  
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_club_games.html', club_games=club_games, page=page, total_pages=total_pages,
                            start_page=start_page, end_page=end_page, search_query=search_query)



@app.route('/club_game_statistics')
def club_game_statistics():
    return render_template('club_game_statistics.html')

@app.route('/top_managers')
def top_managers():
    query = """SELECT own_manager_name, COUNT(is_win) AS winning
            FROM club_games
            GROUP BY own_manager_name
            ORDER BY COUNT(is_win) DESC
            LIMIT 10
            """
    cursor.execute(query)
    result = cursor.fetchall()
    return render_template('top_managers.html', result=result)


@app.route('/max_goal_count')
def max_goal_count(): 
    query = """SELECT g.home_club_name, g.away_club_name,
            SUM(cg.own_goals + cg.opponent_goals) AS total_goals
            FROM club_games cg
            JOIN games g ON cg.game_id = g.game_id
            GROUP BY g.home_club_name, g.away_club_name
            HAVING g.home_club_name IS NOT NULL AND g.away_club_name IS NOT NULL
            ORDER BY total_goals DESC
            LIMIT 10"""
    cursor.execute(query)
    result = cursor.fetchall()
    return render_template('max_goal_count.html', result=result)

@app.route('/away_game_success')
def away_game_success():
    query = """SELECT g.away_club_name, COUNT(cg.is_win)
            FROM club_games cg
            JOIN games g ON cg.game_id = g.game_id
            GROUP BY g.away_club_name
            HAVING g.away_club_name IS NOT NULL
            ORDER BY COUNT(is_win) DESC
            LIMIT 10"""
    cursor.execute(query)
    result = cursor.fetchall()
    return render_template('away_game_success.html', result=result)

@app.route('/view_club_games/add_club_game', methods=['GET', 'POST'])
def add_club_game():
    if request.method == 'POST':  
        try: 
            game_id_input = request.form.get('game_id')  
            game_id = int(game_id_input) if game_id_input else None 
            existing_game = None 
            
            if game_id is not None: 
                check_game_query = "SELECT game_id FROM games WHERE game_id = %s"
                cursor.execute(check_game_query, (game_id,)) 
                existing_game = cursor.fetchone()
                
            club_id_input = request.form.get('club_id')  
            club_id = int(club_id_input) if club_id_input else None  
            existing_club = None  
            
            if club_id is not None:  
                check_club_query = "SELECT club_id FROM clubs WHERE club_id = %s"
                cursor.execute(check_club_query, (club_id,))  
                existing_club = cursor.fetchone() 
           
            check_club_game_query = "SELECT game_id, club_id FROM club_games WHERE game_id = %s AND club_id = %s"
            cursor.execute(check_club_game_query, (game_id,club_id,))
            existing_club_game = cursor.fetchone()  
            
            if existing_club_game:  
                error_message = "Club Game key already taken. Please choose a different key." 
                return render_template('add_club_game.html', error_message=error_message) 
        
            own_goals = int(request.form.get('own_goals'))  
            own_position = int(request.form.get('own_position'))
            own_manager_name = request.form.get('own_manager_name')
            opponent_id = int(request.form.get('opponent_id')) 
            opponent_goals = int(request.form.get('opponent_goals'))
            opponent_position = int(request.form.get('opponent_position')) 
            opponent_manager_name = request.form.get('opponent_manager_name')
            hosting = request.form.get('hosting')
            is_win = int(request.form.get('is_win'))

            if existing_club and existing_game: 
                query = """  
                    INSERT INTO club_games   
                    (game_id, club_id, own_goals, own_position, own_manager_name, opponent_id, opponent_goals,  
                    opponent_position, opponent_manager_name, hosting, is_win) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                """  
                cursor.execute(query, (game_id, club_id, own_goals, own_position, own_manager_name, opponent_id, opponent_goals, 
                opponent_position, opponent_manager_name, hosting, is_win))  
                db.commit()
                return redirect(url_for('view_club_games'))
            else:  
                error_message = "Selected club or game does not exist. Please choose an existing club and game."  
                return render_template('add_club_game.html', error_message=error_message) 
        except ValueError as e:  
            # Handle invalid input values as needed 
            error_message = "Invalid input values. Please try again."
            return render_template('add_club_game.html', error_message=error_message)
    return render_template('add_club_game.html')


@app.route('/sort_filter_club_games')
def sort_filter_club_games():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE 
    
    filters = { 
        'own_manager_name': request.args.get('own_manager_name'), 
        'opponent_manager_name': request.args.get('opponent_manager_name'),  
        'hosting': request.args.get('hosting'), 
        'is_win': request.args.get('is_win'),
        'sort_by': request.args.get('sort_by'),
    }
    
    base_query = "FROM club_games"
    where_clauses = []
    query_params = []
    
    for key, value in filters.items(): 
        if key != 'sort_by' and value: 
            where_clauses.append(f"{key} LIKE %s")  
            query_params.append(f"%{value}%")
            
    data_query = f"SELECT * {base_query}" 
    if where_clauses: 
        data_query += " WHERE " + " AND ".join(where_clauses)
        
    if filters['sort_by'] in ['own_goals', 'own_position', 'opponent_goals', 'opponent_position']:
        data_query += f" ORDER BY {filters['sort_by']} DESC" 
    data_query += " LIMIT %s OFFSET %s" 
    
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    club_games = cursor.fetchall()
    
    count_query = f"SELECT COUNT(*) {base_query}" 
    if where_clauses: 
        count_query += " WHERE " + " AND ".join(where_clauses) 
        
    cursor.execute(count_query, tuple(query_params))
    total_club_games = cursor.fetchone()[0]
    
    total_pages = (total_club_games + PER_PAGE - 1) // PER_PAGE 
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    return render_template('sort_filter_club_games.html', club_games=club_games, page=page, total_pages=total_pages, 
                            start_page=start_page, end_page=end_page, **filters)
    
    
@app.route('/delete_club_game/<int:game_id>', methods=['GET', 'POST']) 
def delete_club_game(game_id): 
    if request.method == 'POST':
        query = "DELETE FROM club_games WHERE game_id = %s"
        cursor.execute(query, (game_id,))
        db.commit()
        return redirect(url_for('view_club_games')) 
    
    query = "SELECT * FROM club_games WHERE game_id = %s" 
    cursor.execute(query, (game_id,)) 
    club_game = cursor.fetchall()[0]
    return render_template('delete_club_game.html', club_game=club_game) 

@app.route('/update_club_game/<int:game_id>/<int:club_id>', methods=['GET', 'POST'])
def update_club_game(game_id, club_id):
    get_club_game_query = "SELECT * FROM club_games WHERE game_id = %s AND club_id = %s"
    cursor.execute(get_club_game_query, (game_id, club_id,))
    club_game_details = cursor.fetchone()
    
    if request.method == 'POST':
        try:       
            updated_own_goals = int(request.form.get('own_goals'))
            updated_own_position = int(request.form.get('own_position'))
            updated_own_manager_name = request.form.get('own_manager_name') 
            updated_opponent_goals = int(request.form.get('opponent_goals'))
            updated_opponent_position = int(request.form.get('opponent_position'))
            updated_opponent_manager_name = request.form.get('opponent_manager_name') 
            updated_hosting = request.form.get('hosting')
            updated_is_win = int(request.form.get('is_win'))
            
            update_query = """ 
                UPDATE club_games  
                SET own_goals = %s, own_position = %s, own_manager_name = %s, opponent_goals = %s,  
                opponent_position = %s, opponent_manager_name = %s,  
                hosting = %s, is_win = %s 
                WHERE game_id = %s AND club_id = %s 
            """  
            cursor.execute(update_query, (updated_own_goals, updated_own_position, 
                            updated_own_manager_name,
                            updated_opponent_goals, updated_opponent_position, 
                            updated_opponent_manager_name, updated_hosting,  
                            updated_is_win, game_id, club_id)) 
            db.commit() 
            return redirect(url_for('view_club_games'))
        except ValueError as e:
            error_message = "Invalid input values. Please try again."
            return render_template('update_club_game.html', error_message=error_message, club_game_details=club_game_details)
    if club_game_details: 
        return render_template('update_club_game.html', club_game_details=club_game_details)
    
    return redirect(url_for('view_club_games'))


if __name__ == '__main__':
    app.run(debug=True)
