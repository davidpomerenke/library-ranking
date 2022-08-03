import json
from statistics import mean
import pandas as pd


with open("data_out/data.json") as f:
    data = json.load(f)

print(len(data))
print(
    len([d for d in data if "opening_hours" in d and "periods" in d["opening_hours"]])
)


def parse_hour(time):
    assert len(time) == 4
    h = int(time[:2])
    min = int(time[2:])
    return h + min / 60


def parse_period(period):
    open = period["open"]["day"] * 24 + parse_hour(period["open"]["time"])
    close = period["close"]["day"] * 24 + parse_hour(period["close"]["time"])
    week = 24 * 7
    return ((close - open) % week) / week


def calc_times(entry):
    if not "opening_hours" in entry:
        return None
    oh = entry["opening_hours"]
    if not "periods" in oh:
        return None
    periods = oh["periods"]
    always_open_convention = [{"open": {"day": 0, "time": "0000"}}]
    if periods == always_open_convention:
        return 1
    return sum([parse_period(period) for period in periods])


ranking = []
unis = set(d["uni"] for d in data)
for uni in unis:
    libraries = [
        {
            "uni": uni,
            "library": d["name"],
            "gmaps_rating_original": d["rating"] if "rating" in d else None,
            "gmaps_rating_count": d["user_ratings_total"]
            if "user_ratings_total" in d
            else None,
            "opening_hours": calc_times(d),
        }
        for d in data
        if d["uni"] == uni and calc_times(d) is not None
    ]
    if len(libraries) > 0:
        lib = max(libraries, key=lambda x: x["opening_hours"])
        ranking.append(lib)

# library open time ranking

df = pd.DataFrame(ranking)

df["opening_hours"] = df["opening_hours"].apply(lambda s: f"{round(s*100)/100:.2f}")

df["rank"] = df["opening_hours"].rank(ascending=False, method="min")
df["rank"] = df["rank"].apply(round)
cols = df.columns.to_list()
df = df[[cols[-1], *cols[:-1]]]


def get_rank(uni):
    rank = qs[qs["Institution Name"] == uni].iloc[0]["RANK"]
    if isinstance(rank, int):
        return str(rank)
    if isinstance(rank, float):
        if pd.isna(rank):
            return "?"
        rank = int(rank)
    if isinstance(rank, str):
        rank = rank.strip(" =+")
        if "-" in rank:
            rank = rank.split("-")[0]
    return str(int(rank))


# add qs ranks

qs = pd.read_excel("data_in/2023 QS World University Rankings V2.1.xlsx")
df["qs_rank"] = df["uni"].apply(get_rank)
df["uni"] = df["uni"].apply(lambda s: s.strip())

# bayesian average of gmaps ratings


def bayesian_avg(row):
    c = df["gmaps_rating_count"].quantile(0.25)
    prior = df["gmaps_rating_original"].mean()
    avg = (row["gmaps_rating_original"] * row["gmaps_rating_count"] + prior * c) / (
        row["gmaps_rating_count"] + c
    )
    if pd.isna(avg):
        return None
    return avg


def stretch(x):
    if pd.isna(x):
        return x
    min = df["gmaps_rating"].min()
    max = df["gmaps_rating"].max()
    return round(((x - min) / (max - min) * 4 + 1) * 10) / 10


df["gmaps_rating"] = df.apply(bayesian_avg, axis=1)
df["gmaps_rating"] = df["gmaps_rating"].apply(stretch)

df = df.sort_values(by=["opening_hours", "gmaps_rating"], ascending=[False, False])
df.to_csv("data_out/ranking.csv", index=False)

df = df[df["qs_rank"] != "?"]
df["qs_rank"] = df["qs_rank"].astype(float)
df["qs_rank"].hist()
import matplotlib.pyplot as plt

plt.show()
