import dotenv
import json
import pandas as pd
import os
import requests

dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

payload = {}
headers = {}

with open("data_out/data.json") as f:
    data = json.load(f)


def get_details(place_id, uni):
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
    response = requests.request("GET", url, headers=headers, data=payload).json()[
        "result"
    ]
    response["uni"] = uni
    data.append(response)


def get_info(uni):
    query = f"{uni} Library"
    fields = ",".join(["name", "user_ratings_total", "place_id"])

    url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields={fields}&key={GOOGLE_API_KEY}&language=en"

    response = requests.request("GET", url, headers=headers, data=payload).json()
    print(uni)
    if len(response["candidates"]) == 0:
        print(f"\t0 results!")
    elif len(response["candidates"]) > 0:
        if len(response["candidates"]) > 1:
            print(f"\t{len(response['candidates'])} results!")
        for candidate in response["candidates"]:
            get_details(candidate["place_id"], uni)


df = pd.read_excel("data/2023 QS World University Rankings V2.1.xlsx")

for uni in list(df["Institution Name"])[:750]:
    if uni not in {d["uni"] for d in data}:
        get_info(uni)

with open("data_out/data.json", "w") as f:
    json.dump(data, f, indent=2)
