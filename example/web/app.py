import json
from datetime import datetime

from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO  # type: ignore
from peewee import (  # type: ignore
    CharField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)
db = SqliteDatabase("alert.db")


class Alert(Model):
    mate_name = CharField()
    mate_version = IntegerField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class FeatureAlert(Model):
    feature_name = CharField()
    feature_alert_kind = CharField()
    feature_value = CharField()
    alert = ForeignKeyField(Alert)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db


def create_db():
    db.connect()
    if not db.table_exists("alert") or not db.table_exists("featurealert"):
        db.create_tables([Alert, FeatureAlert])


create_db()


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


@app.route("/", methods=["GET"])
def home():
    feature_alerts = FeatureAlert.select().order_by(FeatureAlert.created_at.desc())

    return render_template("home.html", feature_alerts=feature_alerts)


@app.route("/hook", methods=["POST"])
def hook():
    data = request.json

    alert = Alert(mate_name=data["mate_name"], mate_version=data["mate_version"])
    alert.save()

    for feature in data["features"]:
        FeatureAlert.create(
            feature_name=feature["feature_name"],
            feature_alert_kind=feature["feature_alert_kind"],
            feature_value=feature["feature_value"],
            alert=alert,
        )

    feature_alerts = FeatureAlert.select().order_by(FeatureAlert.created_at.desc())

    output = []

    for feature_alert in feature_alerts:
        output.append(
            {
                "id": feature_alert.id,
                "mate_name": feature_alert.alert.mate_name,
                "mate_version": feature_alert.alert.mate_version,
                "feature_name": feature_alert.feature_name,
                "feature_alert_kind": feature_alert.feature_alert_kind,
                "feature_value": feature_alert.feature_value,
                "created_at": (feature_alert.created_at).strftime("%Y-%m-%d %H:%M"),
            }
        )

    socketio.emit("update", {"feature_alerts": output})

    return Response(status=201)


if __name__ == "__main__":
    socketio.run(app)
