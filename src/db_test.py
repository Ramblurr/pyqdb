#!/usr/bin/env python
# -*- coding: utf-8 -*-

import db
from data_models import Quote, Tag

quote = Quote("this is a quote")
quote.tags = [ Tag("foo"), Tag("bar") ]

db = db.SQLQuoteStore()
db.put(quote)
print quote.id

quote2 = db.get(quote.id)

assert quote == quote2
