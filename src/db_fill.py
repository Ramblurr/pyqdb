#!/usr/bin/env python
# -*- coding: utf-8 -*-

import db
from data_models import Quote, Tag

db = db.SQLQuoteStore()
for i in range(100):
    quote = Quote("this is a quote %s" % (i))
    quote.tags = [ Tag("foo"), Tag("bar") ]

    db.put(quote)
