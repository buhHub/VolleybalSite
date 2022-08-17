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

@app.route('/matches')
def matches():
    conn = sqlite3.connect('Volleyball.db')
    c = conn.cursor()
    match_list = c.execute("SELECT * FROM MATCHDAYS").fetchall()
    #print(match_list)
    #return render_template('matches.html')
    return render_template('matches.html', list=match_list, n_list=len(match_list))

# THIS CAN BE DELETED, ITS OVERWRITED BY THE RESULTS PAGE

@app.route('/paperwork', methods=['GET', 'POST'])
def paperwork():
    if request.method == 'POST':

        #        print("paperwork posted")
        FormNames = ["A", "B", "C", "D", "E", "F"]
        RefList = [request.form.get(
            FormName) for FormName in FormNames if request.form.get(FormName)]

        DataList = requestdata(RefList)
        return redirect(url_for('results', data=[RefList], len_list=10, location="CZM"))

    print("paperwork getted")
    return render_template('paperwork.html')

# VOLLEYBALL: SIGN UP PAGE

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    #if request.method == 'POST':

     #   pass
      #  return redirect(url_for('signup'))

    return render_template('signup.html')

if __name__ == '__main__':
    app.run(host = "0.0.0.0", debug=True)
