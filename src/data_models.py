import json
from sqlalchemy import MetaData, Column, Table, ForeignKey
from sqlalchemy import Integer, String
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
    body = Column(String)
    tags = relationship(Tag, secondary=quote_tags, backref="quotes")
    up_votes = Column(Integer)
    down_votes = Column(Integer)

    def __init__(self, body):
        self.body = body
        self.up_votes = 0
        self.down_votes = 0

    def __repr__(self):
        return "<Quote('%s', up:%s, down:%s)>" %(self.body, self.up_votes, self.down_votes)

    def rating(self):
        return self.up_votes - self.down_votes

    def votes(self):
        return self.up_votes + self.down_votes

    def json(self):
        return json.dumps({'id': self.id, 'up': self.up_votes, 'down': self.down_votes})
    def votes_json(self):
        return json.dumps( { 'up': self.up_votes, 'down': self.down_votes} )

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
