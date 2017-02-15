import re
from collections import defaultdict

import requests
from tqdm import tqdm
import json


def contains_word(words, text):
    if any([bool(re.findall(r"\b{}\b".format(word), text, re.I)) for word in words]):
        return True
    else:
        return False

def lower_unless_upper(s):
    if s.upper() == s:
        return s
    else:
        return s.lower()


def clean_text(indication):
    """ lowercase all words that are not entirely uppercase """
    tokenizer = re.compile(r'\w+')
    tokens = tokenizer.findall(indication)
    tokens = [lower_unless_upper(w) for w in tokens]
    indication = ' '.join(tokens)
    return indication


def get_names_synonyms_doid(json_path):
    """
    return dict of name to doid purl
    :param json_path: path to a obographs json file
    :return:
    """
    # get DO names and synonyms
    d = json.loads(open(json_path).read())
    nodes = d['graphs'][0]['nodes']
    disease_names = dict()
    for node in nodes:
        if node['id'] == "http://purl.obolibrary.org/obo/DOID_4":  # disease
            continue
        if 'meta' in node and 'deprecated' in node['meta'] and node['meta']['deprecated']:
            continue
        if 'lbl' in node:
            disease_names[clean_text(node['lbl'])] = node['id']
        if 'meta' in node and 'synonyms' in node['meta']:
            for syn in node['meta']['synonyms']:
                disease_names[clean_text(syn['val'])] = node['id']
    #print(list(disease_names.items())[:10])
    return disease_names


def get_doid_names(json_path):
    """
    get dict of DOID purl to list of names and synonyms for that DOID
    where the primary name is the first element in the list
    :param json_path: path to a obographs json file
    :return:
    """
    doid_names = dict()
    d = json.loads(open(json_path).read())
    nodes = d['graphs'][0]['nodes']
    for node in nodes:
        if node['id'] == "http://purl.obolibrary.org/obo/DOID_4":  # disease
            continue
        if 'meta' in node and 'deprecated' in node['meta'] and node['meta']['deprecated']:
            continue
        if 'lbl' in node:
            doid_names[node['id']] = [clean_text(node['lbl'])]
            if 'meta' in node and 'synonyms' in node['meta']:
                for syn in node['meta']['synonyms']:
                    doid_names[node['id']].append(clean_text(syn['val']))
    return doid_names


def get_drug_classes(rxcuis):
    """
    Get some more info about the drug: https://rxnav.nlm.nih.gov/RxClassIntro.html Source: DailyMed, NDFRT
    Drug members of a FDA Established Pharmacologic Class (has_EPC)
    Drugs that have a Mechanism of Action (has_MoA)
    Drugs that have a Physiologic Effect (has_PE)
    Drugs that may prevent a disease (may_prevent)
    Drugs that may treat a disease (may_treat)

    https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui=7052&relaSource=DailyMed&relas=has_EPC+has_MoA+has_PE
    :param rxcui:
    :return:
    """
    relas = {'has_EPC', 'has_MoA', 'has_PE', 'may_prevent', 'may_treat'}
    classes = dict()
    for rxcui in tqdm(rxcuis):
        url = "https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={}".format(rxcui)
        d = requests.get(url).json()
        if 'rxclassDrugInfoList' in d:
            rels = [x for x in d['rxclassDrugInfoList']['rxclassDrugInfo'] if x['rela'] in relas]
            for x in rels:
                x['rxclassMinConceptItem']['rela'] = x['rela']
            rels = [x['rxclassMinConceptItem'] for x in rels]
            rels = set([(x['classId'], x['className'], x['classType'], x['rela']) for x in rels])
            classes[rxcui] = rels
    return classes


def get_mixture_rxcui_from_parts(rxcuis):
    """
    Given a set of ingredient rxcui, get the MIN rxcui
    :param rxcuis:
    :return:
    """
    url = "https://rxnav.nlm.nih.gov/REST/rxcui/{}/related.json?rela=part_of"
    min_rxcuis = []
    for rxcui in rxcuis:
        d = requests.get(url.format(rxcui)).json()['relatedGroup']
        if 'conceptGroup' not in d:
            return None
        d = d['conceptGroup'][0]
        assert d['tty'] == "MIN"
        min_rxcuis.append(set([x['rxcui'] for x in d['conceptProperties']]))
    #print(min_rxcuis)
    min_rxcui = list(set.intersection(*min_rxcuis))
    assert len(min_rxcui) == 1
    return min_rxcui[0]