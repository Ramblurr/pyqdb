# -*- coding: utf-8 -*-

from flask import Flask, Request, json, abort
from werkzeug import cached_property

from jsonify import QuoteDecoder
from data_models import Quote,Tag


json_mimetypes = [ 'application/json',
                   Quote.json_mimetype,
                   Tag.json_mimetype ]

class Request(Request):
    @cached_property
    def json(self):
        if self.mimetype in json_mimetypes:
            request_charset = self.mimetype_params.get('charset')
            try:
                if request_charset is not None:
                    return json.loads(self.data, encoding=request_charset, cls=QuoteDecoder)
                return json.loads(self.data, cls=QuoteDecoder)
            except ValueError:
                abort(400)
    # snippet from http://flask.pocoo.org/snippets/45/
    def wants_json(self):
        mimes = json_mimetypes
        mimes.append( 'text/html' )
        best = self.accept_mimetypes.best_match(mimes)
        return best in json_mimetypes and self.accept_mimetypes[best] > self.accept_mimetypes['text/html']
    
    def provided_json(self):
        print self.mimetype
        return self.mimetype in json_mimetypes

