import sqlite3
import os.path as path

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except ValueError as e:
        print(e)

    return conn

conn = sqlite3.connect('Volleyball.db')
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS DATA ([id] INTEGER PRIMARY KEY,[player_id] int, [match_id] int, [new_player] BIT, [tentative] BIT, [payment_id] text, [paid] BIT)")
players = c.execute("SELECT player_id FROM DATA").fetchall()
testdata = [(1, 1, 0, 0, "i4yro4ybbc9op", 1),
    (1, 2, 0, 0, 'o982bc3982', 1),
    (1, 3, 0, 0, 'NULL', 0),
    (2, 1, 0, 0, "948bvro93", 1),
    (2, 2, 0, 0, "lnbc8u3ol", 1),
    (2, 3, 0, 0, 'NULL', 0),
    (5, 3, 0, 0, 'NULL', 0),
    (3, 2, 0, 0, 'NULL', 0),
    (8, 1, 0, 1, 'NULL', 0),
    (4, 2, 0, 0, 'NULL', 0),
    (5, 1, 0, 1, 'NULL', 0),
    (6, 2, 0, 0, 'NULL', 0),
    (7, 1, 0, 1, 'NULL', 0),
    (8, 2, 0, 0, 'NULL', 0),
    (9, 1, 0, 1, 'NULL', 0),
    (10, 2, 0, 0, 'NULL', 0),
    (8, 1, 0, 1, 'NULL', 0),
    (6, 1, 0, 0, "23lb9cl829843", 1),
    (6, 2, 0, 0, "nc982o323c", 1)
]
c.executemany("INSERT INTO DATA (player_id, match_id, new_player, tentative, payment_id, paid) VALUES (?, ?, ?, ?, ?, ?)", testdata)

c.execute("CREATE TABLE IF NOT EXISTS PLAYER ([id] INTEGER PRIMARY KEY,[firstname] text, [lastname] text)")
testdata = [("Buh", "Khuu"),
    ("Nick", "Chen"),
    ("Esli", "Wang"),
    ("Calvin", "Fung"),
    ("Jennifer", "Fung"),
    ("Jason", "Liu"),
    ("Melissa", "Fung"),
    ("Steven", "Wan"),
    ("Marvin", "Wan"),
    ("Andy", "Yang"),
    ("Janny", "Lam"),
    ("Jesse", "Chim"),
    ("Misaki", "Saraya"),
    ("Saphira", "Chin"),
    ("Almar", "van Diessen")
]
c.executemany("INSERT INTO PLAYER (firstname, lastname) VALUES (?, ?)", testdata)
#c.executemany("INSERT INTO PLAYER (firstname, lastname, participations) VALUES (?, ?, ?)", [i for i in testdata if not i[0:2] in players])

c.execute("CREATE TABLE IF NOT EXISTS MATCHDAYS ([id] INTEGER PRIMARY KEY,[date] text, [starttime] text, [endtime] text, [location] text, [max] int, [open] BIT, [price] text)")
testdata = [("20220713", "20:30", "23:00", "De Vaart", 50, 0, "4.50"),
    ("20220718", "20:30", "23:00", "De Kraal", 35, 0, "3.50"),
    ("20220721", "20:30", "23:00", "De Karekiet", 35, 1, "0.00")
]
c.executemany("INSERT INTO MATCHDAYS (date, starttime, endtime, location, max, open, price) VALUES (?, ?, ?, ?, ?, ?, ?)", testdata)

conn.commit()
