import os
from itertools import chain
import pandas as pd
import json
from collections import defaultdict
from ema.utils import get_names_synonyms_doid, get_doid_names, clean_text, contains_word
DATA_DIR = "../data"

df = pd.read_csv("ema_indications_merged_drug.csv", index_col=0)

diseases = set(chain(*list(df['Therapeutic area'].dropna().str.split("  "))))

# create mesh title synonyms dict
# json is created from https://github.com/stuppie/mesh-parser
mesh = json.load(open("/home/gstupp/projects/mesh/mesh.json"))
title_mesh = dict()
synonym_mesh = dict()
mesh_tree = dict()
for record in mesh.values():
    if record['record_type'] == 'C':
        continue
    title_mesh[record['term'].lower()] = record['_id']
    mesh_tree[record['_id']] = record['tree'] if 'tree' in record else ''
    for syn in record.get('synonyms', []):
        synonym_mesh[syn.lower()] = record['_id']
d = {x:title_mesh[x.lower()] for x in diseases if x.lower() in title_mesh}
d.update({x:synonym_mesh[x.lower()] for x in diseases if x.lower() in synonym_mesh})
mesh_name = {v:k for k,v in title_mesh.items()}

df['therapeutic_area_mesh'] = df['Therapeutic area'].dropna().str.split("  ").apply(lambda row:[d.get(x) for x in row])


def mesh_xref_onto(json_path):
    # mesh to Doid mapper
    # doid.json is an obographs converted doid.owl
    doid = json.loads(open(json_path).read())
    graph = doid['graphs'][0]
    nodes = graph['nodes']
    mesh_doid = dict()
    for node in nodes:
        if 'meta' in node and 'deprecated' in node['meta'] and node['meta']['deprecated']:
            continue
        if 'meta' in node and 'xrefs' in node['meta']:
            mesh_xrefs = [x['val'].split(":")[1] for x in node['meta']['xrefs'] if "MSH" in x['val']]
            mesh_doid.update({mesh:node['id'].split("/")[-1].replace("_",":") for mesh in mesh_xrefs})
    return mesh_doid

# mesh to HP mapper
mesh_doid = mesh_xref_onto(os.path.join(DATA_DIR, "doid.json"))
mesh_hp = mesh_xref_onto(os.path.join(DATA_DIR, "hp.json"))

mesh_doid_or_hp = {mesh: mesh_doid[mesh] for mesh in d.values() if mesh in mesh_doid}
missing = {x for x in d.values() if x not in mesh_doid}
mesh_doid_or_hp.update({mesh: mesh_hp[mesh] for mesh in d.values() if mesh in mesh_hp and mesh in missing})

df['therapeutic_area_do_hp'] = df['therapeutic_area_mesh'].dropna().apply(lambda row:[mesh_doid_or_hp.get(x) for x in row])

df.to_csv("ema_indications_merged_drug_doid.csv")