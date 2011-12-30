import datetime
import json
from data_models import Quote,Tag,Vote,Voter,quote_tags
from sql import db_session
from sqlalchemy import func,desc,or_


class IQuoteStore(object):
    def connect(self): pass
    def get(self, id): pass
    def put(self, quote): pass
    def latest(self, n, start): pass
    def top(self, n, start): pass
    def random(self, n): pass
    def tags(self): pass
    def tag(self, tag, n, start): pass
    def tag_count(self, tag): pass
    def up_vote(self, id, ip): pass
    def down_vote(self, id, ip): pass
    def count(self): pass
    def search(self, query, n, start): pass

class SQLQuoteStore(IQuoteStore):
    def connect(self):
        pass

    def put(self, quote):
        db_session.add(quote)
        db_session.commit()
        return quote

    def delete(self, quote):
        db_session.delete(quote)
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

    def tags(self):
        tags = db_session.query(Tag).order_by(Tag.tag).all()
        tags_count = []
        for t in tags:
            tags_count.append( { 'tag': t.tag, 'count': db_session.query((quote_tags.c.tag_id).label('tag')).filter('tag == %s' %(t.id)).count()} )
        return tags_count

    def tag(self, tag, limit, offset):
        quotes = db_session.query(Quote).join(Quote.tags).filter(Quote.tags.contains(Tag(tag))).order_by(Quote.id.desc()).limit(limit).offset(offset).all()
        return quotes

    def tag_count(self, tag):
        return db_session.query(Quote).join(Quote.tags).filter(Quote.tags.contains(Tag(tag))).count()


    def _vote(self, id, ip, type):
        quote = self.get(id)

        voter = Voter(ip)
        vote = Vote(type)
        vote.quote_id = id
        vote.voter_id = voter.id
        vote.type = type

        result = db_session.query(Vote).filter_by(quote_id=id).filter_by(voter_i    d=voter.id).first()
        if not result is None:
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

    def search(self, query, limit, offset):
        q = '%' + query + '%'
        body_like = Quote.body.like(q)
        tag_like = Tag.tag.like(q)
        quotes = db_session.query(Quote).join(Quote.tags).filter(or_(tag_like,body_like)).order_by(Quote.id).limit(limit).offset(offset).all()
        return quotes


db = SQLQuoteStore()

