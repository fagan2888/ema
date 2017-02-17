import math
import pandas as pd
from bs4 import BeautifulSoup
import requests
import string
import time


def parse_links(html):
    # get EMA #s and urls
    names = dict()
    table = BeautifulSoup(html, 'lxml').find("table", attrs={'class': 'eparResults'})
    for row in table.find_all('tr')[1:]:
        col = row.find_all()
        names[col[0].find('a').text] = col[0].find('a').attrs['href'].rsplit("&")[0]
    return names


def get_letter(letter):
    print("{} page 1".format(letter))
    s = requests.session()
    s.get("http://www.ema.europa.eu/ema/index.jsp")
    url = "http://www.ema.europa.eu/ema/index.jsp?curl=pages%2Fmedicines%2Flanding%2Fepar_search.jsp&mid=&searchTab=" \
          "&alreadyLoaded=true&isNewQuery=true&status=Authorised&status=Withdrawn&status=Suspended&status=Refused&" \
          "startLetter={}&keyword=Enter+keywords&searchType=name&taxonomyPath=&treeNumber=&searchGenericType=generics"
    r = s.get(url.format(letter))
    df = pd.read_html(r.text, attrs={'class': 'eparResults'})[0]
    names = parse_links(r.text)

    pagination_class = BeautifulSoup(r.text, 'lxml').find("div", attrs={'class': 'pagination'})
    if pagination_class is None:
        df['url'] = df['Name'].apply(names.get)
        return df

    pagination = pagination_class.find_all()[1].text
    max_num = int(pagination.split(" ")[-1])
    num_pages = int(math.ceil(max_num / 25))
    time.sleep(1)

    for page in range(2, num_pages + 1):
        print("{} page {}/{}".format(letter, page, num_pages))
        next_url = "http://www.ema.europa.eu/ema/index.jsp?searchType=name&startLetter={}&taxonomyPath=&keyword=" \
                   "Enter+keywords&alreadyLoaded=true&curl=pages%2Fmedicines%2Flanding%2Fepar_search.jsp&status=Authorised&" \
                   "status=Withdrawn&status=Suspended&status=Refused&mid=&searchGenericType=generics&treeNumber=&searchTab=&pageNo={}"
        r = s.get(next_url.format(letter, page))
        df = df.append(pd.read_html(r.text, attrs={'class': 'eparResults'})[0])
        names.update(parse_links(r.text))
        time.sleep(1)

    df = df.reset_index()
    df['url'] = df['Name'].apply(names.get)

    return df

d = {}
for letter in string.ascii_uppercase:
    d[letter] = get_letter(letter)

df = pd.concat(d.values())
df.to_csv("ema_scrape.csv")