#!/usr/bin/env python
# -*- coding: utf-8 -*-


from jsonify import jsonify
import string

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response
from data_models import Quote, Tag, QuoteEncoder
from sql import db_session # yuck, we shouldnt dep on this
from db import db
from basic_auth import FlaskRealmDigestDB
from news import News

SECRET_KEY = 'CHANGEME'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

# convenience function
def nav(url, name):
    nav_keys = ('url', 'name')
    return dict(zip(nav_keys, (url, name))) 

navs = [
    nav('/top', 'Top'),
    nav('/quotes', 'Browse'),
    nav('/random', 'Random'),
    nav('/tags', 'Tags'),
    nav('/search', 'Search'),
    nav('/quotes/new', 'Submit')
]

authDB = FlaskRealmDigestDB('MyAuthRealm')
authDB.add_user('admin', 'test')

# snippet from http://flask.pocoo.org/snippets/45/
def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

def add_loc_hdr(rs, loc):
    rs.headers.add( 'Location', loc )

def add_link_hdr(rs, link, rel):
    rs.headers.add( 'Link', '<%s>; rel="%s"' % (link, rel) )

## Routes and Handlers ##
@app.route('/')
def welcome():
    news = News()
    return render_template('index.html', nav=navs, news=news.news)

@app.route('/admin')
@authDB.requires_auth
def admin():
    session['user'] = request.authorization.username
    return "Yup.\n Hello, %s" % (session['user'])

@app.route('/auth')
def authApi():
    if not authDB.isAuthenticated(request):
        return authDB.challenge()
    return redirect('/')

@app.route('/quotes/new', methods=['GET'])
def new_quote():
    if request_wants_json():
        rs = make_response(jsonify({'body': "Quote here", 'tags': []}))
        add_link_hdr(rs, '/quotes', 'post')
        return rs
    return render_template('submit.html', nav=navs)

@app.route('/quotes', methods=['POST'])
def create_quote():
    ip = request.headers['X-Real-Ip']
    content = request.form['quote']
    tags_raw = request.form['tags'] 
    tags = []
    error = False
    # a smidgen of validation
    if len(tags_raw) > 100:
        flash('Error: Tags too big', 'error')
        error = True
    else:
        tags = map(string.strip, tags_raw.split(','))

    if len(content) > 10*1024: # 10kb, arbitrary limit
        flash('Error: Quote too big', 'error')
        error = True

    quote = None
    if not error:
        quote = Quote(content, ip)
        quote.tags = map(Tag, tags)
        quote = db.put(quote) # grabbing return val isn't strictly necessary
        flash('Quote Submited. Thanks!', 'success')

    if request_wants_json():
        rs = make_response(jsonify(quote))
        add_loc_hdr(rs, '/quotes/%s' % (quote.id))
        rs.status_code = 201
        return rs 
        
    return render_template('message.html', nav=navs)

# convenience function to parse the querystring 
def parse_qs(args, tag = None):
    incr = 15
    start = args.get('start', 0, type=int)
    if tag:
        count = db.tag_count(tag)
    else:
        count = db.count()
    next = min(start+incr, count)
    prev = max(start-incr, 0)
    return (incr, start, next, prev )


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
    app.run(port=8080)
