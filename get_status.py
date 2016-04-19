# -*- coding: utf-8 -*-
import sys
import requests
import config
from helpers.HTML import parseHTMLToken, parseHTMLstatus

LOGINPAGE = 'https://minasidor.sectoralarm.se/Users/Account/LogOn'
VALIDATEPAGE = 'https://minasidor.sectoralarm.se/MyPages.LogOn/Account/ValidateUser'
STATUSPAGE = 'https://minasidor.sectoralarm.se/MyPages/Overview/Panel/' + config.siteid


def cleanup_user(current_status):
    """
    Cleanup the user string in the status object to only contain username.
    """
    current_status['user'] = current_status['user'].replace('(av ', '')
    current_status['user'] = current_status['user'].replace(')', '')
    return current_status


class SectorStatus():
    """
    The class that returns the current status of the alarm.
    """
    def __init__(self):
        self.session = None

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
        Fetch and parse the actual alarm status.
        """
        response = self.session.get(STATUSPAGE)
        parser = parseHTMLstatus()
        parser.feed(response.text)
        return parser.statuses

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
        form_data = {
            'userNameOrEmail': config.email,
            'password': config.password
        }

        # Create a session that shares cookies.
        with requests.Session() as self.session:
            # Get CSRF-token and add it to the form data.
            form_data['__RequestVerificationToken'] = self.__get_token()

            # Verify username and password.
            verify_page = self.session.post(VALIDATEPAGE, data=form_data)
            if not verify_page.json()['Success']:
                print "FAILURE", (verify_page.json()['Message'] or "No messsage")
                sys.exit(1)

            # Do the actual logging in.
            self.session.post(LOGINPAGE + '?Returnurl=~%2F', data=form_data)

            # Get the status
            return cleanup_user(self.__get_status())

if __name__ == '__main__':
    SECTORSTATUS = SectorStatus()
    print SECTORSTATUS.status()
