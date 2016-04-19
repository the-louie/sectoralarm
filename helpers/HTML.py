from HTMLParser import HTMLParser

# create a subclass and override the handler methods
class parseHTMLToken(HTMLParser):
    def __init__(self):
        self.tokens = []
        HTMLParser.__init__(self)

    def __get_value(self, key, attrs):
        for attr in attrs:
            if attr[0] == key:
                return attr[1]

    def handle_starttag(self, tag, attrs):
        is_token = False
        if tag == 'input':
            for attr in attrs:
                if attr[0].lower() == 'name' and attr[1] == '__RequestVerificationToken':
                    self.tokens.append(self.__get_value('value', attrs))

class parseHTMLstatus(HTMLParser):
    def __init__(self):
        self.statuses = {}
        self.currclass = None
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            if attr[0] == 'class' and attr[1][:15] == 'panel-overview-':
                self.currclass = attr[1][15:]

    def handle_data(self, data):
        stripdata = data.strip()
        if self.currclass and stripdata != '':
            self.statuses[self.currclass] = stripdata

    def handle_endtag(self, tag):
        self.currclass = None
