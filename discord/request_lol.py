import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()
api_key = os.environ.get('API_KEY')
region = os.environ.get('region_code')
region_long = os.environ.get('region')

# to load the list of players
with open('players.json', encoding='utf-8') as file:
    players = json.load(file)
list_id = players["list_id"]

# useful to use API
request_headers = {
    "X-Riot-Token": api_key
}

queue_type = [
    'RANKED_SOLO_5x5',
    'RANKED_FLEX_SR'
]


# Based on the api RIOT https://developer.riotgames.com/apis
# You can effortless add other request by consulting the riot documentation

def get_summoner_v4(summonerName: str, header: dict = request_headers, region: str = region):
    try:
        r = requests.get(
            f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summonerName}",
            headers=header
        )
        return r.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(status_code)


def get_rank_player(encryptedSummonerId: str, header: dict = request_headers, region: str = region):
    try:
        r = requests.get(
            f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{encryptedSummonerId}",
            headers=header
        )
        return r.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(status_code)


def get_encryptedSummonerId(summonerName: str, header: dict = request_headers, region: str = region):
    user = get_summoner_v4(summonerName, header, region)
    return user['id']


def get_champion_mastery_v4(encryptedSummonerId: str, region: str = region):
    try:
        r = requests.get(
            f"https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{encryptedSummonerId}",
            headers=request_headers
        )
        return r.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(status_code)


def get_puuid(summonerName: str, header: dict = request_headers, region: str = region):
    user = get_summoner_v4(summonerName, header, region)
    return user['puuid']


def get_matchlist(puuid: str, header: dict = request_headers, region: str = region_long, start: int = 0,
                  count: int = 20,
                  startTime: int = None, endTime=None):
    try:
        if (startTime or endTime) is None:
            r = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}",
                headers=header
            )
        elif endTime is None:
            r = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/" \
                f"ids?startTime={startTime}&start={start}&count={count}",
                headers=header
            )
        else:
            r = requests.get(
                f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/" \
                f"ids?startTime={startTime}&endTime={endTime}&start={start}&count={count}",
                headers=header
            )
        return r.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(status_code)


def get_match_stat(matchId: str, region: str = region_long, header: dict = request_headers):
    """
    Get stats of a match according to the matchId
    :param matchId:
    :param region:
    :param header:
    :return: a dict with statistics
    """
    try:
        r = requests.get(
            f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}",
            headers=header
        )
        return r.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(status_code)


def get_match_timeline(matchId: str, region: str = region_long, header: dict = request_headers):
    try:
        r = requests.get(
            f"https://{region}.api.riotgames.com/lol/match/v5/matches/{matchId}/timeline",
            headers=header
        )
        return r.json()
    except requests.HTTPError as e:
        status_code = e.response.status_code
        print(status_code)


def get_stats_match(json: dict, id: str):
    """
    Extract and return stats of a match according to an id

    :param json:
    :param id:
    :return:
    """
    try:
        data = dict()
        data['duration'] = json['info']['gameDuration']
        data['gameMode'] = json['info']['gameMode']
        participant_data = search_data_match(json['info']['participants'], id)
        data['win'] = participant_data['win']
        data['cs'] = participant_data['totalMinionsKilled']
        data['role'] = participant_data['role']
        data['assists'] = participant_data['assists']
        data['damage'] = participant_data['totalDamageDealtToChampions']
        data['death'] = participant_data['deaths']
        data['champion'] = participant_data['championName']
        data['kill'] = participant_data['kills']
        data['gold'] = participant_data['goldEarned']
        data['name'] = participant_data['summonerName']
        try:
            data['goldMinute'] = participant_data['challenges']['goldPerMinute']
        except:
            data['goldMinute'] = 0.0
        return data
    except Exception as error:
        raise Exception(error.args) from error


def search_data_match(data: dict, id: str):
    """
    Search in data of a match, stats corresponding to a player
    :param data: dict with the stats of one match
    :param id: player id
    :return:
    """
    for participant in data:
        if participant['summonerName'] == id:
            return participant
    raise Exception('participant not found')


def get_list_match(id: str, header: dict = request_headers, region: str = region, startTime: int = None,
                   endTime: int = None, count: int = 20):
    """
    get matchs according to a pseudo
    :param id:
    :param header:
    :param region:
    :return:
    """
    puuid = get_puuid(id, header, region)
    return get_matchlist(puuid, header, startTime=startTime, endTime=endTime, count=count)


def count_win(list_match: list, id: str):
    """
    compute number of win and loss

    :param list_match:
    :param id:
    :return:
    """
    total = len(list_match)
    win = 0
    for match in list_match:
        try:
            stats = get_stats_match(get_match_stat(match), id)
            if stats['win']:
                win += 1
        except:
            # problem, we remove this match of the total
            total -= 1
    return win, total - win


def get_rank(id: str, header: dict = request_headers):
    """
    Convert request to dict to be used
    :param id:
    :param header:
    :return:
    """
    data = dict()
    request = get_rank_player(get_encryptedSummonerId(id, header))
    try:
        stats = request[0]
        for r in request:
            if r['queueType'] == 'RANKED_SOLO_5x5':
                stats = r
        data['success'] = True
        data['type'] = stats['queueType']
        data['tier'] = stats['tier']
        data['rank'] = stats['rank']
        data['win'] = stats['wins']
        data['losses'] = stats['losses']
        data['LP'] = stats['leaguePoints']
        data['name'] = stats['summonerName']
        data['queue'] = stats['queueType']
    except:
        data['success'] = False
    return data


if __name__ == '__main__':
    # few tests
    pseudo = list_id[0]
    get_rank(pseudo)
    puuid = get_puuid(pseudo)
    print(get_matchlist(puuid, count=100))
    for id in list_id:
        print(id)
        print(get_rank(id))
    id_example = list_id[2]
    a = get_summoner_v4(id_example, request_headers)
    b = get_puuid(id_example, request_headers)
    c = get_matchlist(b, request_headers)
    d = get_match_stat(c[0])
