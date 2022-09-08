from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, abort
from flask_login import LoginManager, login_user, login_required, UserMixin, current_user, logout_user
from waitress import serve

import sqlite3
import os.path as path
import datetime
import random
import Functions
import json
import locale

import os
import time

from mollie.api.client import Client
from mollie.api.error import Error
import mollie

def create_app(testing: bool = True):
    app = Flask(__name__)
    app.secret_key = "Made by Buh"
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "adminlogin"
    locale.setlocale(locale.LC_TIME, "nl_NL")

    class User(UserMixin):
        pass

    def logindata():
        return {value[0]: {'password': value[1]} for key, value in list(Functions.getData("login").items()) if value[2] == 1}

    @login_manager.user_loader
    def user_loader(uname):
        unames = logindata()
        if uname not in unames:
            return

        user = User()
        user.id = uname
        return user


    @login_manager.request_loader
    def request_loader(request):
        unames = logindata()
        uname = request.form.get('uname')
        if uname not in unames:
            return

        user = User()
        user.id = uname
        return user


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

        # for key, value in payment.items():
        #     print(f"{key}: ",value)

        print(f"Webhook: \n\t{payment.id} has a new status: {payment.status}.")

        if payment.status == 'paid':
            conn = sqlite3.connect('Volleyball.db')
            c = conn.cursor()

            c.execute(f"UPDATE DATA SET paid=1 WHERE payment_id='{payment.id}'")
            conn.commit()
            print(f"Webhook: \n\t{payment.id} marked as paid in db")


        return 'succes', 200

    # HOMEPAGE

    @app.route('/')
    def index():
        # for key, value in request.environ.items():
        #     print(f"{key}\t\t {value}")
        # return render_template('home.html')
        return redirect(url_for('matches'))

    # ADMIN ADD LOCATION

    @app.route('/addlocation', methods=['GET', 'POST'])
    def addlocation():
        if request.method == 'POST':

            title, details, max = request.form["title"], request.form["address"] + ", " + request.form["zipcode"] + " " + request.form["city"], request.form["capacity"]

            conn = sqlite3.connect('Volleyball.db')
            c = conn.cursor()
            
            c.executemany("INSERT INTO LOCATIONS (name, details, max) VALUES (?, ?, ?)", [(title, details, max)])
            conn.commit()
            print(f"{current_user.id} added {title} as a new location.")
            return redirect(url_for('admincreatematch'))
        return render_template('addlocation.html')

    # ADMIN

    @app.route('/adminregistration', methods=['GET', 'POST'])
    @login_required
    def adminregistration():
        if request.method == "POST":
            uname = request.form.get("uname")
            pw1 = request.form.get("password")
            pw2 = request.form.get("confirmpassword")

            if pw1 != pw2:
                return render_template('adminregistration.html', message = "Wachtwoorden komen niet overeen", uname = uname)

            if uname == "":
                return render_template('adminregistration.html', message = "Geen gebruikersnaam aangegeven", uname = uname)

            if pw1 == "":
                return render_template('adminregistration.html', message = "Geen wachtwoord ingevoerd", uname = uname)

            if pw2 == "":
                return render_template('adminregistration.html', message = "Bevestig je wachtwoord", uname = uname)

            conn = sqlite3.connect('Volleyball.db')
            c = conn.cursor()

            user_id = c.execute(f"SELECT id FROM LOGIN WHERE username='{current_user.id}'").fetchall()[0][0]
            data = [uname, (pw1), user_id]
            c.execute(f"INSERT INTO LOGIN (username, hash, activated) VALUES (?,?,?)", data)
            conn.commit()
            print(f"{uname} has been added as admin by {current_user.id}.")
            return redirect(url_for("admin", message = f"{uname} succesvol toegevoegd door {current_user.id}."))

        message = ""
        uname = ""
        return render_template('adminregistration.html', message = message, uname = uname)

    # ADMIN

    @app.route('/adminlogin', methods=['GET', 'POST'])
    def adminlogin():
        uname = request.args["uname"] if "uname" in request.args else ""
        if request.method == "POST":
            uname = request.form.get("uname")
            unames = logindata()
            if uname in unames and (request.form['password']) == (unames[uname]['password']):
                user = User()
                user.id = uname
                login_user(user)
                return redirect(url_for('admin'))
        return render_template('adminlogin.html', uname = uname)
        
    @app.route('/protected')
    @login_required
    def protected():
        return 'Logged in as: ' + current_user.id

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for("matches"))

    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return redirect(url_for("adminlogin"))

    # ADMIN

    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin():
        message = request.args["message"] if "message" in request.args else ""
        if request.method == 'POST':
            matchday = int(request.form.get('dateBtn'))
            return redirect(url_for('adminmatch', matchday = matchday, message = ''))
        match_list = list(Functions.getData("match").values())
        match_list.sort(key=lambda row: (row[0]))
        match_list = [ i + [datetime.datetime(int(i[0][:4]), int(i[0][4:6]), int(i[0][6:]), 0, 0).strftime("%A, %d %b %Y").title()] for i in match_list]
        return render_template('admin.html', list=match_list[::-1], n_list=len(match_list), message=message)
        
    # ADMIN: MATCH MANAGEMENT

    @app.route('/adminmatch', methods=['GET', 'POST'])
    @login_required
    def adminmatch():
        matchday = request.args['matchday']
        matchday_id = [key for key, value in Functions.getData("match").items() if value[0] == matchday][0]
        message = request.args['message']
        
        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()

        if request.method == 'POST':
            message = ""
            # FORM SUBMIT WHEN DELETE BUTTON PRESS
            if "delete" in request.form:
                c.execute(f"DELETE FROM MATCHDAYS WHERE date='{matchday}'")
                c.execute(f"DELETE FROM DATA WHERE match_id='{matchday_id}'")
                conn.commit()
                print(f"{matchday} has been deleted.")
                return redirect(url_for('admin', message = f"{matchday} verwijderd en alle bijbehorende inschrijvingen."))

            # FORM SUBMIT WHEN DELETE BUTTON PRESS
            if "export" in request.form:
                print(f"{matchday} has been exported.")
                return redirect(url_for('export', matchday=matchday))

            # FORM SUBMIT WHEN SAVE BUTTON PRESS
            if "save" in request.form:
                status = c.execute(f"SELECT status FROM MATCHDAYS WHERE id='{matchday_id}'").fetchall()[0][0]
                new_status = request.form.get("save")
                note = request.form.get("note")

                price = "{:.2f}".format(float(request.form.get("price")))
                    
                if new_status == "ended" and price == "0.00":
                    return redirect(url_for('adminmatch', matchday = matchday, message = "Prijs kan geen 0 zijn."))

                c.execute(f"UPDATE MATCHDAYS SET price='{price}' WHERE id='{matchday_id}'") 
                c.execute(f"UPDATE MATCHDAYS SET note='{note}' WHERE id='{matchday_id}'") 
                conn.commit()
                print(f"{matchday} has been set to {new_status if new_status != None else status}, with price: {price} and note: {note}.")

                if status != new_status and new_status != None:
                    c.execute(f"UPDATE MATCHDAYS SET status='{new_status}' WHERE id='{matchday_id}'")
                    conn.commit()                    
                return redirect(url_for('adminmatch', matchday = matchday, message = "Status en prijs geupdate"))

            # FORM SUBMIT WHEN SUBMIT BUTTON PRESS
            status = c.execute(f"SELECT status FROM MATCHDAYS WHERE id='{matchday_id}'").fetchall()[0][0]
            if status == "open":
                if "unsubscribe" in request.form:
                    participants = [j[0] for j in [i for i in list(Functions.getData().values()) if i[1] == matchday]]
                    unsubscribers = list(set([name for name in participants if request.form.get(name) == 'on']))
                    unsubscribers_ids = [key for key, value in Functions.getData("player").items() if value in unsubscribers]
                    matchday_id = c.execute(f"SELECT id FROM MATCHDAYS WHERE date='{matchday}'").fetchall()[0][0]

                    for n in unsubscribers_ids:
                        c.execute(f"DELETE FROM DATA WHERE player_id='{n}' AND match_id='{matchday_id}'")

                    conn.commit()

                    new_message = f"Volgende spelers zijn verwijderd van de lijst: \n {' - '.join(unsubscribers)}"

                    terminal_message = '\n' + '\n'.join(unsubscribers)
                    print(f"Following players have been removed from {matchday} by {current_user.id}: {terminal_message}")
                    return redirect(url_for('adminmatch', matchday = matchday, message = new_message))
                if "uname" in request.form:
                    if request.form.get("uname") != "":
                        signupname = request.form["uname"]
                        signup_firstname, signup_lastname = request.form["uname"].split()[0], ' '.join(request.form["uname"].split()[1:])
                        newbie = 0

                        status = Functions.signupcheck(matchday, signupname)
                        if status == "unknown_p":
                            c.execute("INSERT INTO PLAYER (firstname, lastname) VALUES (?, ?)", (signup_firstname, signup_lastname))
                            conn.commit()
                            newbie = 1
                            print(f"{signupname} has been added to the db by {current_user.id}")
                            pass
                        elif status == "full":
                            print(f"{signupname} has been signed up to {matchday} by {current_user.id}, but it is full.")
                            return redirect(url_for('adminmatch', matchday = matchday, message = "Limiet bereikt."))
                        elif status == "duplicate":
                            print(f"{signupname} has been signed up to {matchday} by {current_user.id}, but {signupname} is already signed up.")
                            return redirect(url_for('adminmatch', matchday = matchday, message = f"{signupname} staat al ingeschreven."))
                        elif status == "not_paid":
                            print(f"{signupname} has been signed up to {matchday} by {current_user.id}, but did not fulfill all previous events.")
                            return redirect(url_for('adminmatch', matchday = matchday, message = f"Vorige betalingen van {signupname} zijn nog niet voldaan."))
                        elif status == "allowed":
                            pass

                        player_id = list(Functions.get_id("player",signupname).keys())[0]
                        data = [(player_id, matchday_id,newbie,0, 'NULL', 0)]
                        c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", data)
                        conn.commit()
                        print(f"{signupname} has succesfully signed up to {matchday} by {current_user.id}.")
                        message = f"{signupname} is toegevoegd!"

            elif status == "ended": 
                print(request.form)
                participants = [j[0] for j in [i for i in list(Functions.getData().values()) if i[1] == matchday]]
                payers = list(set([name for name in participants if request.form.get(name) == 'on']))
                payers_ids = [key for key, value in Functions.getData("player").items() if value in payers]
                matchday_id = c.execute(f"SELECT id FROM MATCHDAYS WHERE date='{matchday}'").fetchall()[0][0]

                ip = request.environ.get("REMOTE_ADDR")
                dt = datetime.datetime.now().strftime("%Y%m%d %H%M%S")
                db_message = f"Manually modified on {ip} at {dt}"

                terminal_message = '\n'.join([f'{payers[i]} + {payers_ids[i]}' for i in range(len(payers))])
                print(f"{current_user.id} wants to mark [{terminal_message}] on {matchday} as paid.")

                for n in payers_ids:
                    if c.execute(f"SELECT paid FROM DATA WHERE player_id='{n}' AND match_id='{matchday_id}'").fetchall()[0][0] == 0:
                        print(f"{n} has succesfully marked {matchday} as paid by {current_user.id}.")
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
    @login_required
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
            print(f"A new event has been added: {date}.")
            return redirect(url_for('admin', message = f"{date} is toegevoegd!"))
        return render_template('admincreatematch.html', list=list(location_list.values()), n_list=len(location_list))

    # EXPORT NAMELIST

    @app.route('/export', methods=['GET', 'POST'])
    @login_required
    def export():
        matchday = request.args["matchday"]
        data = [f"{i[0]}{', Nieuw' if i[2] else ''}{', Onder Voorbehoude' if i[3] else ''}" for i in Functions.getData().values() if i[1] == matchday]
        data.sort()
        return render_template('export.html',data=data)

    # MATCHES

    @app.route('/matches', methods=['GET', 'POST'])
    def matches():
        message = request.args["message"] if "message" in request.args else ""
        logged_in = current_user.is_authenticated
        if request.method == 'POST':
            matchday = int(request.form.get('dateBtn'))
            if logged_in:
                return redirect(url_for('adminmatch', matchday = matchday, message = ''))
            else:
                open = [i for i in list(Functions.getData("match").values()) if i[0] == str(matchday)][0]
                if open[5] == "ended":
                    return redirect(url_for('payment', matchday = matchday, message = ''))
                else:
                    return redirect(url_for('signup', matchday = matchday, message = ''))

        match_list = list(Functions.getData("match").values())
        match_list.sort(key=lambda row: (row[0]))

        match_list = [ i + [datetime.datetime(int(i[0][:4]), int(i[0][4:6]), int(i[0][6:]), 0, 0).strftime("%A, %d %b %Y").title()] for i in match_list]

        return render_template('matches.html', list=match_list[::-1], n_list=len(match_list), message=message, logged_in = logged_in)

    # VOLLEYBALL: PAYMENT PAGE

    @app.route('/payment', methods=['GET', 'POST'])
    def payment():
        matchday = request.args['matchday']
        message = request.args['message']
        
        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()

        if request.method == 'POST':
            not_paid = [j[0] for j in [i for i in list(Functions.getData().values()) if i[5] == 0 and i[1] == matchday]]

            going2pay = list(set([name for name in not_paid if request.form.get(name) == 'on']))
            n_payments = sum([1 if request.form.get(name) else 0 for name in not_paid])

            if n_payments == 0:
                return redirect(url_for('payment', matchday = matchday, message = 'Geen personen geselecteerd')) 

            price = float([i for i in list(Functions.getData("match").values()) if i[0] == matchday][0][6])

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
        message = [request.args['message']]
        
        conn = sqlite3.connect('Volleyball.db')
        c = conn.cursor()

        if request.method == 'POST':
            matchday_password = [value[-3] for key, value in Functions.getData("match").items() if value[0] == matchday][0]

            if matchday_password != request.form.get("password"):
                match_list, participants_data, names = Functions.match_webdeatils(matchday)
                new_message = ["Wachtwoord komt niet overeen."]
                print(f"Someone tried to sign up for {matchday}, but got the password wrong. \n\tPW: {matchday_password}, Actual: {request.form.get('password')}.")
                return render_template('signup.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = new_message, names = names, n_names = len(names))
            
            message = []

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
                        message.append(f"{signupname} toegevoegd aan db. ")

                        player_id = list(Functions.get_id("player",signupname).keys())[0]

                        data = [(player_id, matchday_id,newbie,tentative, 'NULL', 0)]
                        c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", data)
                        conn.commit()

                        print(f"{signupname} added to db and signed up for {matchday}.")
                    else:
                        print(f"{signupname} is an unknown person, and did not flag [New].")
                        message.append(f"{signupname} niet toegevoegd, geef aan dat {signupname} nieuw is. ")
                
                # MATCH LIMIT REACHED
                elif status == "full":
                    print(f"{signupname} tried to sign up for {matchday}, but its full.")
                    message.append(f"{signupname} niet toegevoegd, limiet bereikt. ")

                # PERSON ALREADY SIGNED UP
                elif status == "duplicate":
                    print(f"{signupname} tried to sign up for {matchday}, but {signupname} is already signed up.")
                    message.append(f"{signupname} is al toegevoegd. ")

                # PERSON DID NOT PAY
                elif status == "not_paid":
                    print(f"{signupname} tried to sign up for {matchday}, but did not pay for previous events.")
                    message.append(f"{signupname} heeft nog niet betaald. ")

                #SUCCESS
                elif status == "allowed":
                    message.append(f"{signupname} toegevoegd! ")
                    
                
                    player_id = list(Functions.get_id("player",signupname).keys())[0]

                    data = [(player_id, matchday_id,0,tentative, 'NULL', 0)]
                    c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", data)
                    conn.commit()
                    print(f"{signupname} signed up {matchday}.")

        match_list, participants_data, names = Functions.match_webdeatils(matchday)

        return render_template('signup.html', match_list = match_list, participants_data = participants_data, n_players = len(participants_data), message = message, names = names, n_names = len(names))
    return app

serve(create_app(testing=False), listen='*:5000')
# if __name__ == '__main__':
#     app.run(host = "0.0.0.0", debug=True)
