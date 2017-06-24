# -*- coding: utf-8 -*-
'''
Simple helper library only used to extract the CSRF-token from the login
page, can probably just be merged with the main script.
'''

from HTMLParser import HTMLParser

def get_value(key, attrs):
    '''
    Find the key and return it's value
    '''
    for attr in attrs:
        if attr[0] == key:
            return attr[1]

# create a subclass and override the handler methods
class ParseHTMLToken(HTMLParser):
    '''
    Parse the HTML data and return the CSRF-token
    '''
    def __init__(self):
        self.tokens = []
        HTMLParser.__init__(self)



    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            for attr in attrs:
                if attr[0].lower() == 'name' and attr[1] == '__RequestVerificationToken':
                    self.tokens.append(get_value('value', attrs))
