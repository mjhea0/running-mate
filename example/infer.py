import logging
import pickle

import pandas as pd  # type: ignore
from joblib import load  # type: ignore

from mate.alerts import AlertWebhookTarget, TerminalAlertTarget
from mate.db import get_current_mate
from mate.run import RunningMate

MATE_NAME = "insurance"

logging.basicConfig(level=logging.INFO)


# create alert targets
alert_targets = [
    TerminalAlertTarget(),
    AlertWebhookTarget("http://localhost:5000/hook"),
]

# load sample data
df = pd.read_csv("data/insurance_infer.csv", sep=",")

# load mate
current_mate = get_current_mate(MATE_NAME)

if current_mate:
    version = current_mate.version

    model = load(f"models/{MATE_NAME}-{version}.joblib")
    with open(f"models/{MATE_NAME}-encoder-{version}.pickle", "rb") as f:
        enc = pickle.load(f)

    # valid data (no alerts)
    with RunningMate(MATE_NAME, version, df, alert_targets):
        output = model.predict(enc.transform(df))

    # insert invalid (below minimum bound) value
    df["age"] = None

    # invalid data (generates an error alert)
    with RunningMate(MATE_NAME, version, df, alert_targets):
        output = model.predict(enc.transform(df))
