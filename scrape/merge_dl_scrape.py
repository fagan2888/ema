"""
Download indication excel file from ema
run scrap.py to scrape htmls tables

We need the ATC and indications columns from the excel file
"""

import pandas as pd

DATA_DIR = "../data"

df_xls = pd.read_excel("ema_indications_dl.xls", skiprows=10)
df_scrape = pd.read_csv("ema_scrape.csv")

df_scrape['atc'] = df_xls['Atc code']
df_scrape['emea'] = df_xls['Product Number']
df_scrape['indication'] = df_xls['Indication']

df_scrape.to_csv("ema_indications_merged.csv")