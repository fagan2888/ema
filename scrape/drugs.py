"""
attempt to match drugs
"""

import os
import pandas as pd
import pickle
from wikidataintegrator import wdi_helpers, wdi_core

from ema.utils import get_mixture_rxcui_from_parts

DATA_DIR = "../data"

def get_drug_qid_map():
    # https://github.com/sebotic/wikidata_notebooks/blob/master/ema_annotations.ipynb
    drug_query = '''
    SELECT ?compound ?label ?who_name (GROUP_CONCAT(DISTINCT(?alias); separator="|") AS ?aliases) WHERE {{
      {{?compound wdt:P31 wd:Q11173 .}} UNION  # chemical compound
      {{?compound wdt:P31 wd:Q12140 .}} UNION  # pharmaceutical drug
      {{?compound wdt:P31 wd:Q79529 .}} UNION  # chemical substance
      {{?compound wdt:P2275 ?who_name FILTER (LANG(?who_name) = "en") .}}

      OPTIONAL {{
        ?compound rdfs:label ?label FILTER (LANG(?label) = "en") .
      }}
      OPTIONAL {{
        ?compound skos:altLabel ?alias FILTER (LANG(?alias) = "en") .
      }}
    }}
    GROUP BY ?compound ?label ?who_name ?aliases
    OFFSET {0}
    LIMIT 100000
    '''
    drug_qid_map = {}
    cc = 0
    while True:
        print(cc)
        r = wdi_core.WDItemEngine.execute_sparql_query(query=drug_query.format(100000 * cc))
        print(cc)
        cc += 1
        if len(r['results']['bindings']) == 0:
            break
        for x in r['results']['bindings']:
            qid = x['compound']['value']

            if 'who_name' in x:
                drug_qid_map.update({x['who_name']['value'].lower(): qid})

            if 'label' in x:
                drug_qid_map.update({x['label']['value'].lower(): qid})

            if 'aliases' in x:
                drug_qid_map.update({y.lower(): qid for y in x['aliases']['value'].split('|')})

    print('Drug to QID map has {} entries!'.format(len(drug_qid_map)))
    drug_qid_map = {k: v.replace("http://www.wikidata.org/entity/", "") for k, v in drug_qid_map.items()}
    with open(os.path.join(DATA_DIR, "drug_qid_map.pkl"), 'wb') as f:
        pickle.dump(drug_qid_map, f)


df = pd.read_csv("ema_indications_merged.csv", index_col=0)

ema_atc = set(list(df['atc'].dropna().str.strip()))

# look up wdid by ATC code (using 7 digit codes only)
atc_wd = wdi_helpers.id_mapper("P267")  # ATC code
atc_wd_ema = {atc: atc_wd[atc] for atc in ema_atc if len(atc)== 7 and atc in atc_wd}
df['atc_wdid'] = df['atc'].apply(atc_wd_ema.get)

# search by name, then by active substance
#drug_qid_map = get_drug_qid_map()
drug_qid_map = pickle.load(open(os.path.join(DATA_DIR, "drug_qid_map.pkl"), 'rb'))

wdid_search_name = df.Name.str.lower().apply(drug_qid_map.get).dropna()
df.loc[wdid_search_name.index, "wdid"] = wdid_search_name

wdid_search_as = df[df['wdid'].isnull()]['Active substance'].str.lower().apply(drug_qid_map.get).dropna()
df.loc[wdid_search_as.index, "wdid"] = wdid_search_as


# search mixures by name
def get_mixtures(drugs):
    qids = [drug_qid_map.get(y.strip()) for y in drugs]
    qids = qids if all(x is not None for x in qids) else None
    return qids
qid_mixtures = df[df['Active substance'].str.contains("/")]['Active substance'].str.split("/").map(get_mixtures)
df.loc[qid_mixtures.index, "wdid_mix"] = qid_mixtures

# get rxcuis
rxnorm_wd = wdi_helpers.id_mapper("P3345")
wd_rxnorm = {v:k for k,v in rxnorm_wd.items()}
df['rxcui'] = df.wdid.apply(wd_rxnorm.get)
df['rxcui_mix'] = df.wdid_mix.dropna().apply(lambda line: [wd_rxnorm.get(x) for x in line])
df['rxcui_combo'] = df[df.wdid_mix.notnull()].rxcui_mix.apply(get_mixture_rxcui_from_parts)
df.to_csv("ema_indications_merged_drug.csv")
