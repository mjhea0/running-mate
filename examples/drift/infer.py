import logging
import pickle
import random

import numpy as np
import pandas as pd  # type: ignore
from joblib import load  # type: ignore
from scipy.stats import ks_2samp  # type: ignore

from mate.alerts import TerminalAlertTarget
from mate.db import connect_db, get_current_mate, get_feature_values
from mate.run import RunningMate
from mate.stats import CustomStats

MATE_NAME = "insurance"

logging.basicConfig(level=logging.INFO)


# create alert targets
alert_targets = [
    TerminalAlertTarget(),
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

    # add a number of inferences
    for _ in range(101):
        with RunningMate(
            MATE_NAME, version, df, [], should_save_all_feature_values=True
        ):
            df["age"] = random.randint(65, 90)  # all values will be above the max stat
            model.predict(enc.transform(df))

    feature_values = get_feature_values(current_mate)
    ages = [f.value for f in feature_values]
    age_predictions = np.array(ages)

    if (
        float(ks_2samp(X["age"].values, age_predictions).pvalue) < 0.05
    ):  # drift detection
        df["age"] = random.randint(65, 90)
        # custom stats (generates an error alert)
        with RunningMate(
            MATE_NAME,
            version,
            df,
            alert_targets,
            custom_stats=[CustomStats("drift", "age")],
        ):
            model.predict(enc.transform(df))
