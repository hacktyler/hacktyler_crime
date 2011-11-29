#!/usr/bin/env python

import datetime
import logging 
log = logging.getLogger('activecalls.scrapecalls')

from dateutil import parser
from django.core.management.base import BaseCommand
import lxml.etree
import lxml.html
import requests

from activecalls.models import ActiveCall

ACTIVE_CALLS_URL = 'http://tylerpolice.com/acl/acl.aspx'

class Command(BaseCommand):
    """
    Scrape the Tyler PD Active Calls List.
    """
    help = 'Scrape the Tyler PD Active Calls list.'
    
    def handle(self, *args, **options):
        calls = self.scrape_page(1) 
        self.save_calls(calls)

    def scrape_page(self, page_number, view_state=None, event_validation=None):
        calls = []

        log.debug('Fetching page %i' % page_number)

        data = {}

        if page_number != 1:
            data.update({
                '__EVENTTARGET': 'GridView1',
                '__EVENTARGUMENT': 'Page$%i' % page_number,
                '__VIEWSTATE': view_state,
                '__EVENTVALIDATION': event_validation,

            })

        response = requests.get(ACTIVE_CALLS_URL, params=data)
        
        # TODO - handle error status codes or empty body
        
        html = response.content
        root = lxml.html.fromstring(html)

        # APS form nonsense
        view_state = root.cssselect('#__VIEWSTATE')[0].value
        event_validation = root.cssselect('#__EVENTVALIDATION')[0].value

        # Extract timestamp
        label = root.cssselect('#lblUpdate')[0]
        span = label.getnext()

        report_time = parser.parse(span.text_content().strip())

        table = root.cssselect('table')[0]
        trs = table.cssselect('tr')

        log.info('Found %i rows' % (len(trs) - 1))

        for i, tr in enumerate(trs):
            # Skip header row
            if i == 0:
                continue

            tds = tr.cssselect('td')

            # Pager
            if len(tds) < 12:
                if page_number == 1:
                    num_pages = len(tds) - 1

                    log.info('Found %i additional pages' % (num_pages - 1))

                    for p in range(1, num_pages):
                        calls.extend(self.fetch_page(p + 1, view_state, event_validation))
                    
                continue

            cells = [td.text_content().strip() for td in tds]

            call = {
                'case_number': cells[0],
                'priority': cells[1],
                'incident': cells[2],
                # Cell 3 - empty
                'status': cells[4],
                'reported': self.datetime_from_relative_time(cells[5], report_time),
                'on_scene': self.datetime_from_relative_time(cells[6], report_time),
                'street_number': cells[7],
                'street_prefix': cells[8],
                'street_name': cells[9],
                'street_suffix': cells[10],
                'cross_street_name': cells[11],
                'cross_street_suffix': cells[12],
                # Cell 13 - empty

                'raw_html': lxml.etree.tostring(tr),

                'first_seen': report_time,
                'last_modified': report_time,
                'last_seen': report_time
            }

            calls.append(call)

        return calls 

    def datetime_from_relative_time(self, timestring, report_time):
        if not timestring:
            return None

        hours, mins = map(int, timestring.split(':'))

        time_part = datetime.time(hours, mins)
        dt = datetime.datetime.combine(report_time.date(), time_part)
        
        # It's from yesterday
        if time_part.hour > 18 and report_time.hour < 6:
            dt = dt - datetime.timedelta(days=1)

        return dt

    def save_calls(self, calls):
        for call_data in calls:
            try:
                active_call = ActiveCall.objects.get(case_number=call_data['case_number'])

                # TODO: check hash and update last_modified if necessary

                active_call.last_seen = call_data['last_seen'] 
                active_call.save()
            except ActiveCall.DoesNotExist:
                active_call = ActiveCall.objects.create(**call_data)

                log.debug('Saved new active call: %s' % unicode(active_call))

