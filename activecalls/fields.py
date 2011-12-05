#!/usr/bin/env python

from django.utils import simplejson

from tastypie.fields import ApiField

class GeometryApiField(ApiField):
    """
    Custom ApiField for dealing with data from GeometryFields (by serializing them as GeoJSON) .
    """
    dehydrated_type = 'geometry'
    help_text = 'Geometry data.'
    
    def dehydrate(self, obj):
        return self.convert(super(GeometryApiField, self).dehydrate(obj))
    
    def convert(self, value):
        if value is None:
            return None

        if isinstance(value, dict):
            return value

        # Get ready-made geojson serialization and then convert it _back_ to a Python object
        # so that Tastypie can serialize it as part of the bundle
        return simplejson.loads(value.geojson)

