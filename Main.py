import requests, json, warnings, random
import pandas as pd
from bs4 import BeautifulSoup as bs
from sqlalchemy import create_engine
from time import sleep
from datetime import datetime
from selenium import webdriver

warnings.filterwarnings('ignore')

# 資料庫資訊
acc = 'root'
pwd = '123456'
ip = 'localhost'
db = 'test'
table = 'AWS_EC2_List'
mysql_engine = create_engine(f'mysql+pymysql://{acc}:{pwd}@{ip}/{db}')

# 取得區域與作業系統列表
with open(r"location.txt", 'r', encoding='utf-8') as f:
    l = f.readlines()
TMP = bs(l[0])
location = {x['data-value']:x.text for x in TMP.find_all('div', class_='awsui-select-option awsui-select-option-selectable')}

with open(r"system.txt", 'r', encoding='utf-8') as f:
    l = f.readlines()
TMP = bs(l[0])
system = [x['data-value'] for x in TMP.find_all('div', class_='awsui-select-option awsui-select-option-selectable')]

# 建立欄位名稱
cols = ['price', 'Location', 'Location Chinese', 'Instance Family', 'vCPU', 'Instance Type', 'Memory', 'Storage', 'Network Performance', 'plc:OperatingSystem', 'rateCode', 'License Model']

"""
l : 地區英文名 (api指定值)
name : 地區中文名
s : 系統英文名 (api指定值)
dt : 當前時間，timestamp格式 (api指定值)
"""
# 開始爬蟲，針對每一個地區、每一個作業系統逐一檢查並將資料抓回
for l, name in location.items():
    for s in system:
        print(l, s, end='\r')
        dt = int(datetime.timestamp(datetime.now()))
        
        # 與API聯繫取得資料
        url = f'https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/{l}/{s}/index.json?timestamp={dt}'
        r = requests.get(url)
        
        # 資料由json轉換成dataframe
        data = json.loads(r.content)
        data = data['regions'][l]
        df = pd.DataFrame(data)
        df = df.T
        df['Location Chinese'] = name

        # 只保留指定的欄位
        df = df[cols]

        # 上傳資料庫
        df.to_sql(table, mysql_engine, index=False, if_exists='append', chunksize=1000)

        # 隨機休息，以免造成對方伺服器啟動擋爬蟲機制
        sleep(random.randint(0, 5))