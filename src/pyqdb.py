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
    nav('/tags', 'Tags'),
    nav('/search', 'Search'),
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

def parse_qs(args, tag = None):
    incr = 15
    start = args.get('start', 0, type=int)
    if tag:
        count = db.tag_count(tag)
    else:
        count = db.count()
    next = min(start+incr, count)
    prev = max(start-incr, 0)
    return (15, start, next, prev )


@app.route('/quotes')
def latest():
    incr,start,next,prev = parse_qs(request.args)
    quotes = db.latest(incr, start)
    
    return render_template('quotes.html', nav=navs, quotes=quotes, page='quotes', next=next, prev=prev)

@app.route('/search')
def search():
    incr,start,next,prev = parse_qs(request.args)
    query = request.args.get('query', None)
    if not query:
        return render_template('search.html', nav=navs)

    return render_template('search.html', nav=navs, quotes=db.search(query, incr, start), title="Search Results for '%s'" %(query), next=next, prev=prev, page="search", query=query)



@app.route('/tags')
def tags():
    format = request.args.get('format', 'html')
    if format == 'json':
        return json.dumps( db.tags() )
    return render_template('tags.html', nav=navs)

@app.route('/tags/<string:tag>')
def tag(tag):
    incr,start,next,prev = parse_qs(request.args, tag)
    quotes = db.tag(tag, incr, start)
    page = 'tags/%s' % (tag)
    return render_template('quotes.html', nav=navs, quotes=quotes, page=page, next=next, prev=prev, title="Quotes Tagged '%s'" %(tag))

@app.route('/top')
def top():
    incr,start,next,prev = parse_qs(request.args)
    return render_template('quotes.html', nav=navs, quotes=db.top(incr, start), page='top', next=next, prev=prev)

@app.route('/random')
def random():
    return render_template('quotes.html', nav=navs, quotes=db.random(15))

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
