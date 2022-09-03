from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, abort
import sqlite3
import os.path as path
import datetime
import random
import Functions
import json

import os
import time

from mollie.api.client import Client
from mollie.api.error import Error
import mollie

app = Flask(__name__)

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
    for key, value in request.environ.items():
        print(f"{key}\t\t {value}")
    return render_template('home.html')

# ADMIN ADD LOCATION

@app.route('/addlocation', methods=['GET', 'POST'])
def addlocation():
    if request.method == 'POST':

        title, details, max = request.form["title"], request.form["address"] + ", " + request.form["zipcode"] + " " + request.form["city"], request.form["capacity"]
        print(title, details, max)

        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()
        
        c.executemany("INSERT INTO LOCATIONS (name, details, max) VALUES (?, ?, ?)", [(title, details, max)])
        conn.commit()
        return redirect(url_for('admincreatematch'))
    return render_template('addlocation.html')

# ADMIN

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        matchday = int(request.form.get('dateBtn'))
        return redirect(url_for('adminmatch', matchday = matchday, message = ''))
    match_list = Functions.getData("match")
    return render_template('admin.html', list=list(match_list.values())[::-1], n_list=len(match_list))
    
# ADMIN: MATCH MANAGEMENT

@app.route('/adminmatch', methods=['GET', 'POST'])
def adminmatch():
    matchday = request.args['matchday']
    matchday_id = [key for key, value in Functions.getData("match").items() if value[0] == matchday][0]
    message = request.args['message']
    
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    if request.method == 'POST':
        status = c.execute(f"SELECT status FROM MATCHDAYS WHERE id='{matchday_id}'").fetchall()[0][0]
        new_status = request.form.get("save")

        price = "{:.2f}".format(float(request.form.get("price")))
            
        if new_status == "ended" and price == "0.00":
            return redirect(url_for('adminmatch', matchday = matchday, message = "Prijs kan geen 0 zijn."))

        c.execute(f"UPDATE MATCHDAYS SET price='{price}' WHERE id='{matchday_id}'") 
        conn.commit()

        if status != new_status and new_status != None:
            c.execute(f"UPDATE MATCHDAYS SET status='{new_status}' WHERE id='{matchday_id}'")
            conn.commit()
            return redirect(url_for('adminmatch', matchday = matchday, message = "Status en prijs geupdate"))

        if status == "open":
            if len(request.form.get("uname")) == 0:
                participants = [j[0] for j in [i for i in list(Functions.getData().values()) if i[1] == matchday]]
                unsubscribers = list(set([name for name in participants if request.form.get(name) == 'on']))
                unsubscribers_ids = [key for key, value in Functions.getData("player").items() if value in unsubscribers]
                matchday_id = c.execute(f"SELECT id FROM MATCHDAYS WHERE date='{matchday}'").fetchall()[0][0]

                for n in unsubscribers_ids:
                    c.execute(f"DELETE FROM DATA WHERE player_id='{n}' AND match_id='{matchday_id}'")

                conn.commit()

                new_message = f"Volgende spelers zijn verwijderd van de lijst: \n {' - '.join(unsubscribers)}"
                return redirect(url_for('adminmatch', matchday = matchday, message = new_message))
            else:
                print("Admin adding person")
                signupname = request.form["uname"]
                signup_firstname, signup_lastname = request.form["uname"].split()[0], ' '.join(request.form["uname"].split()[1:])
                newbie = 0

                status = Functions.signupcheck(matchday, signupname)

                if status == "unknown_p":
                    newbie = 1
                    pass
                elif status == "full":
                    return redirect(url_for('adminmatch', matchday = matchday, message = "Limiet bereikt."))
                elif status == "duplicate":
                    return redirect(url_for('adminmatch', matchday = matchday, message = signupname + " staat al ingeschreven."))
                elif status == "not_paid":
                    return redirect(url_for('adminmatch', matchday = matchday, message = "Vorige betalingen niet voldaan."))
                elif status == "allowed":
                    pass
                player_id = list(Functions.get_id("player",signupname).keys())[0]
                data = [(player_id, matchday_id,newbie,0, 'NULL', 0)]
                c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", data)
                conn.commit()
                
                return redirect(url_for('adminmatch', matchday = matchday, message = 'Je bent toegevoegd!'))  
        elif status == "ended": 
            print(request.form)
            participants = [j[0] for j in [i for i in list(Functions.getData().values()) if i[1] == matchday]]
            payers = list(set([name for name in participants if request.form.get(name) == 'on']))
            payers_ids = [key for key, value in Functions.getData("player").items() if value in payers]
            matchday_id = c.execute(f"SELECT id FROM MATCHDAYS WHERE date='{matchday}'").fetchall()[0][0]

            print(participants, payers, payers_ids, matchday_id)

            ip = request.environ.get("REMOTE_ADDR")
            dt = datetime.datetime.now().strftime("%Y%m%d %H%M%S")
            db_message = f"Manually modified on {ip} at {dt}"

            for n in payers_ids:
                if c.execute(f"SELECT paid FROM DATA WHERE player_id='{n}' AND match_id='{matchday_id}'").fetchall()[0][0] == 0:
                    c.execute(f"UPDATE DATA SET payment_id='{db_message}', paid=1 WHERE player_id='{n}' and match_id='{matchday_id}'")

            conn.commit()

            if len(payers) == 0:
                return redirect(url_for('adminmatch', matchday = matchday, message = "Geen veranderingen"))

            new_message = f"Volgende spelers zijn gemakeerd als betaald: \n {' - '.join(payers)}"
            return redirect(url_for('adminmatch', matchday = matchday, message = new_message))

    match_list, participants_data, names = Functions.match_webdeatils(matchday)

    return render_template('adminmatch.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))

# CREATE MATCH ADMIN

@app.route('/admincreatematch', methods=['GET', 'POST'])
def admincreatematch():
    location_list = (Functions.getData("location"))
    if request.method == 'POST':
        password = random.randint(1000,9999)
        date = ''.join(request.form.get('date').split('-'))
        location = request.form.get('location')
        capacity = request.form.get('capacity')
        starttime = request.form.get('starttime')
        endtime = request.form.get('endtime')
        status = "open" if request.form.get('open') == 'on' else "closed"
        price = "0.00"
        note = request.form.get('note')
        
        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()
        
        c.executemany("INSERT INTO MATCHDAYS (date, starttime, endtime, location, max, status, price, password, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [(date, starttime, endtime, location, capacity, status, price, password, note)])
        conn.commit()
        return redirect(url_for('admin'))
    return render_template('admincreatematch.html', list=list(location_list.values()), n_list=len(location_list))

# MATCHES

@app.route('/matches', methods=['GET', 'POST'])
def matches():
    if request.method == 'POST':
        matchday = int(request.form.get('dateBtn'))
        open = [i for i in list(Functions.getData("match").values()) if i[0] == str(matchday)][0]
        print(open)
        if open[5] == "ended":
            return redirect(url_for('payment', matchday = matchday, message = ''))
        else:
            return redirect(url_for('signup', matchday = matchday, message = ''))

    match_list = Functions.getData("match")

    return render_template('matches.html', list=list(match_list.values())[::-1], n_list=len(match_list))

# VOLLEYBALL: PAYMENT PAGE

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    for key, value in request.environ.items():
        print(f"{key}\t\t {value}")
    print(request.environ.get("HTTP_REFERER"))
    matchday = request.args['matchday']
    message = request.args['message']
    
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    if request.method == 'POST':
        not_paid = [j[0] for j in [i for i in list(Functions.getData().values()) if i[5] == 0 and i[1] == matchday]]
        print(not_paid)

        going2pay = list(set([name for name in not_paid if request.form.get(name) == 'on']))
        print(going2pay)
        n_payments = sum([1 if request.form.get(name) else 0 for name in not_paid])
        print(n_payments)

        if n_payments == 0:
            return redirect(url_for('payment', matchday = matchday, message = 'Geen personen geselecteerd')) 

        price = float([i for i in list(Functions.getData("match").values()) if i[0] == matchday][0][6])
        print(price)

        total_price = n_payments * price

        checkout_url = Functions.create_payment(matchday, going2pay, "{:.2f}".format(total_price))
        return redirect(checkout_url)
                
    match_list, participants_data, names = Functions.match_webdeatils(matchday)

    return render_template('payment.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))

# VOLLEYBALL: SIGN UP PAGE

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    matchday = request.args['matchday']
    matchday_id = list(Functions.get_id("match",matchday).keys())[0]
    message = request.args['message']
    
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    if request.method == 'POST':
        matchday_password = [value[-3] for key, value in Functions.getData("match").items() if value[0] == matchday][0]
        print(matchday_password)

        if matchday_password != request.form.get("password"):
            match_list, participants_data, names = Functions.match_webdeatils(matchday)
            message = "Wachtwoord komt niet overeen."
            return render_template('signup.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))
        
        message = ""

        for newParticipant in json.loads(request.form.get("uname")):

            tentative = 1 if newParticipant["tentative"] == True else 0
            newbie = 1 if newParticipant["newbie"] == True else 0
            signupname = newParticipant["name"]
            signup_firstname, signup_lastname = signupname.split()[0], ' '.join(signupname.split()[1:])

            status = Functions.signupcheck(matchday, signupname)

            # NEW PERSON
            if status == "unknown_p":
                if newbie:
                    c.execute("INSERT INTO PLAYER (firstname, lastname) VALUES (?, ?)", (signup_firstname, signup_lastname))
                    conn.commit()
                    message += f"{signupname} toegevoegd aan db. "

                    player_id = list(Functions.get_id("player",signupname).keys())[0]

                    data = [(player_id, matchday_id,newbie,tentative, 'NULL', 0)]
                    c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", data)
                    conn.commit()
                else:
                    message += f"{signupname} niet toegevoegd, geef aan dat {signupname} nieuw is. "
            
            # MATCH LIMIT REACHED
            elif status == "full":
                message += f"{signupname} niet toegevoegd, limiet bereikt. "

            # PERSON ALREADY SIGNED UP
            elif status == "duplicate":
                message += f"{signupname} is al toegevoegd. "

            # PERSON DID NOT PAY
            elif status == "not_paid":
                message += f"{signupname} heeft nog niet betaald. "

            #SUCCESS
            elif status == "allowed":
                message += f"{signupname} toegevoegd! "
                
            
                player_id = list(Functions.get_id("player",signupname).keys())[0]

                data = [(player_id, matchday_id,0,tentative, 'NULL', 0)]
                c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", data)
                conn.commit()
        
        return redirect(url_for('signup', matchday = matchday, message = message))

    match_list, participants_data, names = Functions.match_webdeatils(matchday)

    return render_template('signup.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))

if __name__ == '__main__':
    app.run(host = "0.0.0.0", debug=True)
