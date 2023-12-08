from flask import Flask, render_template, request, jsonify

app = Flask(__name__ )

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/clubs')
def clubs():
    return render_template('clubs.html')

@app.route('/games')
def games():
    return render_template('games.html')

@app.route('/appearances')
def appearances():
    return render_template('appearances.html')

@app.route('/club_games')
def club_games():
    return render_template('club_games.html')

@app.route('/competitions')
def competitions():
    return render_template('competitions.html')

@app.route('/game_events')
def game_events():
    return render_template('game_events.html')

if __name__ == '__main__':
    app.run()