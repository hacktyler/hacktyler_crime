#!/usr/bin/env python

import logging 
log = logging.getLogger('activecalls.models')

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.utils import simplejson as json
import requests

MAPQUEST_API = 'http://www.mapquestapi.com/geocoding/v1/address'

class GeocodingError(Exception):
    pass

class ActiveCall(models.Model):
    """
    An entry from Tyler's Active Call List:
    http://cityoftyler.org/acl/acl.aspx
    """
    case_number = models.TextField(unique=True)
    priority = models.TextField()
    incident = models.TextField()
    status = models.TextField()
    reported = models.DateTimeField()
    on_scene = models.DateTimeField(null=True, blank=True)
    street_number = models.TextField()
    street_prefix = models.TextField()
    street_name = models.TextField()
    street_suffix = models.TextField()
    cross_street_name = models.TextField()
    cross_street_suffix = models.TextField()

    raw_html = models.TextField()

    # These fields are based on the server timestamp, not now()
    first_seen = models.DateTimeField()
    last_modified = models.DateTimeField()
    last_seen = models.DateTimeField()

    point = models.PointField(srid=4269, null=True, blank=True,
        help_text='The location of this call in EPSG:4269 projection.')

    objects = models.GeoManager()

    class Meta:
        ordering = ('reported',)

    def __unicode__(self):
        """
        Print plural names.
        """
        return u'Case #%s - %s' % (self.case_number, self.incident)

    def save(self, geocode=True, *args, **kwargs):
        if geocode:
            try:
                if not self.cross_street_name:
                    log.info('Not attempting intersection geocoding without a cross street (%s)' % self.case_number)
                    raise GeocodingError('Must have an intersection to geocode.')

                try:
                    location = '%s and %s' % (
                        self.street_name,
                        self.cross_street_name
                    )

                    response = requests.post('%s?key=%s&inFormat=json' % (MAPQUEST_API, settings.MAPQUEST_API_KEY), json.dumps({
                            'location': {
                                'street': location,
                                'city': 'tyler',
                                'state': 'tx',
                                'county': 'smith'
                            },
                            'options': {
                                'thumbMaps': False,
                                'maxResults': 1
                            }
                        })
                    )

                    if response.status_code != 200:
                        raise GeocodingError('MapQuest API returned status code: %s' % response.status_code)

                    data = json.loads(response.content)        
                    result = data['results'][0]

                    if result['locations'][0]['geocodeQuality'] != 'INTERSECTION':
                        log.info('Geocoded to %s, not INTERSECTION: "%s" (%s)' % (result['locations'][0]['geocodeQuality'], location, self.case_number))
                        raise GeocodingError('MapQuest failed to find an intersection matching this location.')
                except GeocodingError:
                    location = '%s %s %s' % (
                        self.street_number,
                        self.street_prefix,
                        self.street_name,
                    )

                    response = requests.post('%s?key=%s&inFormat=json' % (MAPQUEST_API, settings.MAPQUEST_API_KEY), json.dumps({
                            'location': {
                                'street': location,
                                'city': 'tyler',
                                'state': 'tx',
                                'county': 'smith'
                            },
                            'options': {
                                'thumbMaps': False,
                                'maxResults': 1
                            }
                        })
                    )

                    if response.status_code != 200:
                        raise GeocodingError('MapQuest API returned status code: %s' % response.status_code)
                
                    data = json.loads(response.content)        
                    result = data['results'][0]

                    if result['locations'][0]['geocodeQuality'] not in ('ADDRESS', 'STREET'):
                        log.info('Geocoded to %s, not ADDRESS or STREET: "%s" (%s)' % (result['locations'][0]['geocodeQuality'], location, self.case_number))
                        raise GeocodingError('MapQuest failed to find a street matching this location.')

                lat = result['locations'][0]['latLng']['lat']
                lng = result['locations'][0]['latLng']['lng']

                self.point = Point(lng, lat)
                
                log.info('Successfully geocoded: "%s" (%s)' % (location, self.case_number))
            except GeocodingError:
                self.point = None

        super(ActiveCall, self).save(*args, **kwargs)

