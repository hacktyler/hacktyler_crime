#!/usr/bin/env python

from datetime import datetime

from django.test import TestCase

from activecalls.models import ActiveCall

class TestActiveCall(TestCase):
    def test_geocode(self):
        report_time = datetime.now()

        active_call = ActiveCall(
            case_number='113330390',
            priority='Immediate',
            incident='Disturbance Unspecified',
            status='O',
            reported=datetime(2011, 12, 4, 18, 8, 0),
            on_scene=datetime(2011, 12, 4, 18, 14, 0),
            street_number='3400',
            street_prefix='',
            street_name='VARSITY',
            street_suffix='DR',
            cross_street_name='PATRIOT',
            cross_street_suffix='DR',
            raw_html='',
            first_seen=report_time,
            last_modified=report_time,
            last_seen=report_time            
        )

        active_call.save()

        self.assertNotEqual(active_call.point, None)

