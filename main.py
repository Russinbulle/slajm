import datetime
import json

import requests
from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
import os

from requests import RequestException
from sqlalchemy import UniqueConstraint

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
db = SQLAlchemy(app)

wbm_base_url = 'http://web.archive.org/cdx/search/cdx?url='
wbm_params = '/*&output=json&limit=99999999'


def get_wbm_data_for_url(url):
    try:
        url = url.strip().lower()
        r = requests.get(f'{wbm_base_url}{url}{wbm_params}')
        return r.json()
    except RequestException as e:
        return None


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    body = db.Column(db.Text)


class WebArchiveEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    urlkey = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    original = db.Column(db.Text)
    mimetype = db.Column(db.String(250))
    statuscode = db.Column(db.Text)
    digest = db.Column(db.String(250))
    length = db.Column(db.Text)

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/notes/create", methods=["GET", "POST"])
def create_note():
    if request.method == "GET":
        return render_template("create_note.html")
    else:
        title = request.form["title"]
        body = request.form["body"]

        note = Note(title=title, body=body)
        db.session.add(note)
        db.session.commit()
        return redirect("/notes/create")


@app.route("/wbm/fetch", methods=["GET", "POST"])
def fetch_url():
    if request.method == "GET":
        return render_template("fetch_wbm.html")
    else:
        raw_url = request.form["url"]
        json_response = get_wbm_data_for_url(url=raw_url)
        wbm_rows = []
        if json_response:
            json_response.pop(0)
            for entry in json_response:
                wbm_entry = WebArchiveEntry(
                    urlkey = entry[0],
                    timestamp=datetime.datetime.strptime(entry[1], "%Y%m%d%H%M%S"),
                    original=entry[2],
                    mimetype=entry[3],
                    statuscode=entry[4],
                    digest=entry[5],
                    length=entry[6],
                )
                exists = db.session.query(WebArchiveEntry.query.filter(
                        WebArchiveEntry.digest == wbm_entry.digest,
                        WebArchiveEntry.timestamp == wbm_entry.timestamp,
                        WebArchiveEntry.original == wbm_entry.original,
                ).exists()).scalar()
                if not exists:
                    db.session.add(wbm_entry)
                wbm_rows.append(wbm_entry)
            db.session.commit()

        # note = Note(title=title, body=body)
        # db.session.add(note)
        # db.session.commit()
        return redirect("/wbm/fetch")


if __name__ == "__main__":
    app.run(debug=True)
