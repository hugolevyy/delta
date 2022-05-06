import requests
import pandas as pd
import time
import json

class RiotAccess:

    RIOT_API_KEY = "RGAPI-a109608f-8d8c-4742-b4c1-cae077519e09"
    EU_RIOT_MATCH_ENDPOINT = "https://europe.api.riotgames.com/lol/match/v5/matches/"
    ASIA_RIOT_MATCH_ENDPOINT="https://asia.api.riotgames.com/lol/match/v5/matches/"
    NA_RIOT_MATCH_ENDPOINT="https://americas.api.riotgames.com/lol/match/v5/matches/"
    MATCH_ID_PATH = "MatchesID/games.csv"

    END_POINT_MATCH = {"BR1":NA_RIOT_MATCH_ENDPOINT,
                       "LA1":NA_RIOT_MATCH_ENDPOINT,
                       "EUN1":EU_RIOT_MATCH_ENDPOINT,
                       "EUW1":EU_RIOT_MATCH_ENDPOINT,
                       "LA2":NA_RIOT_MATCH_ENDPOINT,
                       "NA1":NA_RIOT_MATCH_ENDPOINT,
                       "TR1":ASIA_RIOT_MATCH_ENDPOINT,
                       "KR":ASIA_RIOT_MATCH_ENDPOINT,
                       "JP1":ASIA_RIOT_MATCH_ENDPOINT,
                       "OC1":NA_RIOT_MATCH_ENDPOINT,
                       "RU":EU_RIOT_MATCH_ENDPOINT}



    REQUEST_SLEEP_TIME = 0.5

    def __init__(self):
        self.headers = {"X-Riot-Token": self.RIOT_API_KEY}

    def get_match_id_info(self, matchID):
        endpoint = self.END_POINT_MATCH[matchID.split("_")[0]]
        try:
            req = requests.get(endpoint+matchID, headers=self.headers)
            return req.json()
        except Exception as e:
            print("[ERROR] get_match_id_info : ", str(e))
            return None

    def save_data_from_source(self, start_id=0,max_id=None):
        try:
            id_file = pd.read_csv(self.MATCH_ID_PATH)
        except:
            print("Couldn't access to the MATCH_ID file. Please check MATCH_ID_PATH is correct /!\\")
            return

        jsonout = {}

        for k,ID in enumerate(id_file['MATCH_ID']):
            if k < start_id:
                continue
            elif max_id is not None and k > max_id:
                break
            data = self.get_match_id_info(ID)
            if data is not None:
                jsonout[ID] = data

            # WAITING TIME BETWEEN REQUESTS
            time.sleep(self.REQUEST_SLEEP_TIME)

        with open('out_data.json', 'w') as f:
            json.dump(jsonout, f)





if __name__ == "__main__": #For debug purposes only
    riot_app = RiotAccess()
    print(riot_app.get_match_id_info("RU_343155688"))
