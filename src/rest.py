# -*- coding: utf-8 -*-
''' Some helpful rest utils '''

from flask import make_response, request
from jsonify import jsonify

def add_loc_hdr(rs, loc):
    rs.headers.add( 'Location', loc )

def add_link_hdr(rs, link, rel):
    stub =  '<%s>; rel="%s"' % (link, rel)
    if 'Link' in rs.headers:
        rs.headers['Link'] += ', %s' %(stub) 
    else:
        rs.headers.add( 'Link', stub)

def build_link(href, rel, mimetype, **kwargs):
    link = {}
    link['href'] = href
    link['rel'] = rel
    link['mimetype'] = mimetype
    if 'title' in kwargs:
        link['title'] = kwargs['title']
    if 'method' in kwargs:
        link['method'] = kwargs['method']
    return link

def json_nyi():
    json_error = {'error': 'nyi', 'error_msg': 'search not yet implemented'}
    rs = jsonify(json_error, 'application/vnd.pyqdb-error+json')
    rs.status_code = 501
    return rs


