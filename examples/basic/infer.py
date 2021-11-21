import logging
import pickle

import pandas as pd  # type: ignore
from joblib import load  # type: ignore

from mate.alerts import AlertWebhookTarget, TerminalAlertTarget
from mate.db import connect_db, get_current_mate
from mate.run import RunningMate
from mate.stats import CustomStats

MATE_NAME = "insurance"

logging.basicConfig(level=logging.INFO)


# create alert targets
alert_targets = [
    TerminalAlertTarget(),
    AlertWebhookTarget("http://localhost:5000/hook"),
]

# load sample data
df = pd.read_csv("../_data/insurance_infer.csv", sep=",")

df_2 = pd.read_csv(f"../_data/{MATE_NAME}.csv", sep=",")
X = df_2.drop(["charges"], axis=1)

# load mate
connect_db()
current_mate = get_current_mate(MATE_NAME)

if current_mate:
    version = current_mate.version

    model = load(f"models/{MATE_NAME}-{version}.joblib")
    with open(f"models/{MATE_NAME}-encoder-{version}.pickle", "rb") as f:
        enc = pickle.load(f)

    # valid data (no alerts)
    with RunningMate(
        MATE_NAME, version, df, alert_targets, should_save_all_feature_values=True
    ):
        model.predict(enc.transform(df))

    # insert sample invalid (below minimum bound) value
    df["age"] = -1

    # invalid data (generates an error alert)
    with RunningMate(MATE_NAME, version, df, alert_targets):
        model.predict(enc.transform(df))

    # custom stats (generates an error alert)
    with RunningMate(
        MATE_NAME,
        version,
        df,
        alert_targets,
        custom_stats=[CustomStats("drift", "age")],
    ):
        model.predict(enc.transform(df))
