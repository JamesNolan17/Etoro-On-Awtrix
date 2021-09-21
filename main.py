import copy
import json
import time
import urllib.request

from selenium import webdriver
import requests
import re
import time
from data import *

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"
}

cmd = {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
}

# path = "/Users/home/Documents/PyCharm/EtoroXAwtrix/chromedriver_mac"
path = "/usr/lib/chromium-browser/chromedriver"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0.3 Safari/605.1.15"
url_prefix = f"https://www.etoro.com/zh/people/{account_name}/portfolio/"
url_awtrix = f"http://{awtrix_url}:7000/api/v3/customapp"
url_rate = "http://webforex.hermes.hexun.com/forex/quotelist?code=FOREXUSDCNY&column=Code,Price"
id_app = 10


def get_exchange_rate():
    req = urllib.request.Request(url_rate, headers=header)
    f = urllib.request.urlopen(req)
    html = f.read().decode("utf-8")
    print(html)

    s = re.findall("{.*}", str(html))[0]
    sjson = json.loads(s)
    USDCNY = sjson["Data"][0][0][1] / 10000
    return (float(USDCNY))


def get_profit(stock_type):
    # HEADLESS
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--user-agent=%s' % user_agent)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(executable_path=path, options=options)
    driver.set_window_size(700, 800)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", cmd)
    stock_type = copy.deepcopy(stock_type)
    for stock_name in stock_type.keys():
        driver.get(url_prefix + stock_name)
        time.sleep(10)
        profit_text = driver.find_element_by_class_name("bottom-right-head-cell") \
            .find_element_by_class_name("hat-cell-value").find_element_by_class_name("ng-scope").text
        profit_float = float(profit_text[:-1])
        stock_type[stock_name][1] = profit_float
    print(str(stock_type))
    driver.quit()
    return stock_type


def push_stock_to_awtrix(stock_type):
    text = ""
    total_profit_USD = 0.0
    for stock_name in stock_type.keys():
        total_profit_USD += stock_type[stock_name][0] * stock_type[stock_name][1] * 0.01
    total_profit_CNY = total_profit_USD * get_exchange_rate()
    # Total Profit:
    text += "¥" + str(int(total_profit_CNY))
    print(text)
    data = {
        "name": "Etoro",
        "ID": id_app,
        "force": True,
        "icon": "etoro",
        "moveIcon": False,
        "repeat": 10,
        "text": text,
        "color":[106,173,34]
    }
    r = requests.post(url_awtrix, json=data)
    print("send status: " + str(r.status_code))


while True:
    print(time.asctime( time.localtime(time.time()) ))
    try:
    	push_stock_to_awtrix(get_profit(stock_type))
    	time.sleep(60)
    except Exception as e:
        pass
