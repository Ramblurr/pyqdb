import json
from datetime import datetime
from dateutil import tz
from sqlalchemy import MetaData, Column, Table, ForeignKey
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import relationship, backref

from sql import db_session,Base

# magic recipe from http://www.sqlalchemy.org/trac/wiki/UsageRecipes/UniqueObject
# lets us automagically have only unique keywords (or other kinds of objects)
# without doing a query for the keyword and getting a reference to the row 
# containing that keyword
def unique_constructor(scoped_session, hashfunc, queryfunc):
    def decorate(cls):
        def _null_init(self, *arg, **kw):
            pass
        def __new__(cls, bases, *arg, **kw):
            # no-op __new__(), called
            # by the loading procedure
            if not arg and not kw:
                return object.__new__(cls)

            session = scoped_session()
            cache = getattr(session, '_unique_cache', None)
            if cache is None:
                session._unique_cache = cache = {}
        
            key = (cls, hashfunc(*arg, **kw))
            if key in cache:
                return cache[key]
            else:
                # disabling autoflush is optional here.
                # this tends to be an awkward place for 
                # flushes to occur, however, as we're often
                # inside a constructor.
                with no_autoflush(session):
                    q = session.query(cls)
                    q = queryfunc(q, *arg, **kw)
                    obj = q.first()
                    if not obj:
                        obj = object.__new__(cls)
                        obj._init(*arg, **kw)
                        session.add(obj)
                cache[key] = obj
                return obj
        
        cls._init = cls.__init__
        cls.__init__ = _null_init
        cls.__new__ = classmethod(__new__)
        return cls
        
    return decorate


quote_tags = Table('quote_tags', Base.metadata,
                    Column('quote_id', Integer, ForeignKey('quotes.id')),
                    Column('tag_id', Integer, ForeignKey('tags.id')))

quote_votes = Table('quote_votes', Base.metadata,
                    Column('quote_id', Integer, ForeignKey('quotes.id')),
                    Column('vote_id', Integer, ForeignKey('votes.id')))

@unique_constructor(db_session, 
            lambda tag:tag, 
            lambda query, tag:query.filter(Tag.tag==tag)
    )
class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String, nullable=False, unique=True)
    def __init__(self, tag):
        self.tag = tag

class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True)
    body = Column(String, nullable=False)
    tags = relationship(Tag, secondary=quote_tags, backref="quotes")
    up_votes = Column(Integer, nullable=False)
    down_votes = Column(Integer, nullable=False)
    created = Column(DateTime, nullable=False)
    created_by = Column(String)

    def __init__(self, body, author = None):
        self.body = body
        self.up_votes = 0
        self.down_votes = 0
        self.created_by = author
        self.created = datetime.utcnow()

    def rating(self):
        return self.up_votes - self.down_votes

    def num_votes(self):
        return self.up_votes + self.down_votes

    def votes_json(self):
        return json.dumps( { 'up': self.up_votes, 'down': self.down_votes} )

    def created_local(self):
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/New_York')
        utc = self.created.replace(tzinfo=from_zone)
        return utc.astimezone(to_zone)


class QuoteEncoder(json.JSONEncoder):
    ''' a custom JSON encoder for Quote objects '''
    def default(self, q):
        if not isinstance(q, Quote):
            print 'You cannot use the JSON custom encoder for a non-Quote object.'
            return
        return {'id': q.id, 'up': q.up_votes, 'down': q.down_votes, 'body': q.body}
    
@unique_constructor(db_session, 
            lambda ip:ip, 
            lambda query, ip:query.filter(Voter.ip==ip)
    )
class Voter(Base):
    __tablename__ = 'voters'
    id = Column(Integer, primary_key=True)
    ip = Column(String, nullable=False, unique=True)

    def __init__(self, ip):
        self.ip = ip

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    quote_id = Column(None, ForeignKey('quotes.id'))
    voter_id = Column(None, ForeignKey('voters.id'))
    type = Column(String, nullable=False)
    quote = relationship(Quote, primaryjoin=(quote_id==Quote.id), backref=backref('votes', order_by=id))
    voter = relationship(Voter, primaryjoin=(voter_id==Voter.id), backref=backref('votes', order_by=id))

    def __init__(self, type):
        self.type = type



class no_autoflush(object):
    """Temporarily disable autoflush.

    See http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DisableAutoflush
    """
    def __init__(self, session):
        self.session = session
        self.autoflush = session.autoflush

    def __enter__(self):
        self.session.autoflush = False

    def __exit__(self, type, value, traceback):
        self.session.autoflush = self.autoflush
