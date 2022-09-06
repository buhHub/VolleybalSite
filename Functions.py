from xml.sax import default_parser_list
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, abort
import sqlite3
import datetime

from mollie.api.client import Client
from mollie.api.error import Error
import mollie

def getData(mode="all"):
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    match_list = {i[0]: list(i[1:]) for i in c.execute("SELECT * FROM MATCHDAYS").fetchall()}
    player_list = {i[0]:' '.join(i[1:]) for i in c.execute("SELECT * FROM PLAYER").fetchall()}
    data_list = {i[0]: list(i[1:]) for i in c.execute("SELECT * FROM DATA").fetchall()}
    location_list = {i[0]: list(i[1:]) for i in c.execute("SELECT * FROM LOCATIONS").fetchall()}
    login_list = {i[0]: list(i[1:]) for i in c.execute("SELECT * FROM LOGIN").fetchall()}

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
    elif mode == "location":
        return location_list
    elif mode == "login":
        return login_list
    elif mode == "all":
        return data_list
    else:
        print("Empty")
        return 0

def create_payment(matchday, names, price):

    api_key = "test_k9tafBmqUy3ATSVUVywAjGqtAqhVR7"
    mollie_client = Client()
    mollie_client.set_api_key(api_key)

    my_webshop_id = "test"
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

        #  ONLY DO THIS WHEN IT GENUINLY SAYS 0 AT PAID
        c.execute(f"UPDATE DATA SET payment_id='{payment.id}' WHERE player_id='{player_id}' AND match_id='{match_id}'")
    conn.commit()

    return payment.checkout_url

def signupcheck(matchday, signupname):
    # Existence Check
    search_list = [(key, value) for key, value in getData("player").items() if value == signupname]
    if len(search_list) == 0:
        return "unknown_p"

    # Capacity Check
    max_limit = [i for i in list(getData("match").values()) if i[0]==matchday][0][4]
    n_participants = len([i for i in list(getData().values()) if i[1] == matchday])
    if n_participants >= max_limit:
        return "full"

    # Duplicate Check
    participants = [i for i in list(getData().values()) if i[1] == matchday]
    for i in participants:
        if i[0] == signupname:
            return "duplicate"
    
    # Payment Check
    player_history = [i for i in list(getData().values()) if i[0] == signupname]
    payment_history = [0 if i[4] == 'NULL' else 1 for i in player_history]

    if sum(payment_history) != len(payment_history):
        return "not_paid"

    return "allowed"

def get_id(mode, search):
    if mode == "match":
        ids = {key: value for key, value in getData(mode).items() if value[0] == search or value[0] in search}
    elif mode == "player":
        ids = {key: value for key, value in getData(mode).items() if value == search or value in search}
    else:
        ids = dict()
    return ids

def match_webdeatils(matchday):
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()

    match_list = [[key] + value for key, value in getData("match").items() if value[0] == matchday][0]
    match_list.append(c.execute(f"SELECT details FROM LOCATIONS WHERE name='{match_list[4]}'").fetchall()[0][0])
    i=match_list[1]
    match_list.append(datetime.datetime(int(i[:4]), int(i[4:6]), int(i[6:]), 0, 0).strftime("%A, %d %b %Y").title())
    print(match_list)

    participants_data = [i for i in list(getData().values()) if i[1]==matchday]
    participants_data.sort(key=lambda row: (row[0]))

    participant_names = [i[0] for i in participants_data]
    all_names = set(getData("player").values())

    names = list(all_names.difference(set(participant_names)))
    names.sort()

    return match_list, participants_data, names