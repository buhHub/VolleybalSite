from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, abort
import sqlite3
import os.path as path
import datetime
import requests

import os
import time

from mollie.api.client import Client
from mollie.api.error import Error
import mollie

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
    
def create_payment(matchday, names, price):
    api_key = "test_k9tafBmqUy3ATSVUVywAjGqtAqhVR7"
    mollie_client = Client()
    mollie_client.set_api_key(api_key)

    my_webshop_id = int(time.time())
    payment = mollie_client.payments.create(
        {
            "amount": {"currency": "EUR", "value": (price)},
            "description": f"Volleybal betaling {matchday}",
            "webhookUrl": f"http://143.177.144.137/webhook",
            "redirectUrl": f"http://143.177.144.137/payment?matchday={matchday}&message=",
            "metadata": {"my_webshop_id": str(my_webshop_id)},
            "method": "ideal"
        }
    )

    data = {"status": payment.status}
    print(payment)

    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    for name in names:
        firstname, lastname = name.split(' ')[0], ' '.join(name.split(' ')[1:])
        player_id = c.execute(f"SELECT id FROM PLAYER WHERE firstname='{firstname}' AND lastname='{lastname}'").fetchall()[0][0]
        match_id = c.execute(f"SELECT id FROM MATCHDAYS WHERE date='{matchday}'").fetchall()[0][0]

        print(player_id, match_id, payment.id)

        c.execute(f"UPDATE DATA SET payment_id='{payment.id}' WHERE player_id='{player_id}' AND match_id='{match_id}'")
    conn.commit()

    return payment.checkout_url


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

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if "id" not in request.form:
            abort(404, "Unknown payment id")

    payment_id = request.form["id"]
    
    api_key = "test_k9tafBmqUy3ATSVUVywAjGqtAqhVR7"
    mollie_client = Client()
    mollie_client.set_api_key(api_key)
    payment = mollie_client.payments.get(payment_id)

    for key, value in payment.items():
        print(f"{key}: ",value)

    if payment.status == 'paid':
        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()

        c.execute(f"UPDATE DATA SET paid=1 WHERE payment_id='{payment.id}'")
        conn.commit()


    return 'succes', 200

# HOMEPAGE

@app.route('/')
def index():
    return render_template('home.html')

# MATCHES

@app.route('/matches', methods=['GET', 'POST'])
def matches():
    if request.method == 'POST':
        matchday = int(request.form.get('dateBtn'))
        open = [i for i in list(getData("match").values()) if i[0] == str(matchday)][0]
        if not open[5]:
            return redirect(url_for('payment', matchday = matchday, message = ''))
        else:
            return redirect(url_for('signup', matchday = matchday, message = ''))

    match_list = getData("match")

    return render_template('matches.html', list=list(match_list.values()), n_list=len(match_list))

# VOLLEYBALL: PAYMENT PAGE

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    matchday = request.args['matchday']
    message = request.args['message']
    
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    if request.method == 'POST':

        not_paid = [j[0] for j in [i for i in list(getData().values()) if i[5] == 0 and i[1] == matchday]]
        print(not_paid)

        n_payments = sum([1 if request.form.get(name) else 0 for name in not_paid])
        print(n_payments)

        price = float([i for i in list(getData("match").values()) if i[0] == matchday][0][6])
        print(price)

        total_price = n_payments * price

        checkout_url = create_payment(matchday, not_paid, "{:.2f}".format(total_price))
        return redirect(checkout_url)
                
        return redirect(url_for('payment', matchday = matchday, message = 'Je bent toegevoegd!'))

    match_list = c.execute("SELECT * FROM MATCHDAYS WHERE date="+str(matchday)).fetchall()[0]
    participants_data = [i for i in list(getData().values()) if i[1]==matchday]
    # player_data = c.execute("SELECT * FROM DATA WHERE match_id="+str(match_list[0])).fetchall()

    participant_names = [i[0] for i in participants_data]
    all_names = set(getData("player").values())

    names = list(all_names.difference(set(participant_names)))
    names.sort()

    return render_template('payment.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))


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
