#!/usr/bin/env python
# -*- coding: utf-8 -*-


import string

# flask includes
from flask import Flask, request, session, g, \
                  redirect, url_for, abort, render_template, \
                  flash, make_response

# local includes
from data_models import Quote, Tag
from jsonify import jsonify
import flask_override
from db import db
from sql import db_session # yuck, we shouldnt dep on this
from basic_auth import FlaskRealmDigestDB
from news import News

# app config 
SECRET_KEY = 'CHANGEME'
DEBUG = True

app = Flask(__name__)
app.request_class = flask_override.Request
app.config.from_object(__name__)

# convenience function
def nav(href, title):
    nav_keys = ('href', 'title')
    return dict(zip(nav_keys, (href, title))) 

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

def add_loc_hdr(rs, loc):
    rs.headers.add( 'Location', loc )

def add_link_hdr(rs, link, rel):
    stub =  '<%s>; rel="%s"' % (link, rel)
    if 'Link' in rs.headers:
        rs.headers['Link'] += ', %s' %(stub) 
    else:
        rs.headers.add( 'Link', stub)

## Routes and Handlers ##
@app.route('/')
def welcome():
    if request.wants_json():
        for nav in navs: nav['rel'] = 'child-resource'
        root = { 'version': '0.1',
                 'title': 'VT Bash',
                 'link': { 'href': '/', 'rel': 'self' },
                 'resources' : [ navs ] }
        return jsonify(root)
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
    if request.wants_json():
        rs = jsonify({'body': "Quote here", 'tags': [], 'link': {'href':'/quotes', 'method':'post', 'rel': 'submit'}})
        add_link_hdr(rs, '/quotes', 'submit')
        return rs
    return render_template('submit.html', nav=navs)

@app.route('/quotes', methods=['POST'])
def create_quote():
    if request.provided_json():
        return create_quote_json()
    else:
        return create_quote_form()

def validate_quote(body, tags):
    body_valid = True
    tags_valid = True
    if len(body) > 10*1024: # 10kb, arbitrary limit
        body_valid = False
    for tag in tags:
        if len(tag) > 15:
            tags_valid = False
            break
    return body_valid, tags_valid

def create_quote_json():
    ip = request.headers['X-Real-Ip']
    data = request.json

    body_valid, tags_valid = validate_quote(data['body'], data['tags'])

    if body_valid and tags_valid:
        quote = Quote(data['body'], ip)
        quote.tags = map(Tag, data['tags'])
        quote = db.put(quote) # grabbing return val isn't strictly necessary

    if request.wants_json():
        return create_quote_resp_json(quote, body_valid, tags_valid)
    else:
        return create_quote_resp_html(quote, body_valid, tags_valid)
     
def create_quote_form():
    ip = request.headers['X-Real-Ip']
    type = request.headers['Content-Type']

    tags = []
    tags_valid = True
    body_valid = True

    content = request.form['quote']
    tags_raw = request.form['tags'] 
    # a smidgen of validation
    if len(tags_raw) > 100:
        tags_valid = False
    else:
        tags = map(string.strip, tags_raw.split(','))
        body_valid, tags_valid = validate_quote(content, tags)

    quote = None
    if body_valid and tags_valid:
        quote = Quote(content, ip)
        quote.tags = map(Tag, tags)
        quote = db.put(quote) # grabbing return val isn't strictly necessary

    if request.wants_json():
        return create_quote_resp_json(quote, body_valid, tags_valid)
    else:
        return create_quote_resp_html(quote, body_valid, tags_valid)

def create_quote_resp_json(quote, body_valid, tags_valid): 
    error = { 'error': 'validation', 'error_msg': '' }
    if not body_valid:
        error['error_msg'] += 'Body too large'
    if not tags_valid:
        error['error_msg'] += 'Tags too large'
    if not body_valid or not tags_valid:
        rs = jsonify(error)
        rs.status_code = 413
        return rs
     
    rs = jsonify(quote)
    add_loc_hdr(rs, '/quotes/%s' % (quote.id))
    rs.status_code = 201
    rs.headers['Content-Type'] = Quote.json_mimetype
    return rs 

def create_quote_resp_html(quote, body_valid, tags_valid): 
    if not body_valid:
        flash('Error: Quote too big', 'error')
    if not tags_valid:
        flash('Error: Tags too big', 'error')

    if body_valid and tags_valid:
        flash('Quote Submitted. Thanks!', 'success')

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
    if request.wants_json():
        rs = jsonify(quotes)
        next_link = '/quotes?start=%s' % (next)
        prev_link = '/quotes?start=%s' % (prev)
        add_link_hdr(rs, next_link, 'next')
        if start > 0:
            add_link_hdr(rs, prev_link, 'prev')
        return rs
    return render_template('quotes.html', nav=navs, quotes=quotes, page='quotes', next=next, prev=prev)

@app.route('/search')
def search():
    incr,start,next,prev = parse_qs(request.args)
    query = request.args.get('query', None)
    json_error = {'error': 'nyi', 'error_msg': 'search not yet implemented'}
    if not query:
        if request.wants_json():
            rs = jsonify(json_error)
            rs.status_code = 501
            return rs
        return render_template('search.html', nav=navs)

    if request.wants_json():
        rs = jsonify(json_error)
        rs.status_code = 501
        return rs
    return render_template('search.html', nav=navs, quotes=db.search(query, incr, start), title="Search Results for '%s'" %(query), next=next, prev=prev, page="search", query=query)


@app.route('/tags')
def tags():
    format = request.args.get('format', 'html')
    if request.wants_json():
        return jsonify( db.tags() )
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
