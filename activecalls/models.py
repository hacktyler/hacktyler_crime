#!/usr/bin/env python

import logging 
log = logging.getLogger('activecalls.models')

from googlegeocoder import GoogleGeocoder

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.forms.models import model_to_dict

class GeocodingError(Exception):
    pass

class ActiveCall(models.Model):
    """
    An entry from Tyler's Active Call List:
    http://tylerpolice.com/acl/acl.aspx
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

    def _normalize_suffix(self, suffix):
        if suffix == 'HW':
            return 'HWY'

        if suffix == 'PK':
            return 'PKWY'

        if suffix == '' and self.street_name.lower() in ('1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th'):
            return 'ST'

        return suffix

    def save(self, *args, **kwargs):
        geocoder = GoogleGeocoder()

        try:
            if not self.cross_street_name:
                log.info('Not geocoding without a cross street (%s)' % self.case_number)
                raise GeocodingError('Must have an intersection to geocode.')

            try:
                location = '%s %s %s and %s %s Tyler, TX' % (
                    self.street_prefix,
                    self.street_name,
                    self._normalize_suffix(self.street_suffix),
                    self.cross_street_name,
                    self._normalize_suffix(self.cross_street_suffix)
                )

                results = geocoder.get(location)
            
                types = results[0].types

                if 'intersection' not in types:
                    log.info('Geocoded to %s, not intersection: "%s" (%s)' % (unicode(types), location, self.case_number))
                    raise GeocodingError('Google failed to find an intersection matching this location.')
            except (ValueError, GeocodingError):
                try:
                    location = '%s %s %s %s Tyler, TX' % (
                        self.street_number,
                        self.street_prefix,
                        self.street_name,
                        self._normalize_suffix(self.street_suffix)
                    )

                    results = geocoder.get(location)
                
                    types = results[0].types

                    if 'street_address' not in types:
                        log.info('Geocoded to %s, not street_address: "%s" (%s)' % (unicode(types), location, self.case_number))
                        raise GeocodingError('Google failed to find an intersection matching this location.')

                except ValueError:
                    log.info('Failed to geocode: "%s" (%s)' % (location, self.case_number))
                    raise GeocodingError('Failed to geocode.')

            lat = results[0].geometry.location.lat
            lng = results[0].geometry.location.lng

            self.point = Point(lng, lat)
            
            log.info('Successfully geocoded: "%s" (%s)' % (location, self.case_number))
        except GeocodingError:
            self.point = None

        super(ActiveCall, self).save(*args, **kwargs)

