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
    sort_by = request.args.get('sort_by')
    name = request.args.get('name')
    stadium_name = request.args.get('stadium_name')
    domestic_competition_name = request.args.get('domestic_competition_name')

    # Construct the base query
    base_query = """
    FROM clubs c
    LEFT JOIN competitions comp ON c.domestic_competition_id = comp.domestic_league_code
    """
    where_clauses = ["comp.type LIKE 'domestic_league'"]  # Start with this condition
    query_params = []

    # Add filtering conditions
    if name:
        where_clauses.append("c.name LIKE %s")  # Prefix with 'c.' for the clubs table
        query_params.append(f"%{name}%")
    if stadium_name:
        where_clauses.append("c.stadium_name LIKE %s")  # Prefix with 'c.' for the clubs table
        query_params.append(f"%{stadium_name}%")
    if domestic_competition_name:
        where_clauses.append("REPLACE(comp.name, '-', ' ') LIKE %s")  # Use 'comp.name' with REPLACE function
        query_params.append(f"%{domestic_competition_name}%")


    # Complete SQL query for fetching data
    data_query = """
    SELECT c.*, REPLACE(comp.name, '-', ' ') AS competition_name
    """ + base_query
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting condition
    if sort_by in ['stadium_seats', 'average_age', 'national_team_players', 'foreigners_percentage']:
        data_query += f" ORDER BY {sort_by} DESC"
    else:
        data_query += f" ORDER BY c.club_id ASC"
    data_query += " LIMIT %s OFFSET %s"

    # Execute the query for fetching data
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    clubs = cursor.fetchall()

    # Complete SQL query for counting total games
    count_query = "SELECT COUNT(*) " + base_query
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
                           start_page=start_page, end_page=end_page)

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
    sort_by = request.args.get('sort_by')
    filter_params = {
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
    for key, value in filter_params.items():
        if value:
            if key == 'competition_name':
                where_clauses.append("REPLACE(comp.name, '-', ' ') LIKE %s")
                query_params.append(f"%{value}%")
            elif key == 'competition_type' and value in ['other', 'domestic_cup', 'international_cup', 'domestic_league']:
                where_clauses.append(f"comp.type = %s")
                query_params.append(value)
            else:
                where_clauses.append(f"g.{key} LIKE %s")  # Ensure to prefix with 'g.'
                query_params.append(f"%{value}%")

    # Complete SQL query for fetching data
    data_query = """
    SELECT g.*,
    REPLACE(comp.name, '-', ' ') AS competition_name,
    CONCAT(CAST(g.home_club_goals AS CHAR), '-', CAST(g.away_club_goals AS CHAR)) AS score,
    home_club.name AS home_club_name,
    away_club.name AS away_club_name
    """ + base_query
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)
    if sort_by:
        data_query += f" ORDER BY g.{sort_by}" 
    else:
        data_query += f" ORDER BY g.game_id ASC" 
    data_query += " LIMIT %s OFFSET %s"

    # Execute the query for fetching data
    cursor.execute(data_query, tuple(query_params + [PER_PAGE, offset]))
    games = cursor.fetchall()

    # Complete SQL query for counting total games
    count_query = "SELECT COUNT(*) " + base_query
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
                           start_page=start_page, end_page=end_page)

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
        appearance_id = request.form.get('appearance_id')
        game_id = request.form.get('game_id')
        player_id = request.form.get('player_id')
        player_club_id = request.form.get('player_club_id')
        player_current_club_id = request.form.get('player_current_club_id')
        date = request.form.get('date')
        player_name = request.form.get('player_name')
        competition_id = request.form.get('competition_id')
        yellow_cards = request.form.get('yellow_cards')
        red_cards = request.form.get('red_cards')
        goals = request.form.get('goals')
        assists = request.form.get('assists')
        minutes_played = request.form.get('minutes_played')
        
        query = """
            INSERT INTO appearances 
            (appearance_id, game_id, player_id, player_club_id, player_current_club_id, date, player_name, competition_id, yellow_cards, red_cards, goals, assists, minutes_played)"""
        cursor.execute(query, (appearance_id, game_id, player_id, player_club_id, player_current_club_id, date, player_name, competition_id, yellow_cards, red_cards, goals, assists, minutes_played))
        db.commit()
        
        return redirect(url_for('view_appearances'))
    
    return render_template('add_appearance.html')

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
