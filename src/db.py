import datetime

from data_models import Quote,Tag
from sql import db_session


class IQuoteStore(object):
    def connect(self): pass
    def get(self, id): pass
    def put(self, quote): pass
    def latest(Self, n): pass
    def up_vote(self, id): pass
    def down_vote(self, id): pass

class SQLQuoteStore(IQuoteStore):
    def connect(self):
        pass
    
    def put(self, quote):
        db_session.add(quote)
        db_session.commit()
        
    def get(self, id):
        quote = db_session.query(Quote).filter_by(id=id).first()
        return quote

    def latest(self, n):
        quotes = db_session.query(Quote).order_by(Quote.id.desc()).limit(n).all()
        return quotes


    def up_vote(self, id):
        quote = self.get(id)
        quote.up_votes += 1
        db_session.commit()

    def down_vote(self, id):
        quote = self.get(id)
        quote.down_votes += 1
        db_session.commit()

db = SQLQuoteStore()

