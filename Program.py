from flask import Flask, flash, redirect, render_template, request, session, url_for
import sqlite3
import os.path as path
import datetime

app = Flask(__name__)

# REMOVE CACHING POSSIBILITIES [PDF WILL UPDATE AFTER REFRESH]

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    # r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    # r.headers["Pragma"] = "no-cache"
    # r.headers["Expires"] = "0"
    # r.headers['Cache-Control'] = 'public, max-age=0'
    return r

# HOMEPAGE

@app.route('/')
def index():
    return render_template('home.html')

# MATCHES

@app.route('/matches', methods=['GET', 'POST'])
def matches():
    if request.method == 'POST':
        matchday = int(request.form.get('dateBtn'))
        return redirect(url_for('signup', matchday = matchday, message = ''))

    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()
    match_list = c.execute("SELECT * FROM MATCHDAYS").fetchall()
    player_list = c.execute("SELECT date FROM PLAYER").fetchall()

    matchdays = {i[1]:0 for i in match_list}
    for i in [j[0] for j in player_list]:
        matchdays[i] = matchdays[i] + 1

    match_list = [list(i) + [matchdays[(i[1])]] for i in match_list]

    #print(match_list)
    #return render_template('matches.html')
    return render_template('matches.html', list=match_list, n_list=len(match_list))

# VOLLEYBALL: SIGN UP PAGE

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    matchday = request.args['matchday']
    message = request.args['message']

    if request.method == 'POST':
        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()

        signupname = request.form["uname"]
        signup_firstname, signup_lastname = request.form["uname"].split()[0], ' '.join(request.form["uname"].split()[1:])
        
        # Capacity Check
        check = [(' '.join(i[1:3]),i[-1]) for i in c.execute("SELECT * FROM PLAYER WHERE date="+str(matchday)).fetchall()]
        if len(c.execute("SELECT * FROM PLAYER WHERE date="+str(matchday)).fetchall()) > 50:
            return redirect(url_for('signup', matchday = matchday, message = "Limiet bereikt."))

        # Duplicate Check
        for i in check:
            if i[0] == signupname:
                return redirect(url_for('signup', matchday = matchday, message = signupname + " staat al ingeschreven."))

        # Payment Check
        player_history = c.execute(f"SELECT * FROM PLAYER WHERE firstname='{signup_firstname}' AND lastname='{signup_lastname}'").fetchall()
        payment_history = [int(i[4]) for i in player_history]
        if sum(payment_history) != len(payment_history):
            return redirect(url_for('signup', matchday = matchday, message = "Vorige betalingen niet voldaan."))

        data = [(signup_firstname, signup_lastname, matchday, 0, 'NULL')]
        c.executemany("INSERT INTO PLAYER (firstname, lastname, date, paid, payment_id) VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()
        
        return redirect(url_for('signup', matchday = matchday, message = 'Je bent toegevoegd!'))

    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()
    match_list = c.execute("SELECT * FROM MATCHDAYS WHERE date="+str(matchday)).fetchall()[0]
    player_data = c.execute("SELECT * FROM PLAYER WHERE date="+str(matchday)).fetchall()

    player_attendance = [(' '.join(i[1:3]),i[4]) for i in player_data]

    return render_template('signup.html', match_list = match_list, player_attendance = player_attendance, n_players = len(player_attendance), message = message)

if __name__ == '__main__':
    app.run(host = "0.0.0.0", debug=True)
