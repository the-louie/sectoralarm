# -*- coding: utf-8 -*-
"""
This is a small module to interface against the webpage of Sector Alarm.

Current functions:
    get_status()       - returns the current status as an object, example:
                            {
                              "status": "Frånkopplat",
                              "user": "Person C",
                              "time": "Idag 9:40"
                            }

    get_log()          - returns the event log as a list, example:
                            [
                              [
                                "Tillkopplat",
                                "Igår 9:46",
                                "Person A"
                              ],
                              [
                                "Frånkopplat",
                                "16/4 19:20",
                                "Person B"
                              ],
                              [
                                "Tillkopplat",
                                "16/4 18:51",
                                "Person B"
                              ],
                              [
                                "Frånkopplat",
                                "14/4 11:33",
                                "Person C"
                              ],
                              [
                                "Tillkopplat",
                                "14/4 10:06",
                                "Person A"
                              ]
                            ]
"""

import config
import datetime
import json
from helpers.HTML import parseHTMLToken, parseHTMLstatus, parseHTMLlog
import HTMLParser
import re
import requests
import sys

LOGINPAGE = 'https://minasidor.sectoralarm.se/Users/Account/LogOn'
VALIDATEPAGE = 'https://minasidor.sectoralarm.se/MyPages.LogOn/Account/ValidateUser'
STATUSPAGE = 'https://minasidor.sectoralarm.se/MyPages/Overview/Panel/' + config.siteid
LOGPAGE = 'https://minasidor.sectoralarm.se/MyPages/Panel/AlarmSystem/' + config.siteid + '?locksAvailable=False'
COOKIEFILE = './data/cookies.jar'

DATENORMRE = re.compile(r'(\d+)/(\d+) (\d+):(\d+)')
DATESPECRE = re.compile(r'^(.+) (\d+):(\d+)')


def cleanup_user(current_status):
    """
    Cleanup the user string in the status object to only contain username.
    """
    current_status['user'] = current_status['user'].replace('(av ', '')
    current_status['user'] = current_status['user'].replace(')', '')
    return current_status

def fix_date(date_string):
    """
    Convert the Sectore Alarm way of stating dates to something sane (ISO compliant).
    """
    datematches = DATENORMRE.match(date_string)
    namematches = DATESPECRE.match(date_string)
    today = datetime.datetime.now().date()
    if datematches:
        the_date = datetime.datetime(
            int(datetime.datetime.now().strftime('%Y')),
            int(datematches.group(2)),
            int(datematches.group(1)), int(datematches.group(3)), int(datematches.group(4)))
        # If it's in the future, it was probably last year.
        if datetime.datetime.now() < the_date:
            the_date = datetime.datetime(the_date.year - 1, the_date.month, the_date.day, the_date.hour, the_date.minute)
    elif namematches:
        if namematches.group(1) == u'Idag':
            the_date = datetime.datetime(today.year, today.month, today.day)
        elif namematches.group(1) == u'Igår':
            the_date = (datetime.datetime(today.year, today.month, today.day) - datetime.timedelta(1))
        else:
            raise Exception("Unknown date type in '{0}'".format(date_string))

        the_date = the_date + datetime.timedelta(hours=int(namematches.group(2)), minutes=int(namematches.group(3)))

    else:
        raise Exception("No match for ", date_string)

    result = the_date.strftime('%Y-%m-%d %H:%M:%S')

    return result


class SectorStatus():
    """
    The class that returns the current status of the alarm.
    """
    def __init__(self):
        # self.session = None
        self.session = requests.Session()

    def __get_token(self):
        """
        Do an initial request to get the CSRF-token from
        the login form.
        """
        response = self.session.get(LOGINPAGE)
        parser = parseHTMLToken()
        parser.feed(response.text)

        if not parser.tokens[0]:
            raise Exception('Could not find CSRF-token.')

        return parser.tokens[0]

    def __get_status(self):
        """
        Fetch and parse the actual alarm status page.
        """
        response = self.session.get(STATUSPAGE)
        parser = parseHTMLstatus()
        parser.feed(response.text)
        return parser.statuses

    def __get_log(self):
        """
        Fetch and parse the event log page.
        """
        response = self.session.get(LOGPAGE)
        parser = parseHTMLlog()
        parser.feed(HTMLParser.HTMLParser().unescape(response.text))
        result = []
        for row in parser.log:
            result.append({'event': row[0], 'date': fix_date(row[1]), 'user': row[2]})
        return result

    def __save_cookies(self):
        """
        Store the cookie-jar on disk to avoid having to login
        each time the script is run.
        """
        with open(COOKIEFILE, 'w') as cookie_file:
            json.dump(
                requests.utils.dict_from_cookiejar(self.session.cookies),
                cookie_file
            )

    def __load_cookies(self):
        """
        Load the cookies from the cookie-jar to avoid logging
        in again if the session still is valid.
        """
        with open(COOKIEFILE, 'r') as cookie_file:
            self.session.cookies = requests.utils.cookiejar_from_dict(
                json.load(cookie_file)
            )

    def __is_logged_in(self):
        """
        Check if we're logged in.

        Returns bool
        """
        response = self.session.get(LOGINPAGE)
        loggedin = ('logOnForm' not in response.text)
        return loggedin

    def __login(self):
        """
        Login to the site if we're not logged in already. First try any
        existing session from the stored cookie. If that fails we should
        login again.
        """
        self.__load_cookies()

        if not self.__is_logged_in():
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
                print "FAILURE",
                print (verify_page.json()['Message'] or "No messsage")
                sys.exit(1)

            # Do the actual logging in.
            self.session.post(LOGINPAGE + '?Returnurl=~%2F', data=form_data)

            # Save the cookies to file.
            self.__save_cookies()

    def event_log(self):
        """
        Retrive the event log
        """
        self.__login()

        # Get event log
        return self.__get_log()

    def status(self):
        """
        Wrapper function for logging in and fetching the status
        of the alarm in one go that returns a dict.

        Example:
            {
                'status': 'Fr\xe5nkopplat',
                'user': 'Person ett',
                'time': 'Idag 07:14'
            }
        """
        self.__login()

        # Get the status
        return cleanup_user(self.__get_status())

if __name__ == '__main__':
    if len(sys.argv) < 2 or (sys.argv[1] != 'status' and sys.argv[1] != 'log'):
        print "Usage:", sys.argv[0],"[status|log]"
        sys.exit(1)

    SECTORSTATUS = SectorStatus()
    if sys.argv[1] == 'status':
        print json.dumps(SECTORSTATUS.status())
    elif sys.argv[1] == 'log':
        print json.dumps(SECTORSTATUS.event_log())

