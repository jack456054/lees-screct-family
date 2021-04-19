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


def get_currency_bot(currency_attr: str) -> str:
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


def get_currency_hsbc(currency_attr: str) -> str:
    url = 'https://www.apps1.asiapacific.hsbc.com/1/2/Misc/popup-tw/currency-calculator'
    res = pd.read_html(url)
    df = res[1]
    currency = df.iloc[3:, :5]
    currency.columns = [u'幣別', u'即期匯率-本行買入', u'即期匯率-本行賣出', u'現金匯率-本行買入', u'現金匯率-本行賣出']
    currency = currency.set_index(u'幣別')
    currency = currency.filter(like=currency_attr, axis=0)
    buy_price = currency.iloc[0][u'即期匯率-本行買入']
    currency = currency.T.to_csv()
    currency = list(csv.reader(StringIO(currency)))
    del currency[0]
    currency = tabulate(currency, tablefmt='plain')
    time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("資料抓取時間：%m/%d/%Y, %H:%M:%S")
    source = '資料來源：HSBC'
    currency_type = f'幣別：{currency_attr}'
    currency = f'''

{currency_type}
{currency}

{time}
{source}
'''
    return currency, buy_price


def check_direct_buy(buy_price_usd: float, buy_price_cny: float) -> str:
    c_n_ratio = buy_price_cny / buy_price_usd
    return f'''
即期匯率-本行買入(CYN)/ 即期匯率-本行買入(USD) = {c_n_ratio}

* USD 買價 > {1 / c_n_ratio}(CNY)
應直接換匯 CNY -> NTD

* USD 買價 < {1 / c_n_ratio}(CNY)
應換匯兩次 CNY -> USD -> NTD
'''


if __name__ == '__main__':
    token = os.environ.get('TOKEN')
    # token = TOKEN
    # send_notify(token=token, msg=get_currency_bot('USD'))
    # send_notify(token=token, msg=get_currency_bot('CNY'))
    currency, buy_price_usd = get_currency_hsbc('USD')
    send_notify(token=token, msg=currency)
    currency, buy_price_cny = get_currency_hsbc('CNY')
    send_notify(token=token, msg=currency)
    msg = check_direct_buy(float(buy_price_usd), float(buy_price_cny))
    send_notify(token=token, msg=msg)
