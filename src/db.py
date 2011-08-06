import datetime
import json
from data_models import Quote,Tag,Vote,Voter
from sql import db_session
from sqlalchemy import func,desc


class IQuoteStore(object):
    def connect(self): pass
    def get(self, id): pass
    def put(self, quote): pass
    def latest(self, n, start): pass
    def top(self, n, start): pass
    def random(self, n): pass
    def up_vote(self, id, ip): pass
    def down_vote(self, id, ip): pass
    def count(self): pass

class SQLQuoteStore(IQuoteStore):
    def connect(self):
        pass
    
    def put(self, quote):
        db_session.add(quote)
        db_session.commit()
        
    def get(self, id):
        quote = db_session.query(Quote).filter_by(id=id).first()
        return quote

    def latest(self, limit, offset):
        quotes = db_session.query(Quote).order_by(Quote.id.desc()).limit(limit).offset(offset).all()
        return quotes

    def top(self, limit, offset):
        quotes = db_session.query(Quote,(Quote.up_votes-Quote.down_votes).label('sum')).order_by(desc('sum')).limit(limit).offset(offset).all()
        quotes = [t[0] for t in quotes]
        return quotes

    def random(self, limit):
        quotes = db_session.query(Quote).order_by(func.random()).limit(limit)
        return quotes

    def _vote(self, id, ip, type):
        quote = self.get(id)

        voter = Voter(ip)
        vote = Vote(type)
        vote.quote_id = id
        vote.type = type
        result = db_session.query(Voter).filter(Voter.votes.any(Vote.quote_id==id)).filter(Voter.votes.any(Vote.type == type)).all()
        if len(result) > 0:
            return False
    
        voter.votes.append( vote )
        if type == 'up':
            quote.up_votes += 1
        elif type == 'down':
            quote.down_votes += 1

        db_session.commit()
        return quote

    def up_vote(self, id, ip):
        return self._vote(id, ip, 'up')
        
    def down_vote(self, id, ip):
        return self._vote(id, ip, 'down')

    def count(self):
        return db_session.query(Quote).count()

db = SQLQuoteStore()

