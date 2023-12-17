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
    
    column = request.args.get('column', 'player_id')
    order = request.args.get('order', 'asc')
    
    allowed_columns = ['player_id', 'first_name', 'last_name', 'name', 'last_season', 'current_club_id', 'country_of_birth', 'city_of_birth', 'country_of_citizenship', 'date_of_birth', 'foot', 'height_in_cm', 'market_value_in_eur', 'highest_market_value_in_eur']
    allowed_orders = ['asc', 'desc']

    if column not in allowed_columns:
        column = 'player_id'  # Set a default value or handle the error as needed

    if order not in allowed_orders:
        order = 'asc'  # Set a default value or handle the error as needed

    # Define the secondary sort column to resolve ties
    secondary_sort = 'player_id' if column != 'player_id' else 'first_name'

    # Fetch players for the current page
    query = f"SELECT * FROM players WHERE player_id = %s OR name = %s OR first_name LIKE %s OR last_name LIKE %s ORDER BY {column} {order}, {secondary_sort} {order} LIMIT %s OFFSET %s"
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
                           start_page=start_page, end_page=end_page, column=column, order=order, search_query=search_query)
    
    
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
            date_of_birth_input = request.form.get('date_of_birth')
            date_of_birth = None
            if date_of_birth_input:
                try:
                    # Assuming the date format is '%Y-%m-%d', adjust it based on your actual format
                    date_of_birth = datetime.strptime(date_of_birth_input, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format as needed
                    pass

            # Insert the new player into the 'players' table
            if existing_club or current_club_id is None:
                query = """
                    INSERT INTO players 
                    (player_id, first_name, last_name, last_season, current_club_id,
                    player_code, country_of_birth, city_of_birth, country_of_citizenship, date_of_birth)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (player_id, first_name, last_name, last_season, current_club_id,
                                    player_code, country_of_birth, city_of_birth, country_of_citizenship, date_of_birth))
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
            
            date_of_birth_input = request.form.get('date_of_birth')
            updated_date_of_birth = None
            if date_of_birth_input:
                try:
                    # Assuming the date format is '%Y-%m-%d', adjust it based on your actual format
                    updated_date_of_birth = datetime.strptime(date_of_birth_input, '%Y-%m-%d').date()
                except ValueError:
                    # Handle invalid date format as needed
                    pass
                
            if existing_club or updated_current_club_id is None:
                update_query = """
                    UPDATE players 
                    SET first_name = %s, last_name = %s, last_season = %s, 
                        current_club_id = %s, player_code = %s, 
                        country_of_birth = %s, city_of_birth = %s, 
                        country_of_citizenship = %s, date_of_birth = %s
                    WHERE player_id = %s
                """
                cursor.execute(update_query, (updated_first_name, updated_last_name,
                                                updated_last_season, updated_current_club_id,
                                                updated_player_code, updated_country_of_birth,
                                                updated_city_of_birth, updated_country_of_citizenship,
                                                updated_date_of_birth, player_id))
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
