from HTMLParser import HTMLParser

STATUSKEYS = {
    'status': 'event',
    'time': 'timestamp',
    'user': 'user'
}

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
            self.statuses[STATUSKEYS[self.currclass]] = stripdata

    def handle_endtag(self, tag):
        self.currclass = None

class parseHTMLlog(HTMLParser):
    def __init__(self):
        self.log = []
        self.in_head = False
        self.in_event = False
        self.in_log = False
        self.in_foot = False
        self.curr_event = []
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        """
        When we find an opening TR tag we start a new event
        """
        if tag.lower() == 'tbody':
            self.in_log = True

        if tag.lower() == 'tr':
            self.in_event = True

        if tag.lower() == 'th':
            self.in_head = True

        if tag.lower() == 'td':
            for attr in attrs:
                if attr[0].lower() == 'class' and attr[1].lower()[:17] == 'next-logs-toggle-':
                    self.in_foot = True

    def handle_data(self, rawdata):
        """
        When we get data, and we're 'in_event' we should add that
        data to the current event.
        """
        data = rawdata.strip()
        if self.in_log and self.in_event and not self.in_head and not self.in_foot and data:
            self.curr_event.append(data)


    def handle_endtag(self, tag):
        if tag.lower() == 'tr':
            if self.curr_event:
                self.log.append(self.curr_event)
            self.in_event = False
            self.curr_event = []

        if tag.lower() == 'tbody':
            self.in_log = False

        if tag.lower() == 'th':
            self.in_head = False

        if tag.lower() == 'td' and self.in_foot:
            self.in_foot = False



