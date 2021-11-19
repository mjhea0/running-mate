import logging
import pickle

import pandas as pd  # type: ignore
from joblib import dump  # type: ignore
from sklearn.linear_model import LinearRegression  # type: ignore
from sklearn.preprocessing import OneHotEncoder  # type: ignore

from mate.db import connect_db, version_or_create_mate
from mate.generators import generate_baseline_stats

MATE_NAME = "insurance"

logging.basicConfig(level=logging.INFO)


df = pd.read_csv(f"../_data/{MATE_NAME}.csv", sep=",")
new_df = df.copy()
X = new_df.drop(["charges"], axis=1)

# version existing mate/create new mate and generate baseline stats
connect_db()
mate = version_or_create_mate(MATE_NAME)
generate_baseline_stats(X, MATE_NAME)

enc = OneHotEncoder(handle_unknown="ignore")
y = new_df["charges"]
X = new_df.drop(["charges"], axis=1)

# train
X_transform = enc.fit_transform(X)
model = LinearRegression()
model.fit(X_transform, y)

# save model and encoder
dump(model, f"models/{MATE_NAME}-{mate.version}.joblib")

with open(f"models/{MATE_NAME}-encoder-{mate.version}.pickle", "wb") as f:
    pickle.dump(enc, f)
