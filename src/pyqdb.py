#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import string

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from data_models import Quote, Tag, QuoteEncoder
from sql import db_session # yuck, we shouldnt dep on this
from db import db

app = Flask(__name__)

def nav(url, name):
    return {'url': url, 'name': name}

navs = [
    nav('/top', 'Top'),
    nav('/quotes', 'Browse'),
    nav('/random', 'Random'),
    nav('/quotes/submit', 'Submit')
]


@app.route('/')
def welcome():
    return render_template('index.html', nav=navs)

@app.route('/quotes/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        quote = Quote(request.form['quote'])
        quote.tags = map(Tag, map(string.strip, request.form['tags'].split(',')))
        db.put(quote)

        title = "Quote Submitted"
        msg = "Thank you for submitting a quote to our database. An administrator will review it shortly. If it gets approved, it will appear soon. Fingers crossed!"
        return render_template('message.html', nav=navs, msg=msg, title=title)
    else:
        return render_template('submit.html', nav=navs)

@app.route('/quotes')
def latest():
    incr = 15
    start = request.args.get('start', 0, type=int)
    next = min(start+incr, db.count())
    prev = max(start-incr, 0)
    return render_template('quotes.html', nav=navs, quotes=db.latest(incr, start), next=next, prev=prev)

@app.route('/quotes/<int:quote_id>')
def single(quote_id):
    quotes = [ db.get(quote_id) ]
    return render_template('quotes.html', nav=navs, quotes=quotes)



@app.route('/quotes/<int:quote_id>/votes', methods=['GET', 'PUT'])
def votes(quote_id):
    ip = request.headers['X-Real-Ip']
    quote = db.get(quote_id)
    if request.method == 'GET':
        return quote.votes_json()
    elif request.method == 'PUT':
        type = request.form['type']
        if type == "up":
            return json.dumps(db.up_vote(quote_id, ip), cls=QuoteEncoder)
        elif type == "down":
            return json.dumps(db.down_vote(quote_id, ip), cls=QuoteEncoder)

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    app.debug = True
    app.run(port=8080)
