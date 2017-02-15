"""
string search indications with DO
add categories
"""
import json
import os
import re

from utils import get_names_synonyms_doid, get_doid_names, clean_text, contains_word
import pandas as pd

DATA_DIR = "../data"

def match_diseases_in_indication(indication, name_doid):
    if not isinstance(indication, str):
        return []
    indication = " " + clean_text(indication) + " "
    return [disease for disease in name_doid if ' ' + disease + ' ' in indication]


name_doid = get_names_synonyms_doid(os.path.join(DATA_DIR, "doid.json"))
doid_names = get_doid_names(os.path.join(DATA_DIR, "doid.json"))

df = pd.read_csv(os.path.join(DATA_DIR, "ema_indications.csv"), index_col=0)
df.Indication.fillna('', inplace=True)
df.wdid_mix = df.wdid_mix.dropna().apply(eval)
d = df.to_dict('records')

for record in d:
    record['diseases'] = match_diseases_in_indication(record['Indication'], name_doid)
    record['doids'] = {name_doid[x]: doid_names[name_doid[x]] for x in record['diseases']}

# categorize
tokenizer = re.compile(r'\w+')
genetic_words = {'mutation', 'deletion', 'duplication', 'inversion', 'substitution', 'inactivation',
                 'gene', 'protein', 'chromosomal', 'chromosome', 'splicing', 'exon', 'intron', 'short arm',
                 'long arm', 'genetic'}
genetic_words.update({word + 's' for word in genetic_words})
contra_words = {'contraindication', 'should not be', 'do not', 'avoid', 'contraindications'}
for record in d:
    record['cat'] = dict()
    tokens = tokenizer.findall(record['Indication'])
    record['cat']['short'] = True if len(tokens) < 100 else False
    record['cat']['genetic'] = True if contains_word(genetic_words, record['Indication']) else False
    record['cat']['contra'] = True if contains_word(contra_words, record['Indication']) else False

with open(os.path.join(DATA_DIR, "ema.json"), "w") as f:
    json.dump(d, f, indent=2)
