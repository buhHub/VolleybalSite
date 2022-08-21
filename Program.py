from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
import sqlite3
import os.path as path
import datetime

app = Flask(__name__)

def getData(mode="all"):
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    match_list = {i[0]: list(i[1:]) for i in c.execute("SELECT * FROM MATCHDAYS").fetchall()}
    player_list = {i[0]:' '.join(i[1:]) for i in c.execute("SELECT * FROM PLAYER").fetchall()}
    data_list = {i[0]: list(i[1:]) for i in c.execute("SELECT * FROM DATA").fetchall()}

    # Data_list manupalation:
    #   {i: [name, match, new, tent, p_id]}
    for (n, data) in data_list.items():
        data_list[n][0] = player_list[data[0]]
        data_list[n][1] = match_list[data[1]][0]

    match_n = {data[0]:0 for i, data in match_list.items()}
    for i in [data[1] for j,data in data_list.items()]:
        match_n[i] = match_n[i] + 1

    match_list = {i: data + [match_n[data[0]]] for i, data in match_list.items()}

    if mode == "match":
        return match_list
    elif mode == "player":
        return player_list
    elif mode == "all":
        return data_list
    else:
        print("Empty")
        return 0
    


# REMOVE CACHING POSSIBILITIES [PDF WILL UPDATE AFTER REFRESH]

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
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

    match_list = getData("match")
    print(match_list.values())
    print(len(match_list))

    return render_template('matches.html', list=list(match_list.values()), n_list=len(match_list))

# VOLLEYBALL: SIGN UP PAGE

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    matchday = request.args['matchday']
    message = request.args['message']
    
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    if request.method == 'POST':

        signupname = request.form["uname"]
        signup_firstname, signup_lastname = request.form["uname"].split()[0], ' '.join(request.form["uname"].split()[1:])
        
        # Capacity Check
        max_limit = [i for i in list(getData("match").values()) if i[0]==matchday][0][4]
        n_participants = len([i for i in list(getData().values()) if i[1] == matchday])
        if n_participants >= max_limit:
            return redirect(url_for('signup', matchday = matchday, message = "Limiet bereikt."))

        # Duplicate Check
        participants = [i for i in list(getData().values()) if i[1] == matchday]
        for i in participants:
            if i[0] == signupname:
                return redirect(url_for('signup', matchday = matchday, message = signupname + " staat al ingeschreven."))

        # Payment Check
        player_id = c.execute(f"SELECT id FROM PLAYER WHERE firstname='{signup_firstname}' AND lastname='{signup_lastname}'").fetchall()[0][0]
        print("---------------\n",player_id,"\n---------------\n")
        player_history = [i for i in list(getData().values()) if i[0] == signupname]
        print("---------------\n",player_history,"\n---------------\n")
        payment_history = [0 if i[4] == 'NULL' else 1 for i in player_history]
        print("---------------\n",payment_history,"\n---------------\n")

        if sum(payment_history) != len(payment_history):
            return redirect(url_for('signup', matchday = matchday, message = "Vorige betalingen niet voldaan."))

        data = [(signup_firstname, signup_lastname, matchday, 0, 'NULL')]
        # c.executemany("INSERT INTO PLAYER (firstname, lastname, date, paid, payment_id) VALUES (?, ?, ?, ?, ?)", data)
        # conn.commit()
        
        return redirect(url_for('signup', matchday = matchday, message = 'Je bent toegevoegd!'))

    match_list = c.execute("SELECT * FROM MATCHDAYS WHERE date="+str(matchday)).fetchall()[0]
    participants_data = [i for i in list(getData().values()) if i[1]==matchday]
    # player_data = c.execute("SELECT * FROM DATA WHERE match_id="+str(match_list[0])).fetchall()

    participant_names = [i[0] for i in participants_data]
    all_names = set(getData("player").values())

    names = list(all_names.difference(set(participant_names)))
    names.sort()

    return render_template('signup.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))

if __name__ == '__main__':
    app.run(host = "0.0.0.0", debug=True)
