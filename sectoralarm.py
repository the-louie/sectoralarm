# -*- coding: utf-8 -*-
'''
This is a small module to interface against the webpage of Sector Alarm.

Current functions:
    get_status()       - returns the current status as an object, example:
                            {
                                "event": "Tillkopplat",
                                "user": "Person A",
                                "timestamp": "2016-02-14 23:17:00"
                            }

    get_log()          - returns the event log as a list, example:
                            [
                                {
                                    "timestamp": "2016-02-14 23:17:00",
                                    "event": "Tillkopplat",
                                    "user": "Person A"
                                }, {
                                    "timestamp": "2016-02-15 17:09:00",
                                    "event": "Frånkopplat",
                                    "user": "Person B"
                                }, {
                                    "timestamp": "2016-02-15 08:31:00",
                                    "event": "Tillkopplat",
                                    "user": "Person B"
                                }, {
                                    "timestamp": "2016-02-15 05:40:00",
                                    "event": "Frånkopplat",
                                    "user": "Person C"
                                }, {
                                    "timestamp": "2016-02-14 23:23:00",
                                    "event": "Tillkopplat",
                                    "user": "Person A"
                                }, {
                                    "timestamp": "2016-02-14 19:24:00",
                                    "event": "Frånkopplat",
                                    "user": "Person C"
                                }
                            ]
'''

import datetime
import json
from helpers.HTML import parseHTMLToken, parseHTMLstatus, parseHTMLlog
import HTMLParser
import os
import re
import requests
import sys


LOGINPAGE = 'https://minasidor.sectoralarm.se/Users/Account/LogOn'
VALIDATEPAGE = 'https://minasidor.sectoralarm.se/MyPages.LogOn/Account/ValidateUser'
STATUSPAGE = 'https://minasidor.sectoralarm.se/MyPages/Overview/Panel/'
LOGPAGE = 'https://minasidor.sectoralarm.se/MyPages/Panel/AlarmSystem/'
COOKIEFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cookies.jar')

DATENORMRE = re.compile(r'(\d+)/(\d+) (\d+):(\d+)')
DATESPECRE = re.compile(r'^(.+) (\d+):(\d+)')


def log(message):
    if os.environ.get('DEBUG'):
        print message


def fix_user(user_string):
    '''
    Cleanup the user string in the status object to only contain username.
    '''

    return user_string.replace('(av ', '').replace(')', '')


def fix_date(date_string):
    '''
    Convert the Sectore Alarm way of stating dates to something
    sane (ISO compliant).
    '''
    datematches = DATENORMRE.match(date_string)
    namematches = DATESPECRE.match(date_string)
    today = datetime.datetime.now().date()
    if datematches:
        the_date = datetime.datetime(
            int(datetime.datetime.now().strftime('%Y')),
            int(datematches.group(2)),
            int(datematches.group(1)),
            int(datematches.group(3)),
            int(datematches.group(4)))
        # If it's in the future, it was probably last year.
        if datetime.datetime.now() < the_date:
            the_date = datetime.datetime(
                the_date.year - 1,
                the_date.month,
                the_date.day,
                the_date.hour,
                the_date.minute)
    elif namematches:
        if namematches.group(1) == u'Idag':
            the_date = datetime.datetime(today.year, today.month, today.day)
        elif namematches.group(1) == u'Igår':
            the_date = (datetime.datetime(today.year,
                        today.month, today.day) - datetime.timedelta(1))
        else:
            raise Exception('Unknown date type in "{0}"'.format(date_string))

        the_date = the_date + datetime.timedelta(
            hours=int(namematches.group(2)),
            minutes=int(namematches.group(3)))

    else:
        raise Exception('No match for ', date_string)

    result = the_date.strftime('%Y-%m-%d %H:%M:%S')

    return result


class SectorStatus():
    '''
    The class that returns the current status of the alarm.
    '''

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()


    def __get_token(self):
        '''
        Do an initial request to get the CSRF-token from
        the login form.
        '''
        response = self.session.get(LOGINPAGE)
        parser = parseHTMLToken()
        parser.feed(response.text)

        if not parser.tokens[0]:
            raise Exception('Could not find CSRF-token.')

        return parser.tokens[0]

    def __get_status(self):
        '''
        Fetch and parse the actual alarm status page.
        '''
        response = self.session.get(STATUSPAGE + self.config.siteid)
        parser = parseHTMLstatus()
        parser.feed(response.text)
        return parser.statuses

    def __get_log(self):
        '''
        Fetch and parse the event log page.
        '''
        response = self.session.get(LOGPAGE + self.config.siteid + '?locksAvailable=False')
        parser = parseHTMLlog()
        parser.feed(HTMLParser.HTMLParser().unescape(response.text))
        result = []
        for row in parser.log:
            try:
                result.append({
                    'event': row[0],
                    'timestamp': fix_date(row[1]),
                    'user': row[2]
                })
            except IndexError, e:
                result.append({
                    'raw_event': row,
                    'error_message': e.__class__.__name__ + str(e)
                })
        return result

    def __save_cookies(self):
        '''
        Store the cookie-jar on disk to avoid having to login
        each time the script is run.
        '''
        with open(COOKIEFILE, 'w') as cookie_file:
            json.dump(
                requests.utils.dict_from_cookiejar(self.session.cookies),
                cookie_file
            )
        log('Saved {0} cookie values'.format(
            len(requests.utils.dict_from_cookiejar(
                self.session.cookies).keys())))

    def __load_cookies(self):
        '''
        Load the cookies from the cookie-jar to avoid logging
        in again if the session still is valid.
        '''
        with open(COOKIEFILE, 'r') as cookie_file:
            self.session.cookies = requests.utils.cookiejar_from_dict(
                json.load(cookie_file)
            )
        log('Loaded {0} cookie values'.format(
            len(requests.utils.dict_from_cookiejar(
                self.session.cookies).keys())))

    def __is_logged_in(self):
        '''
        Check if we're logged in.

        Returns bool
        '''
        response = self.session.get(LOGINPAGE)
        loggedin = ('logOnForm' not in response.text)
        return loggedin

    def __login(self):
        '''
        Login to the site if we're not logged in already. First try any
        existing session from the stored cookie. If that fails we should
        login again.
        '''
        self.__load_cookies()

        if not self.__is_logged_in():
            log('Logging in')
            form_data = {
                'userNameOrEmail': config.email,
                'password': config.password
            }
            self.session = requests.Session()
            # Get CSRF-token and add it to the form data.
            form_data['__RequestVerificationToken'] = self.__get_token()

            # Verify username and password.
            verify_page = self.session.post(VALIDATEPAGE, data=form_data)
            if not verify_page.json()['Success']:
                print 'FAILURE',
                print (verify_page.json()['Message'] or 'No messsage')
                sys.exit(1)

            # Do the actual logging in.
            self.session.post(LOGINPAGE + '?Returnurl=~%2F', data=form_data)

            # Save the cookies to file.
            self.__save_cookies()
        else:
            log('Already logged in')

    def event_log(self):
        '''
        Retrive the event log, login if neccesary.
        '''
        self.__login()

        # Get event log
        return self.__get_log()

    def status(self):
        '''
        Wrapper function for logging in and fetching the status
        of the alarm in one go that returns a dict.
        '''
        self.__login()

        # Get the status
        status = self.__get_status()
        status['timestamp'] = fix_date(status['timestamp'])
        status['user'] = fix_user(status['user'])
        return status

if __name__ == '__main__':
    if len(sys.argv) < 2 or (sys.argv[1] != 'status' and sys.argv[1] != 'log'):
        print 'Usage: {0} [status|log]'.format(sys.argv[0])
        sys.exit(1)

    import config
    SECTORSTATUS = SectorStatus(config)

    if sys.argv[1] == 'status':
        print json.dumps(SECTORSTATUS.status())
    elif sys.argv[1] == 'log':
        print json.dumps(SECTORSTATUS.event_log())
