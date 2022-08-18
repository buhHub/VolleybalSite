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

c.execute("CREATE TABLE IF NOT EXISTS PARTICIPANT ([id] INTEGER PRIMARY KEY,[participant_id] int, [tentative] BIT)")
participants = [i[0] for i in c.execute("SELECT participant_id FROM PARTICIPANT").fetchall()]
testdata = [(2, 0),
    (4, 0),
    (1, 0)
]
c.executemany("INSERT INTO PARTICIPANT (participant_id, tentative) VALUES (?, ?)", [data for data in testdata if not (data[0] in participants)])

c.execute("CREATE TABLE IF NOT EXISTS PLAYER ([id] INTEGER PRIMARY KEY,[firstname] text, [lastname] text, [date] text, [paid] BIT, [payment_id] text)")
players = c.execute("SELECT firstname,lastname FROM PLAYER").fetchall()
testdata = [("Buh", "Khuu", "20220713", 1, "i4yro4ybbc9op"),
    ("Buh", "Khuu", "20220718", 1, 'o982bc3982'),
    ("Buh", "Khuu", "20220721", 0, 'NULL'),
    ("Nick", "Chen", "20220713", 1, "948bvro93"),
    ("Nick", "Chen", "20220718", 1, "lnbc8u3ol"),
    ("Nick", "Chen", "20220721", 0, 'NULL'),
    ("Jennifer", "Fung", "20220721", 0, 'NULL'),
    ("Esli", "Wang", "20220718", 0, 'NULL'),
    ("Almar", "van Diessen", "20220713", 0, 'NULL'),
    ("Jason", "Liu", "20220713", 1, "23lb9cl829843"),
    ("Jason", "Liu", "20220718", 1, "nc982o323c")
]
c.executemany("INSERT INTO PLAYER (firstname, lastname, date, paid, payment_id) VALUES (?, ?, ?, ?, ?)", testdata)
#c.executemany("INSERT INTO PLAYER (firstname, lastname, participations) VALUES (?, ?, ?)", [i for i in testdata if not i[0:2] in players])

c.execute("CREATE TABLE IF NOT EXISTS MATCHDAYS ([id] INTEGER PRIMARY KEY,[date] text, [starttime] text, [endtime] text, [location] text, [max] int, [open] BIT)")
testdata = [("20220713", "20:30", "23:00", "De Vaart", 50, 0),
    ("20220718", "20:30", "23:00", "De Kraal", 35, 0),
    ("20220721", "20:30", "23:00", "De Karekiet", 35, 1)
]
c.executemany("INSERT INTO MATCHDAYS (date, starttime, endtime, location, max, open) VALUES (?, ?, ?, ?, ?, ?)", testdata)

conn.commit()

check = [i[0] for i in c.execute("SELECT participant_id FROM PARTICIPANT").fetchall()]
sql="SELECT firstname, lastname FROM PLAYER WHERE ROWID IN ({seq})".format(seq=','.join(['?']*len(check)))
print(c.execute(sql, check).fetchall())
