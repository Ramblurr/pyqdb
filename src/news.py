import yaml

NEWS_FILE = 'news.yml'

class News(object):
    def __init__(self):
        self.news = None
        self.load()

    def load(self, file = NEWS_FILE):
        stream = open(file, 'r')
        self.news = yaml.load_all(stream)

