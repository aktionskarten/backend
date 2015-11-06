# -*- coding: utf-8 -*-
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

from maps.utils import parse_bbox_string


class Map(models.Model):
    name = models.CharField(_(u'name'), max_length=50)
    bbox = models.PolygonField(_(u'bounding box'))
    public = models.BooleanField(_(u'public'), default=False)
    editable = models.BooleanField(_(u'editable'), default=True)

    def set_bbox(self, bbox_string):
        self.bbox = parse_bbox_string(bbox_string)


class Feature(models.Model):
    geo = models.GeometryField(u'')
    map = models.ForeignKey(Map, related_name=u'features')
