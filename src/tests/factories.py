import factory
import random
from faker.providers import BaseProvider

from models import db, Map, Feature


class SQLAlchemyModelFactory(factory.Factory):

    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = db.session
        session.begin(nested=True)
        obj = model_class(*args, **kwargs)
        session.add(obj)
        session.commit()
        return obj


class BBoxProvider(BaseProvider):
    # roughly draw boxes in germany
    lower_longitude = 7.2
    upper_longitude = 14.5
    lower_latitude = 47.0
    upper_latitude = 53.0

    def bbox(self):
        min_longitude = random.uniform(self.lower_longitude, self.upper_longitude)
        max_longitude = random.uniform(min_longitude, self.upper_longitude)
        min_latitude = random.uniform(self.lower_latitude, self.upper_latitude)
        max_latitude = random.uniform(min_latitude, self.upper_latitude)
        return [min_longitude, min_latitude, max_longitude, max_latitude]


factory.Faker.add_provider(BBoxProvider)


class MapFactory(SQLAlchemyModelFactory):

    class Meta:
        model = Map

    name = factory.Faker('uuid4')
    bbox = factory.Faker('bbox')
