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

@app.route('/view_players', methods=['GET'])
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


if __name__ == '__main__':
    app.run(debug=True)
