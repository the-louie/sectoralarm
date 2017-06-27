#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This is a small module to interface against the webpage of Sector Alarm.

Current functions:
    get_status()       - returns the current status as an object, example:
                            {"ArmedStatus": "disarmed"}

    get_log()          - returns the event log as a list, example:
                            [
                                {
                                    "EventType": "disarmed",
                                    "LockName": "sitename.event.disarming",
                                    "User": "user1",
                                    "Channel": "",
                                    "Time": "2017-06-18T16:17:00"
                                },
                                {
                                    "EventType": "armed",
                                    "LockName": "sitename.event.arming",
                                    "User": "user2",
                                    "Channel": "",
                                    "Time": "2017-06-17T12:01:00"
                                },
                                {
                                    "EventType": "disarmed",
                                    "LockName": "sitename.event.disarming",
                                    "User": "user1",
                                    "Channel": "",
                                    "Time": "2017-06-17T10:22:00"
                                }
                            ]
'''

import datetime
import json
import os
import re
import sys
import requests
from helpers.HTML import ParseHTMLToken


LOGINPAGE = 'https://mypagesapi.sectoralarm.net/User/Login'
CHECKPAGE = 'https://mypagesapi.sectoralarm.net/'
STATUSPAGE = 'https://mypagesapi.sectoralarm.net/Panel/GetOverview/'
LOGPAGE = 'https://mypagesapi.sectoralarm.net/Panel/GetPanelHistory/'
COOKIEFILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data', 'cookies.jar')


def log(message):
    '''
    If we're in debug-mode we should show a lot more output
    '''
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
    result = ""
    try:
        epoch = re.search(r'\/Date\(([0-9]+?)\)\/', date_string).group(1)
        date = datetime.datetime.fromtimestamp(int(epoch)/1000)
        result = date.isoformat()
    except AttributeError:
        result = ""

    return result


class SectorStatus():
    '''
    The class that returns the current status of the alarm.
    '''
    def __init__(self, configdata):
        self.config = configdata
        self.session = requests.Session()


    def __get_token(self):
        '''
        Do an initial request to get the CSRF-token from
        the login form.
        '''
        response = self.session.get(LOGINPAGE)
        parser = ParseHTMLToken()
        parser.feed(response.text)
        if not parser.tokens[0]:
            raise Exception('Could not find CSRF-token.')

        return parser.tokens[0]

    def __get_status(self):
        '''
        Fetch and parse the actual alarm status page.
        '''
        response = self.session.post(STATUSPAGE)
        return {'ArmedStatus': response.json().get('Panel', {}).get('ArmedStatus', None)}

    def __get_log(self):
        '''
        Fetch and parse the event log page.
        '''
        response = self.session.get(LOGPAGE + config.siteid)
        event_log = []
        for row in  (response.json())['LogDetails']:
            row_data = row.copy()
            row_data['Time'] = fix_date(row_data.get('Time', None))
            event_log.append(row_data)

        return event_log

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
        try:
            with open(COOKIEFILE, 'r') as cookie_file:
                self.session.cookies = requests.utils.cookiejar_from_dict(
                    json.load(cookie_file)
                )
        except IOError, message:
            if str(message)[:35] != '[Errno 2] No such file or directory':
                raise message

        log('Loaded {0} cookie values'.format(
            len(requests.utils.dict_from_cookiejar(
                self.session.cookies).keys())))

    def __is_logged_in(self):
        '''
        Check if we're logged in.

        Returns bool
        '''
        response = self.session.get(CHECKPAGE)
        loggedin = ('frmLogin' not in response.text)
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
                'userID': self.config.email,
                'password': self.config.password
            }
            self.session = requests.Session()
            # Get CSRF-token and add it to the form data.
            form_data['__RequestVerificationToken'] = self.__get_token()

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
