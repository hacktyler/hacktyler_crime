#!/usr/bin/env python

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

    def save(self, *args, **kwargs):
        geocoder = GoogleGeocoder()

        try:
            if not self.cross_street_name:
                raise GeocodingError('Must have an intersection to geocode.')
            
            location = '%(street_prefix)s %(street_name)s %(street_suffix)s and %(cross_street_name)s %(cross_street_suffix)s Tyler, TX' % model_to_dict(self)

            results = geocoder.get(location)

            if not results:
                raise GeocodingError('Failed to geocode.')

            try:
                types = results[0].types
            except KeyError:
                raise GeocodingError('No first result found.')

            if 'intersection' not in types:
                raise GeocodingError('Google failed to find an intersection matching this location.')

            lat = results[0].geometry.location.lat
            lng = results[0].geometry.location.lng

            self.point = Point(lng, lat)
        except GeocodingError:
            self.point = None

        super(ActiveCall, self).save(*args, **kwargs)

