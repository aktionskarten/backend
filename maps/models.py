# -*- coding: utf-8 -*-
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _


class MapManager(models.Manager):
    def public(self):
        qs = self.get_queryset()
        return qs.filter(public=True)


class Map(models.Model):
    name = models.CharField(_(u'name'), max_length=50, primary_key=True)
    bbox = models.PolygonField(_(u'bounding box'))
    public = models.BooleanField(_(u'public'), default=False)
    editable = models.BooleanField(_(u'editable'), default=True)

    def __str__(self):
        return self.name

    objects = MapManager()


class Feature(models.Model):
    geo = models.GeometryField(u'')
    map = models.ForeignKey(Map, related_name=u'features')
