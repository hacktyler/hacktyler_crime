#!/usr/bin/env python

from datetime import datetime

from django.test import TestCase

from activecalls.management.commands.scrapecalls import ScrapeCallsCommand

class TestScrapeCalls(TestCase):
    def setUp(self):
        self.command = ScrapeCallsCommand()
    
    def test_datetime_from_relative_time_simple(self):
        timestring = '03:00'
        report_time = datetime(2011, 12, 4, 16, 45, 0)
        dt = self.command.datetime_from_relative_time(timestring, report_time)

        expected = datetime(2011, 12, 4, 3, 0, 0)
        self.assertEqual(dt, expected)
    
    def test_datetime_from_relative_time_crossing_midnight(self):
        timestring = '23:30'
        report_time = datetime(2011, 12, 5, 0, 1, 0)
        dt = self.command.datetime_from_relative_time(timestring, report_time)

        expected = datetime(2011, 12, 4, 23, 30, 0)
        self.assertEqual(dt, expected)

