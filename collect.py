import dotenv
import json
import logging
import pandas as pd
import os
import requests

dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

payload = {}
headers = {}

with open("data.json") as f:
    data = json.load(f)


def get_details(place_id, query):
    fields = ",".join(
        [
            "name",
            "formatted_address",
            "opening_hours",
            "business_status",
            "rating",
            "user_ratings_total",
            "website",
        ]
    )
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields={fields}&key={GOOGLE_API_KEY}&language=en"
    response = requests.request("GET", url, headers=headers, data=payload).json()
    response["query"] = query
    data.append(response)


def get_info(query):
    fields = ",".join(["name", "user_ratings_total", "place_id"])

    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields={fields}&key={GOOGLE_API_KEY}&language=en"

    response = requests.request("GET", url, headers=headers, data=payload).json()
    if len(response["candidates"]) == 0:
        logging.warn(f"{query} had 0 results")
    elif len(response["candidates"]) > 0:
        if len(response["candidates"]) > 1:
            logging.warn(f"{query} had {len(response['candidates'])} results")
        for candidate in response["candidates"]:
            get_details(candidate["place_id"], query)


df = pd.read_csv("data/2023 QS World University Rankings V2.1.csv")

for query in list(df["Institution Name"])[:2]:
    if query not in {d["query"] for d in data}:
        get_info(query)

with open("data.json", "w") as f:
    json.dump(data, f)
