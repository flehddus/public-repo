from fastmcp import FastMCP
import pandas as pd
import numpy as np
import requests
import matplotlib as plt
import json
from collections import OrderedDict

mcp = FastMCP("riot-mcp-http")
api_key = ""
requesturl_items = "https://ddragon.leagueoflegends.com/cdn/15.22.1/data/ko_KR/item.json"
requesturl_champions = "https://ddragon.leagueoflegends.com/cdn/15.22.1/data/ko_KR/champion.json"
requesturl_summoners = "https://ddragon.leagueoflegends.com/cdn/15.22.1/data/ko_KR/summoner.json"

@mcp.tool
def get_puuid(user_name: str, user_tag: str) -> str:
    """Get puuid from Riot API using username and tag"""
    requesturl = "https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"+user_name+"/"+user_tag+"?api_key="+api_key
    r = requests.get(requesturl)
    
    return r.json()['puuid']

@mcp.tool
def recent_matches(puuid: str, game_type: str, game_count: int) -> list:
    """Get recent match IDs from Riot API using puuid"""
    requesturl = "https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/"+puuid+"/ids?type="+game_type+"&start=0&count="+game_count+"&api_key="+api_key
    r = requests.get(requesturl)

    return r.json()

@mcp.tool
def match_win_rate(puuid: str, game_type: str, game_count: int) -> dict:
    """Get match win rate from Riot API using puuid"""
    requesturl = "https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/"+puuid+"/ids?type="+game_type+"&start=0&count="+game_count+"&api_key="+api_key
    r = requests.get(requesturl)

    # 승리 횟수
    win_count = 0

    for i in range(len(r.json())):
        match_requesturl = "https://asia.api.riotgames.com/lol/match/v5/matches/"+r.json()[i]+"?api_key="+api_key
        match_r = requests.get(match_requesturl)

        # 몇번째 참가자인지 확인
        participant_index = 0
        for j in range(10):
            if (match_r.json()['info']['participants'][j]['puuid']) == puuid:
                participant_index = j
                break

        if match_r.json()['info']['participants'][participant_index]['win']:
            win_count += 1

    match_win_rate = OrderedDict()
    match_win_rate["total_matches"] = len(r.json())
    match_win_rate["win_count"] = win_count
    match_win_rate["win_rate_percentage"] = round((win_count/len(r.json()))*100, 2)

    return match_win_rate

@mcp.tool
def match_result(match_id: str, puuid: str) -> dict:
    """Get match result from Riot API using match ID and puuid"""
    requesturl = "https://asia.api.riotgames.com/lol/match/v5/matches/"+match_id+"?api_key="+api_key
    r = requests.get(requesturl)
    r_items = requests.get(requesturl_items)
    r_champions = requests.get(requesturl_champions)
    r_summoners = requests.get(requesturl_summoners)

    # 몇번째 참가자인지 확인
    participant_index = 0
    for i in range(10):
        if (r.json()['info']['participants'][i]['puuid']) == puuid:
            participant_index = i
            break
    # 해당 참가자의 정보
    r.json()['info']['participants'][participant_index]

    # 챔피언 한글 이름
    champion_name = r.json()['info']['participants'][participant_index]['championName']
    champion_name_ko = r_champions.json()['data'][champion_name]['name']

    # 소환사 스펠 한글 이름
    summoner1_id = r.json()['info']['participants'][participant_index]['summoner1Id']
    summoner2_id = r.json()['info']['participants'][participant_index]['summoner2Id']
    summoner1_name_ko = ""
    summoner2_name_ko = ""
    for key in r_summoners.json()['data'].keys():
        if r_summoners.json()['data'][key]['key'] == str(summoner1_id):
            summoner1_name_ko = r_summoners.json()['data'][key]['name']
        if r_summoners.json()['data'][key]['key'] == str(summoner2_id):
            summoner2_name_ko = r_summoners.json()['data'][key]['name']

    # 아이템 한글 이름
    item_names_ko = []
    ward_name_ko = ""
    for i in range(7):
        item_id = str(r.json()['info']['participants'][participant_index]['item'+str(i)])
        if i < 6:
            if item_id != '0':
                item_name_ko = r_items.json()['data'][item_id]['name']
                item_names_ko.append(item_name_ko)
            else:
                continue
            
        else:
            ward_name_ko = r_items.json()['data'][item_id]['name']

    match_result = OrderedDict()
    match_result["game_mode"] = r.json()['info']['gameMode']
    match_result["game_duration_minutes"] = r.json()['info']['gameDuration']//60
    match_result["game_duration_seconds"] = r.json()['info']['gameDuration']%60
    match_result["match_id"] = r.json()['metadata']['matchId']
    match_result["summoner_name"] = r.json()['info']['participants'][participant_index]['riotIdGameName'] + "#" + r.json()['info']['participants'][participant_index]['riotIdTagline']
    match_result["champion"] = champion_name_ko
    match_result["champion_level"] = r.json()['info']['participants'][participant_index]['champLevel']
    match_result["kills"] = r.json()['info']['participants'][participant_index]['kills']
    match_result["deaths"] = r.json()['info']['participants'][participant_index]['deaths']
    match_result["assists"] = r.json()['info']['participants'][participant_index]['assists']
    match_result["gold_earned"] = r.json()['info']['participants'][participant_index]['goldEarned']
    match_result["items"] = item_names_ko
    match_result["ward"] = ward_name_ko
    match_result["spells"] = summoner1_name_ko + "(D), " + summoner2_name_ko + "(F)"
    match_result["kill_participation_rate"] = round((r.json()['info']['participants'][participant_index]['kills'] +
                                    r.json()['info']['participants'][participant_index]['assists']) /
                                   (r.json()['info']['teams'][r.json()['info']['participants'][participant_index]['teamId']//100]['objectives']['champion']['kills']
                                    ), 2)
    if r.json()['info']['participants'][participant_index]['win']:
        match_result["win"] = True
    else:
        match_result["win"] = False
    match_result["total_minions_killed"] = r.json()['info']['participants'][participant_index]['totalMinionsKilled']
    match_result["neutral_minions_killed"] = r.json()['info']['participants'][participant_index]['neutralMinionsKilled']
    match_result["totalDamageDealtToChampions"] = r.json()['info']['participants'][participant_index]['totalDamageDealtToChampions']
    match_result["totalDamageTaken"] = r.json()['info']['participants'][participant_index]['totalDamageTaken']
    match_result["wardsPlaced"] = r.json()['info']['participants'][participant_index]['wardsPlaced']
    match_result["wardsKilled"] = r.json()['info']['participants'][participant_index]['wardsKilled']
    match_result["individualPosition"] = r.json()['info']['participants'][participant_index]['individualPosition']

    return match_result

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
    #mcp.run()