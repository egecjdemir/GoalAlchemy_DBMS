from flask import Flask, render_template, request, jsonify
import mysql.connector
import config
from flask_mysqldb import MySQL

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
    query = "SELECT * FROM clubs LIMIT %s OFFSET %s"
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
    domestic_competition_id = request.args.get('domestic_competition_id')

    # Construct the base query
    base_query = "FROM clubs"
    where_clauses = []
    query_params = []

    # Add filtering conditions
    if name:
        where_clauses.append("name LIKE %s")
        query_params.append(f"%{name}%")
    if stadium_name:
        where_clauses.append("stadium_name LIKE %s")
        query_params.append(f"%{stadium_name}%")
    if domestic_competition_id:
        where_clauses.append("domestic_competition_id = %s")
        query_params.append(domestic_competition_id)

    # Complete SQL query for fetching data
    data_query = "SELECT * " + base_query
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)

    # Add sorting condition
    if sort_by in ['stadium_seats', 'average_age', 'national_team_players', 'foreigners_percentage']:
        data_query += f" ORDER BY {sort_by} DESC"
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
    query = "SELECT * FROM games LIMIT %s OFFSET %s"
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
        'competition_id': request.args.get('competition_id'),
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
    base_query = "FROM games"
    where_clauses = []
    query_params = []

    # Add filtering conditions
    for key, value in filter_params.items():
        if value:
            if key == 'competition_type' and value in ['other', 'domestic_cup', 'international_cup', 'domestic_league']:
                where_clauses.append(f"{key} = %s")
                query_params.append(value)
            else:
                where_clauses.append(f"{key} LIKE %s")
                query_params.append(f"%{value}%")

    # Complete SQL query for fetching data
    data_query = "SELECT * " + base_query
    if where_clauses:
        data_query += " WHERE " + " AND ".join(where_clauses)
    if sort_by:
        data_query += f" ORDER BY {sort_by}"
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

@app.route('/view_appearances')
def view_appearances():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    # Fetch appearances for the current page
    query = "SELECT * FROM appearances LIMIT %s OFFSET %s"
    cursor.execute(query, (PER_PAGE, offset))
    appearances = cursor.fetchall()

    # Fetch total number of appearances for pagination
    cursor.execute("SELECT COUNT(*) FROM appearances")
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

@app.route('/view_players', methods=['GET','POST'])
def view_players():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    # Fetch players for the current page
    query = "SELECT * FROM players LIMIT %s OFFSET %s"
    cursor.execute(query, (PER_PAGE, offset))
    players = cursor.fetchall()

    # Fetch total number of players for pagination
    cursor.execute("SELECT COUNT(*) FROM players")
    total_players = cursor.fetchone()[0]

    # Calculate total pages based on the number of players and per-page limit
    total_pages = (total_players + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)
    
    (playerId, firstName, lastName, playerHeight, playerWeight) = (request.form['playerId'], request.form['firstName'], request.form['lastName'], request.form['playerHeight'], request.form['playerWeight'])
    cursor.execute('INSERT INTO Master (playerId, firstName, lastName, height, weight) VALUES (?, ?, ?, ?, ?)', (playerId, firstName, lastName, playerHeight, playerWeight))
    print(cursor.rowcount)

    myRow = cursor.execute('SELECT * FROM Master WHERE playerId = ?', (playerId,)).fetchone()

    print(myRow)
    
    return render_template('view_players.html', players=players, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)

@app.route('/view_club_games', methods=['GET'])
def view_club_games():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    # Fetch club_games for the current page
    query = "SELECT * FROM club_games LIMIT %s OFFSET %s"
    cursor.execute(query, (PER_PAGE, offset))
    club_games = cursor.fetchall()

    # Fetch total number of club_games for pagination
    cursor.execute("SELECT COUNT(*) FROM club_games")
    total_club_games = cursor.fetchone()[0]

    # Calculate total pages based on the number of club_games and per-page limit
    total_pages = (total_club_games + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_club_games.html', club_games=club_games, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)

@app.route('/view_competitions')
def view_competitions():
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * PER_PAGE
    # Fetch competitions for the current page
    query = "SELECT * FROM competitions LIMIT %s OFFSET %s"
    cursor.execute(query, (PER_PAGE, offset))
    competitions = cursor.fetchall()

    # Fetch total number of competitions for pagination
    cursor.execute("SELECT COUNT(*) FROM competitions")
    total_competitions = cursor.fetchone()[0]

    # Calculate total pages based on the number of competitions and per-page limit
    total_pages = (total_competitions + PER_PAGE - 1) // PER_PAGE

    # Define the sliding window for pagination links
    visible_pages = 5  
    half_window = visible_pages // 2
    start_page = max(1, page - half_window)
    end_page = min(total_pages, start_page + visible_pages - 1)

    return render_template('view_competitions.html', competitions=competitions, page=page, total_pages=total_pages,
                           start_page=start_page, end_page=end_page)
@app.route('/add_competition')
def add_competition():
    return render_template('add_competition.html')

@app.route('/add_competition', methods=['POST'])
def insert_competition():
    (competition_id, competition_code, name, sub_type, type, country_id, country_name, domestic_league_code, confederation, url) = (request.form['competition_id'], request.form['competition_code'], request.form['name'], request.form['sub_type'], request.form['type'], request.form['country_id'], request.form['country_name'], request.form['domestic_league_code'], request.form['confederation'], request.form['url'])
    cursor.execute('INSERT INTO Competitions (competition_id, competition_code, name, sub_type, type, country_id, country_name, domestic_league_code, confederation, url) VALUES (?,?,?,?,?,?,?,?,?,?)', (competition_id, competition_code, name, sub_type, type, country_id, country_name, domestic_league_code, confederation, url))
    print(cursor.rowcount)
  
    new_row = cursor.execute('SELECT * FROM Competitions WHERE competition_id = ?', (competition_id)).fetchone()
    print(new_row)
    return render_template('add_competition.html')

@app.route('/add_club_game')
def add_club_game():
    return render_template('add_club_game.html')

@app.route('/add_club_game', methods=['POST'])
def insert_club_game():
    (game_id, club_id, own_goals, own_position, own_manager_name, opponent_id, opponent_goals, opponent_position, opponent_manager_name, hosting, is_win) = (request.form['game_id'], request.form['club_id'], request.form['own_goals'], request.form['own_position'], request.form['own_manager_name'], request.form['opponent_id'], request.form['opponent_goals'], request.form['opponent_position'], request.form['opponent_manager_name'], request.form['hosting'], request.form['is_win'])
    cursor.execute('INSERT INTO competitions (game_id, club_id, own_goals, own_position, own_manager_name, opponent_id, opponent_goals, opponent_position, opponent_manager_name, hosting, is_win) VALUES (?,?,?,?,?,?,?,?,?,?,?)', (game_id, club_id, own_goals, own_position, own_manager_name, opponent_id, opponent_goals, opponent_position, opponent_manager_name, hosting, is_win))
    print(cursor.rowcount)
  
    new_row = cursor.execute('SELECT * FROM club_games WHERE club_id = ? AND game_id = ?', (club_id,game_id)).fetchone()
    print(new_row)
    return render_template('add_club_game.html')

if __name__ == '__main__':
    app.run(debug=True)
