# -*- coding: utf-8 -*-
import unittest

import transaction
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.z2 import Browser
from Products.MailHost.interfaces import IMailHost
from zope.component import getUtility
from zope.interface import alsoProvides

from plone.login.interfaces import IPloneLoginLayer
from plone.login.testing import PLONE_LOGIN_FUNCTIONAL_TESTING


class TestLoginLogout(unittest.TestCase):

    layer = PLONE_LOGIN_FUNCTIONAL_TESTING

    def setUp(self):
        # Make sure our browserlayer is applied
        alsoProvides(IPloneLoginLayer)
        self.browser = Browser(self.layer['app'])

    def test_login_with_bad_credentials(self):
        self.browser.open('http://nohost/plone/login')
        self.browser.getLink('Log in').click()
        self.assertEqual(self.browser.url, 'http://nohost/plone/login')

        self.browser.getControl('Login Name').value = TEST_USER_NAME
        self.browser.getControl('Password').value = 'wrongpassword'
        self.browser.getControl('Log in').click()

        self.assertIn("Login failed", self.browser.contents)
        self.assertEqual(self.browser.url, 'http://nohost/plone/login')

    def test_login_with_correct_credentials(self):
        self.browser.open('http://nohost/plone/login')
        self.browser.getLink('Log in').click()
        self.assertEqual(self.browser.url, 'http://nohost/plone/login')

        self.browser.getControl('Login Name').value = TEST_USER_NAME
        self.browser.getControl('Password').value = TEST_USER_PASSWORD
        self.browser.getControl('Log in').click()

        self.assertIn("You are now logged in.", self.browser.contents)
        self.assertEqual(self.browser.url,
                         'http://nohost/plone',
                         'Successful login did not redirect to the homepage when came_from was not defined.')

        # Now log out.
        self.browser.getLink('Log out').click()
        self.assertEqual(self.browser.url,
                         'http://nohost/plone',
                         'Successful logout did not redirect to the homepage.')

        self.assertIn('You have been logged out.',
                      self.browser.contents,
                      'Logout status message not displayed.')

    def test_login_with_user_defined_in_root_user_folder(self):
        """ A user defined in the root user folder should be able to log
            in into the site
        """
        self.layer['app'].acl_users.userFolderAddUser('rootuser',
                                                      'secret',
                                                      [],
                                                      [])
        transaction.commit()
        self.browser.open('http://nohost/plone/login')
        self.browser.getControl('Login Name').value = 'rootuser'
        self.browser.getControl('Password').value = 'secret'
        self.browser.getControl('Log in').click()
        self.assertIn('You are now logged in', self.browser.contents)

    def test_not_logged_in_and_not_authorized_shows_login_form(self):
        self.browser.open('http://nohost/plone/@@overview-controlpanel')
        self.assertTrue(self.browser.getControl('Login Name'))

    def test_insufficient_privileges_returned_when_logged_in_but_not_authorized(self):
        self.browser.open('http://nohost/plone/login')
        self.browser.getControl('Login Name').value = TEST_USER_NAME
        self.browser.getControl('Password').value = TEST_USER_PASSWORD
        self.browser.getControl('Log in').click()
        self.assertIn('You are now logged in', self.browser.contents)

        self.browser.open('http://nohost/plone/@@overview-controlpanel')
        self.assertIn('Insufficient Privileges', self.browser.contents)


class TestRequestAccess(unittest.TestCase):

    layer = PLONE_LOGIN_FUNCTIONAL_TESTING

    def setUp(self):
        # Make sure our browserlayer is applied
        alsoProvides(IPloneLoginLayer)
        self.browser = Browser(self.layer['app'])

    def test_insufficient_privileges_only_shows_access_button_when_site_can_send_email(self):

        mailhost = getUtility(IMailHost)
        self.assertEqual(mailhost.smtp_host, '')

        self.browser.open('http://nohost/plone/login')
        self.browser.getControl('Login Name').value = TEST_USER_NAME
        self.browser.getControl('Password').value = TEST_USER_PASSWORD
        self.browser.getControl('Log in').click()
        self.assertIn('You are now logged in', self.browser.contents)

        self.browser.open('http://nohost/plone/@@overview-controlpanel')
        self.assertIn('Insufficient Privileges', self.browser.contents)

        self.assertNotIn('Request Access', self.browser.contents)

        mailhost.smtp_host = 'localhost'
        setattr(self.layer['portal'], 'email_from_address', 'foo@example.com')

        self.browser.open('http://nohost/plone/@@overview-controlpanel')
        self.assertIn('Insufficient Privileges', self.browser.contents)

        self.assertIn('Request Access', self.browser.contents)


