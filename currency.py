import csv
from datetime import datetime, timedelta, timezone
from io import StringIO
# from var.variable import TOKEN
import os

import pandas as pd
import requests
from tabulate import tabulate


def send_notify(token, msg, filepath=None, stickerPackageId=None, stickerId=None):
    payload = {'message': msg}
    headers = {
        "Authorization": "Bearer " + token
    }
    if stickerPackageId and stickerId:
        payload['stickerPackageId'] = stickerPackageId
        payload['stickerId'] = stickerId

    if filepath:
        attachment = {'imageFile': open(filepath, 'rb')}
        print(attachment)
        r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload, files=attachment)
    else:
        print("attachment")
        r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
    return r.status_code, r.text


def get_currency(currency_attr: str) -> str:
    url = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
    res = pd.read_html(url)
    df = res[0]
    currency = df.iloc[:, :5]
    currency.columns = [u'幣別', u'現金匯率-本行買入', u'現金匯率-本行賣出', u'即期匯率-本行買入', u'即期匯率-本行賣出']
    currency[u'幣別'] = currency[u'幣別'].str.extract(r'\((\w+)\)')
    currency = currency.set_index(u'幣別')
    currency = currency.filter(like=currency_attr, axis=0).T.to_csv()
    currency = list(csv.reader(StringIO(currency)))
    del currency[0]
    currency = tabulate(currency, tablefmt='plain')
    time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("資料抓取時間：%m/%d/%Y, %H:%M:%S")
    source = '資料來源：台灣銀行'
    currency_type = f'幣別：{currency_attr}'
    currency = f'''

{currency_type}
{currency}

{time}
{source}
'''

    return currency


if __name__ == '__main__':
    token = os.environ.get('TOKEN')
    send_notify(token=token, msg=get_currency('USD'))
    send_notify(token=token, msg=get_currency('CNY'))
