#!/usr/bin/env python

import datetime
import logging 
log = logging.getLogger('activecalls.scrapecalls')
import time

from dateutil import parser
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.serializers.json import DjangoJSONEncoder
import lxml.etree
import lxml.html
import pusher
import requests

from activecalls.models import ActiveCall
from activecalls.resources import ActiveCallResource

ACTIVE_CALLS_URL = 'http://cityoftyler.org/acl/acl.aspx'

class PagerRowError(Exception):
    """
    Exception encountered when a pager row is encountered.
    """
    def __init__(self, num_pages):
        self.num_pages = num_pages

class Command(BaseCommand):
    """
    Scrape the Tyler PD Active Calls List.
    """
    help = 'Scrape the Tyler PD Active Calls list.'
    
    def handle(self, *args, **options):
        calls = self.scrape_page(1) 

        for call_data in calls:
            self.save_call(call_data)

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

            try:
                call = self.scrape_row(tr, report_time)
            except PagerRowError, e:
                if page_number == 1:
                    log.info('Found %i additional pages' % (e.num_pages - 1))

                    for p in range(1, e.num_pages):
                        calls.extend(self.scrape_page(p + 1, view_state, event_validation))

                continue

            calls.append(call)

        return calls 

    def scrape_row(self, tr, report_time):
        """
        Extracts call data from a table row.

        Returns a dict of attributes
        """
        tds = tr.cssselect('td')

        # Pager
        if len(tds) < 12:
            raise PagerRowError(len(tds) - 1) 

        cells = [td.text_content().strip() for td in tds]

        return {
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

    def save_call(self, call_data):
        try:
            active_call = ActiveCall.objects.get(case_number=call_data['case_number'])

            modified = False

            for attr in ['priority', 'incident', 'status', 'on_scene', 'street_number', 'street_prefix', 'street_name', 'street_suffix', 'cross_street_name', 'cross_street_suffix']:
                if call_data[attr] != getattr(active_call, attr):
                    log.info('%s -- %s changed, "%s" became "%s"' % (unicode(active_call), attr, getattr(active_call, attr), call_data[attr]))
                    setattr(active_call, attr, call_data[attr])
                    modified = True

            if modified:
                active_call.last_modified = call_data['last_modified']

            active_call.last_seen = call_data['last_seen'] 
            active_call.save(geocode=modified)  # only geocode if something has changed
            time.sleep(1)

            if modified:
                self.push_notification('changed_active_call', active_call)
        except ActiveCall.DoesNotExist:
            active_call = ActiveCall.objects.create(**call_data)

            self.push_notification('new_active_call', active_call)

            log.debug('Saved new active call: %s' % unicode(active_call))

    def push_notification(self, event, active_call):
        p = pusher.Pusher(
            app_id=settings.PUSHER_APP_ID,
            key=settings.PUSHER_KEY,
            secret=settings.PUSHER_SECRET,
            encoder=DjangoJSONEncoder)

        resource = ActiveCallResource()

        bundle = resource.build_bundle(obj=active_call)
        bundle = resource.full_dehydrate(bundle)

        p[settings.PUSHER_CHANNEL].trigger(event, bundle.data)

