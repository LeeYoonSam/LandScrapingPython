# -*- coding: utf-8 -*-

import requests
import re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os
from enum import Enum

# DEF_TRADING_LAND_URL = "http://land.naver.com/article/articleList.nhn?rletTypeCd=A01&tradeTypeCd=A1&hscpTypeCd=A01&rletNo=110747"
# DEF_CHARTER_LAND_URL = "http://land.naver.com/article/articleList.nhn?rletTypeCd=A01&tradeTypeCd=B1&hscpTypeCd=A01&rletNo=110747"


BASE_LAND_URL = "http://land.naver.com/article/articleList.nhn?rletTypeCd=A01&tradeTypeCd={}&hscpTypeCd=A01&rletNo=110747"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TradeType(Enum):
    all = ''            # 전체
    trading = 'A1'      # 매매
    charter = 'B1'      # 전세
    month_rent = 'B2'   # 월세
    short_rent = 'B3'   # 단기임대


class AllLand:
    def __init__(self):
        self.allLand = []

    def append_land(self, landData):
        self.allLand.append(landData)

    def get_json_all_land(self):
        jsonDump = {}
        for i, landData in enumerate(self.allLand):
            jsonDump[i] = landData.__dict__

        return jsonDump


class LandData:
    def __init__(self, deal, date, scene_name, name, supply_area, exclusive_area, dong, floor, price, contact):
        self.deal = deal
        self.date = date.__str__()
        self.scene_name = scene_name
        self.name = name
        self.supply_area = supply_area
        self.exclusive_area = exclusive_area
        self.dong = dong
        self.floor = floor
        self.price = price
        self.contact = contact

def startScraping(scrapingURL, tradeType):

    newScrapingURL = scrapingURL.format(tradeType.value)
    count = getPageCount(newScrapingURL)

    allLand = AllLand()

    for page in range(count):
        NewURL = newScrapingURL + '&page=' + str(page + 1)

        r = requests.get(NewURL)
        soup = BeautifulSoup(r.text, 'lxml')

        table = soup.find('table')
        trs = table.tbody.find_all('tr')

        # allLand = AllLand()

        for tr in trs[::2]:
            tds = tr.find_all('td')

            cols = [' '.join(td.text.strip().split()) for td in tds]

            if '_thumb_image' not in tds[2]['class']:
                cols.insert(2, '')

            deal = cols[0]
            date = datetime.strptime(cols[1], '%y.%m.%d.')

            data3 = cols[3].split(' ')

            if data3[0] == '현장확인':
                scene_name = data3[0]
                name = data3[1]
            else:
                scene_name = ''
                name = data3[0]


            areas = cols[4]

            supply_area_list = re.findall('공급면적(.*?)㎡', areas)
            exclusive_list = re.findall('전용면적(.*?)㎡', areas)

            supply_area = 0
            if len(supply_area_list) > 0:
                supply_area = supply_area_list[0].replace(',', '')

            exclusive_area = 0
            if len(exclusive_list) > 0:
                exclusive_area = exclusive_list[0].replace(',', '')

            supply_area = float(supply_area)
            exclusive_area = float(exclusive_area)

            dong = cols[5]
            floor = cols[6]

            try:
                price = int(cols[7].replace(',', ''))
            except:
                price = 0

            contact = cols[8]

            resultDir = os.path.join(BASE_DIR, "Results")
            if not os.path.exists(resultDir):
                os.makedirs(resultDir)

            now = datetime.now()

            fileName = now.strftime('%y%m%d%T')

            landData = LandData(deal, date, scene_name, name, supply_area, exclusive_area, dong, floor, price, contact)

            allLand.append_land(landData)
            # print(json.dumps(landData.__dict__, ensure_ascii=False))


    with open(os.path.join(resultDir, fileName + "_" + tradeType.name + '_result.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(allLand.get_json_all_land(), json_file, ensure_ascii=False, sort_keys=True, indent=4)


def getPageCount(checkUrl):
    req = requests.get(checkUrl)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')

    div_content = soup.find("div", {"class": "paginate"})

    count = 0

    for page in div_content.text:
        if isNumber(page):
            count = count + 1

    return count


def isNumber(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def html_parser_scraping():
    req = requests.get(DEF_LAND_URL)
    html = req.text
    soup = BeautifulSoup(html, 'html.parser')
    # CSS Selector를 통해 html요소들을 찾아낸다.
    my_titles = soup.select(
        'tbody > tr'
    )

    data = {}

    # L[::2] - 2스텝씩 진행 ex) 2, 4, 6, ... / L[1::2] - 1부터 시작해서 2스텝씩 진행 ex) 1, 3, 5, ...
    # 2개의 tr이 한개의 부동산건이라서 2스텝씩 진행
    for i, title in enumerate(my_titles[::2]):
        data[i] = title.text

    jsonData = {}
    for i, items in enumerate(data):
        jsonData[i] = data[items].split()


    resultDir = os.path.join(BASE_DIR, "Results")
    if not os.path.exists(resultDir):
        os.makedirs(resultDir)

    now = datetime.now()

    fileName = now.strftime('%y%m%d')

    with open(os.path.join(resultDir, fileName + '_result.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(jsonData, json_file, ensure_ascii=False,  sort_keys=True, indent=4)



# if __name__ == "__main__": html_parser_scraping()
if __name__ == "__main__":
    startScraping(BASE_LAND_URL, TradeType.trading)
    startScraping(BASE_LAND_URL, TradeType.charter)