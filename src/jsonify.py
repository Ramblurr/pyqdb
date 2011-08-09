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
            return { 'id': q.id,
                     'up': q.up_votes,
                     'down': q.down_votes,
                     'body': q.body, 
                     'tags': q.tags, 
                     'link': { 'rel': 'self', 'href': '/quotes/%s' %(q.id) }, # what if the url changes?
                     'created': q.created }
        elif isinstance(q, Tag):
            return { 'id': q.id,
                     'tag': q.tag,
                     'link': { 'rel': 'tag', 'href': '/quotes/tags/%s' % (q.tag) } }
        elif isinstance(q, (datetime.datetime, datetime.date)):
            return q.ctime()
        else:
            return json.JSONEncoder.default(self, q)
 
def jsonify(data):
    return Response(json.dumps(data, cls=QuoteEncoder), mimetype="application/json")
