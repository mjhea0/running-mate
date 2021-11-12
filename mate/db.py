import datetime
import logging
from typing import List, Union

from peewee import (  # type: ignore
    CharField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
)

db = SqliteDatabase("mate.db")

logger = logging.getLogger("mate")


class Mate(Model):
    name = CharField()
    version = IntegerField()
    item_count = IntegerField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class Feature(Model):
    name = CharField()
    inferred_type = CharField()
    mate = ForeignKeyField(Mate)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class NumericalStats(Model):
    num_present = IntegerField()
    num_missing = IntegerField()
    mean = FloatField()
    sum = IntegerField()
    std_dev = FloatField()
    min = IntegerField()
    max = IntegerField()
    feature = ForeignKeyField(Feature)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class StringStats(Model):
    num_present = IntegerField()
    num_missing = IntegerField()
    distinct_count = IntegerField()
    feature = ForeignKeyField(Feature)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class FeatureAlert(Model):
    name = CharField()
    kind = CharField()
    value = CharField(null=True)
    feature = ForeignKeyField(Feature)

    class Meta:
        database = db


def create_db():
    db.connect()
    if (
        not db.table_exists("mate")
        or not db.table_exists("feature")
        or not db.table_exists("numericalstats")
        or not db.table_exists("stringstats")
        or not db.table_exists("featurealert")
    ):
        db.create_tables([Mate, Feature, NumericalStats, StringStats, FeatureAlert])


def get_current_mate(name: str) -> Union[Mate, None]:
    mate = Mate.select().where(Mate.name == name).order_by(Mate.version.desc()).limit(1)

    if mate:
        return mate[0]

    return None


def get_features(mate: Mate) -> List[Feature]:
    features = Feature.select().where(Feature.mate == mate)

    return features


def get_statistics(Stats: Model, feature: Feature) -> Model:
    return Stats.get(feature=feature)


def version_or_create_mate(name: str) -> Mate:
    current_mate = get_current_mate(name)

    if current_mate:
        version = int(current_mate.version) + 1
        logger.info(f"Model found. Creating new version: {version}.")
    else:
        version = 1
        logger.info("Model not found. Creating new mate.")

    mate = Mate(name=name, version=version)
    mate.save()

    return mate
