# -*- coding: utf-8 -*-
"""
Models needed for the representation of a map
"""
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _


class MapManager(models.Manager):
    """
    Manager for Maps
    replaces objects in Class Map
    """
    def all(self):
        """
        :return: all Maps
        """
        # pylint: disable=no-member
        return self.get_queryset()

    def public(self):
        """
        :return: all public Maps
        """
        # pylint: disable=no-member
        qs = self.get_queryset()
        return qs.filter(public=True)


class Map(models.Model):
    """
    Class representing the Maps generated with aktionskarten-frontend
    (https://github.com/KartographischeAktion/aktionskarten-frontend)

    name: name of the Map used in title and url (unique identifier)
    bbox: the bounding box of the Map
        all features need to be in the bbox
        exported map will only show content of bbox
    public: indicates whether the map is publicly visible
    editable: indicates whether the map is publicly editable
    """
    name = models.CharField(_(u'name'), max_length=50, primary_key=True)
    bbox = models.PolygonField(_(u'bounding box'))
    public = models.BooleanField(_(u'public'), default=False)
    editable = models.BooleanField(_(u'editable'), default=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    objects = MapManager()


class Feature(models.Model):
    """
    Class representing the Features of a map

    geo: the type of the Feature i.e. Point, Polygon, etc
    map: the Map the feature belongs to
    """

    def __str__(self):
        return u'Feature #' + str(self.id) + u' for map: ' + str(self.map)

    def __unicode__(self):
        return u'Feature #' + str(self.id) + u' for map: ' + str(self.map)

    geo = models.GeometryField(u'')
    map = models.ForeignKey(Map, related_name=u'features')
