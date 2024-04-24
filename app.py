from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spiel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SECRET_KEY'] = '17a425694393bf20fd346a4ee779966ee1b76bcd'

menu = [{"title": "Neue spielen", "url": "neu"},
        {"title": "Weiter spielen", "url": "weiter"},
        {"title": "Spieler anzeigen", "url": "spieler"}]

db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)


class Games(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    richtig = db.Column(db.Integer, default=0)
    falsch = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    sitting_id = db.Column(db.Integer, db.ForeignKey('sittings.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Sittings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    addition = db.Column(db.Integer)
    subtraktion = db.Column(db.Integer)


@app.route("/")
def index():
    return render_template("index.html", menu=menu, title="Mathe spielen")


@app.route("/neu", methods=["POST", "GET"])
def neu():
    if request.method == 'POST':
        if request.form['psw'] == request.form['psw2']:
            u = Users(name=request.form['name'], psw=request.form['psw'])
            try:
                db.session.add(u)
                db.session.commit()
                session['User'] = u.id
                return redirect(url_for('sittings'))
            except Exception as e:
                print(e)
                flash("Fehler bei Datenbankeinsatz", "error")
        else:
            flash("Passwords übereinstimmen nicht")

    return render_template('neu.html', title="Neu speilen")


@app.route("/sittings", methods=["POST", "GET"])
def sittings():
    if request.method == 'POST':
        try:
            s = Sittings(addition=request.form['add'], subtraktion=request.form['sub'])
            db.session.add(s)
            db.session.flush()

            g = Games(sitting_id=s.id, user_id=session['User'])
            db.session.add(g)
            db.session.commit()

            session['Game'] = g.id
            session['Sitting'] = s.id

            return redirect(url_for('spiel'))
        except Exception as e:
            db.session.rollback()
            print("Fehler bei Dateneinsatz " + str(e))

    return render_template('sittings.html', title="Einstellungen")


@app.route("/spieler", methods=["POST", "GET"])
def spieler():
    if request.method == 'POST':

        user_name = request.form['name']
        u = Users.query.filter_by(name=user_name).first()
        print(u)
        if u:
            if u.psw == request.form['psw']:
                session['User'] = u.id
                return redirect(url_for('spieler_anzeigen'))
            else:
                flash("Password ist falsch", "error")

        else:
            flash("Es gibt kein User mit solchem Namen", "error")

    return render_template('weiter2.html', title="Spieler anzeigen")


@app.route("/spieler_anzeigen", methods=["POST", "GET"])
def spieler_anzeigen():
    
    u = Users.query.get(session['User'])
    games = Games.query.filter_by(user_id=u.id).all()

    return render_template('spieler_anzeigen.html', spieler=u, games=games, title="Spieler")
 

@app.route("/spiel", methods=["POST", "GET"])
def spiel():
    if request.method == 'POST':
        try:
            ergebnis = session['x'] + session['y'] if session['zeichen'] == 1 else session['x'] - session['y']
            ergebnis_spieler = int(request.form['ergebnis'])

            game_id = session.get('Game')
            print("game_id:", game_id)

            game = Games.query.get(game_id)
            print("game:", game)

            if ergebnis == ergebnis_spieler:
                game.richtig += 1
                flash("Richtig", "success")

            else:
                game.falsch += 1
                flash("Falsch. {ergebnis} ist richtig", "error")

            db.session.commit()
            redirect(url_for('spiel'))
            
        except Exception as e:
            db.session.rollback()
            print("Fehler bei Dateneinsatz " + str(e)) 

    s_id = session.get('Sitting')
    print(s_id)

    s = Sittings.query.get(s_id)
    print(s)
    
    session['zeichen'] = random.randint(0, 1)

    if session['zeichen'] == 1:
        session['x'] = random.randint(1, s.addition)
        session['y'] = random.randint(1, s.addition)
    else:
        session['x'] = random.randint(1, s.subtraktion)
        session['y'] = random.randint(1, s.subtraktion)
        if session['x'] < session['y']:
            session['x'], session['y'] = session['y'], session['x']

    return render_template('spiel.html', title="Rechnen", x=session['x'], y=session['y'], char='+' if session['zeichen'] == 1 else '-')


@app.route("/weiter", methods=["POST", "GET"])
def weiter():
    if request.method == 'POST':

        user_name = request.form['name']
        u = Users.query.filter_by(name=user_name).first()
        print(u)
        if u:
            if u.psw == request.form['psw']:
                session['User'] = u.id
                return redirect(url_for('sittings'))
            else:
                flash("Password ist falsch", "error")

        else:
            flash("Es gibt kein User mit solchem Namen", "error")

    return render_template('weiter.html', title="Weiter spielen")


if __name__ == "__main__":
    app.run(debug=True)