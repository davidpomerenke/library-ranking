import json
import pandas as pd
import re


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
    libraries = [d for d in data if d["uni"] == uni]
    times = [(library["name"], calc_times(library)) for library in libraries]
    times = [t for t in times if t[1] is not None]
    lib, time = max(times, key=lambda x: x[1], default=("-", 0))  # type: ignore
    ranking.append({"uni": uni, "library": lib, "open_time": time})

# library open time ranking

df = pd.DataFrame(ranking)
df = df.sort_values(by="open_time", ascending=False)
df["rank"] = df["open_time"].rank(ascending=False, method="min")
df["rank"] = df["rank"].apply(round)
df["open_time"] = df["open_time"].apply(lambda s: f"{round(s*100)/100:.2f}")
cols = df.columns.to_list()
df = df[[cols[-1], *cols[:-1]]]


def get_rank(uni):
    rank = qs[qs["Institution Name"] == uni].iloc[0]["RANK"]
    if isinstance(rank, float):
        if pd.isna(rank):
            print(uni, rank)
            return None
        rank = int(rank)
    if isinstance(rank, str):
        rank = rank.strip(" =")
        if "-" in rank:
            rank = rank.split("-")[0]
    return str(int(rank))


qs = pd.read_excel("data_in/2023 QS World University Rankings V2.1.xlsx")
df["qs_rank"] = df["uni"].apply(get_rank)
df["uni"] = df["uni"].apply(lambda s: s.strip())
df.to_csv("data_out/ranking.csv", index=False)
