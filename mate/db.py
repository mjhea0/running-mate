import datetime
import logging
import os
import pathlib
from typing import List, Union

from peewee import (  # type: ignore
    CharField,
    DatabaseProxy,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
)

logger = logging.getLogger("mate")


db = DatabaseProxy()


class Mate(Model):
    name = CharField()
    version = IntegerField()
    item_count = IntegerField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        table_name = "mate"


class Inference(Model):
    mate = ForeignKeyField(Mate)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        table_name = "inference"


class Feature(Model):
    name = CharField()
    inferred_type = CharField()
    mate = ForeignKeyField(Mate)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        table_name = "feature"


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
        table_name = "numerical_stats"


class StringStats(Model):
    num_present = IntegerField()
    num_missing = IntegerField()
    distinct_count = IntegerField()
    feature = ForeignKeyField(Feature)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        table_name = "string_stats"


class FeatureValue(Model):
    value = CharField(null=True)
    feature = ForeignKeyField(Feature)
    inference = ForeignKeyField(Inference)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        table_name = "feature_value"


class FeatureAlert(Model):
    name = CharField()
    kind = CharField()
    feature_value = ForeignKeyField(FeatureValue)
    feature = ForeignKeyField(Feature)
    inference = ForeignKeyField(Inference)

    class Meta:
        database = db
        table_name = "feature_alert"


def connect_db():
    db = init_db()
    db.connect()

    if (
        not db.table_exists("mate")
        or not db.table_exists("inference")
        or not db.table_exists("feature")
        or not db.table_exists("numerical_stats")
        or not db.table_exists("string_stats")
        or not db.table_exists("feature_alert")
        or not db.table_exists("feature_value")
    ):
        db.create_tables(
            [
                Mate,
                Inference,
                Feature,
                NumericalStats,
                StringStats,
                FeatureValue,
                FeatureAlert,
            ]
        )


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


def init_db() -> SqliteDatabase:
    test_mode = int(os.getenv("TESTING", "0"))

    if test_mode:
        database = SqliteDatabase(":memory:")
        logger.info("Using in-memory SQLite")
    else:
        BASE = pathlib.Path.cwd()
        database = SqliteDatabase(BASE / "mate.db")
        logger.info("Using disk-based SQLite")

    db.initialize(database)

    return db


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
