#!/usr/bin/env python

from datetime import datetime

from django.test import TestCase
import lxml.etree
import lxml.html
from mock import Mock
import requests

from activecalls.management.commands.scrapecalls import ACTIVE_CALLS_URL, PagerRowError, ScrapeCallsCommand

def pop_last_call(mock):
    """
    From: http://www.voidspace.org.uk/python/mock/examples.html#checking-multiple-calls-with-mock
    """
    if not mock.call_count:
        raise AssertionError("Cannot pop last call: call_count is 0")
    mock.call_args_list.pop()
    
    try:
        mock.call_args = mock.call_args_list[-1]
    except IndexError:
        mock.call_args = None
        mock.called = False

    mock.call_count -=1

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

    def test_scrape_row(self):
        row_html = '''<tr style="color:#333333;background-color:#FFFBD6;font-family:Arial;font-size:8pt;white-space:nowrap;">
			<td>113330390</td><td>Immediate</td><td>Disturbance Unspecified</td><td></td><td>O </td><td>18:08</td><td>18:14</td><td>3400</td><td>  </td><td>VARSITY                       </td><td>DR  </td><td>PATRIOT                       </td><td>DR  </td><td><a></a></td><td style="font-size:0pt;">A</td>
		</tr>'''

        tr = lxml.html.fromstring(row_html)
        report_time = datetime(2011, 12, 4, 18, 45, 0)

        call_data = self.command.scrape_row(tr, report_time)

        self.assertEqual(call_data, {
            'case_number': '113330390',
            'priority': 'Immediate',
            'incident': 'Disturbance Unspecified',
            'status': 'O',
            'reported': datetime(2011, 12, 4, 18, 8, 0),
            'on_scene': datetime(2011, 12, 4, 18, 14, 0),
            'street_number': '3400',
            'street_prefix': '',
            'street_name': 'VARSITY',
            'street_suffix': 'DR',
            'cross_street_name': 'PATRIOT',
            'cross_street_suffix': 'DR',
            'raw_html': lxml.etree.tostring(tr),
            'first_seen': report_time,
            'last_modified': report_time,
            'last_seen': report_time            
        })

    def test_scrape_pager_row(self):
        row_html = '''<tr align="center" style="color:#333333;background-color:#FFCC66;font-family:Arial;font-size:8pt;">
			<td colspan="15"><table border="0">
				<tr>
					<td><span>1</span></td><td><a href="javascript:__doPostBack('GridView1','Page$2')" style="color:#333333;">2</a></td>
				</tr>'''

        tr = lxml.html.fromstring(row_html)
        report_time = datetime(2011, 12, 4, 18, 45, 0)

        self.assertRaises(PagerRowError, ScrapeCallsCommand.scrape_row, self.command, tr, report_time)

    def test_scrape_page(self):
        page1_html = open('testdata/page1.html').read()
        page2_html = open('testdata/page2.html').read()

        return_values = [page1_html, page2_html]

        def get(*args, **kwargs):
            m = Mock()
            m.content = return_values.pop(0)

            return m

        requests.get = Mock(side_effect=get)

        calls = self.command.scrape_page(1)

        root = lxml.html.fromstring(page1_html)
        view_state = root.cssselect('#__VIEWSTATE')[0].value
        event_validation = root.cssselect('#__EVENTVALIDATION')[0].value

        requests.get.assert_called_with(ACTIVE_CALLS_URL, params={ '__EVENTTARGET': 'GridView1', '__EVENTARGUMENT': 'Page$2', '__VIEWSTATE': view_state, '__EVENTVALIDATION': event_validation })
        pop_last_call(requests.get)
        requests.get.assert_called_once_with(ACTIVE_CALLS_URL, params={})

        self.assertEqual(len(calls), 8) 
        self.assertEqual([c['case_number'] for c in calls], ['113380157', '113380156', '113380155', '113380153', '113380152', '113380150', '113380147', '113380144'])

