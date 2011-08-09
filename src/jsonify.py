# -*- coding: utf-8 -*-

try:
    import json
except ImportError:
    import simplejson as json

import datetime

from flask import Response
from data_models import Quote, Tag

class QuoteEncoder(json.JSONEncoder):
    ''' a custom JSON encoder for Quote objects '''
    def default(self, q):
        if isinstance(q, Quote):
            return { 'mimetype': Quote.mimetype+'+json', 
                     'id': q.id,
                     'up': q.up_votes,
                     'down': q.down_votes,
                     'body': q.body, 
                     'tags': q.tags, 
                     'links': [
                                { 'rel': 'self', 'href': '/quotes/%s' %(q.id) },
                                { 'rel': 'vote', 'href': '/quotes/%s/votes' %(q.id) },
                         #{ 'rel': 'report', 'href': '/quotes/%s/votes' %(q.id) },
                              ],
                     'created': q.created }
        elif isinstance(q, Tag):
            return { 'id': q.id,
                     'tag': q.tag,
                     'links': [ { 'rel': 'self', 'href': '/quotes/tags/%s' % (q.tag) } ] }
        elif isinstance(q, (datetime.datetime, datetime.date)):
            return q.ctime()
        else:
            return json.JSONEncoder.default(self, q)
 
class QuoteDecoder(json.JSONDecoder):
    ''' Custom decoder class. Can throw TypeErrors '''
    def default(self, json_obj):
        if json_obj['mimetype'] == Quote.json_mimetype:
            q = Quote()
            q.id = int(json_obj['id'])
            q.up_votes = int(json_obj['up'])
            q.down_votes = int(json_obj['down'])
            q.body = json_obj['body']
            q.tags = [QuoteDecoder.default(self, t) for t in json_obj['tags']]
            return q
        elif json_obj['mimetype'] == Tag.json_mimetype:
            t = Tag()
            t.id = int(json_obj['id'])
            t.tag = json_obj['tag']
            return tag
        else:
            return json.JSONDecoder.default(self, json_obj)

def jsonify(data):
    return Response(json.dumps(data, cls=QuoteEncoder), mimetype="application/json")
