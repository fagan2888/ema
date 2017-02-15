"""
Make html version of indications text.
highlight all doid drug names in text

create list of choices
primary DO name, (synonyms in parenthesis)

Some code copied from here: https://github.com/SuLab/crowd_cid_relex/blob/master/crowd_only/src/make_cf_work_units.py
(thanks Toby Li)

"""

# https://success.crowdflower.com/hc/en-us/articles/217231986?input_string=checkboxes+with+variable+number+of+choices
import json
import os
import re
import csv
from itertools import chain
DATA_DIR = "../data"

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


def add_simple_tag(tag_name, tag_class, text):
    """Put a HTML tag around a snippet of text."""
    return "<{0} class=\"{1}\">{2}</{0}>".format(tag_name, tag_class, text)


def multireplace(string, replacements):
    """
    Given a string and a replacement map, it returns the replaced string.
    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :rtype: str
    https://gist.github.com/bgusach/a967e0587d6e01e889fd1d776c5f3729
    """
    # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
    # 'hey ABC' and not 'hey ABc'
    substrs = sorted(replacements, key=len, reverse=True)

    # Create a big OR regex that matches any of the substrings to replace
    regexp = re.compile('|'.join(map(re.escape, substrs)))

    # For each match, look up the new string in the replacements
    return regexp.sub(lambda match: replacements[match.group(0)], string)


def highlight_concepts(text, tag_class, spans):
    """
    Inserts HTML tags around the pieces of text
    which need to be highlighted in a string.
    """
    spans = sorted(spans, key=lambda x: x[0])

    replacements = {}
    for span in spans:
        s_orig = text[span[0]:span[1]]
        s_new = add_simple_tag("span", tag_class, s_orig)
        replacements[s_orig] = s_new
    text = multireplace(text, replacements)
    return text


def merge_spans(spans):
    # http://codereview.stackexchange.com/a/108651
    sorted_intervals = sorted(spans, key=lambda x: x[0])

    if not sorted_intervals:  # no intervals to merge
        return

    # low and high represent the bounds of the current run of merges
    low, high = sorted_intervals[0]

    for iv in sorted_intervals[1:]:
        if iv[0] <= high:  # new interval overlaps current run
            high = max(high, iv[1])  # merge with the current run
        else:  # current run is over
            yield low, high  # yield accumulated interval
            low, high = iv  # start new run

    yield low, high  # end the final run


def highlight_text(text, words):
    """
    Given a string and the annotations which fall
    within this string, highlights the concepts.
    """
    text = text.lower()
    words = [x.lower() for x in words]

    spans = list(chain(*[[(m.start(), m.end()) for m in re.finditer(word, text)] for word in words]))
    spans = list(merge_spans(spans))
    if spans:
        return highlight_concepts(text, "disease", spans)
    else:
        return text

if __name__ == "__main__":
    # text = "Mild-to-moderate infections of the yaws upper-respiratory tract due to susceptible streptococci. " \
    #       "Venereal infections—Syphilis, yaws, bejel, and pinta."
    # highlight_text(text, ["upper-respiratory tract", "respiratory", "due to", "yaws", "pinta"])

    d = json.load(open(os.path.join(DATA_DIR, "ema.json")))
    f = open("tmp.csv", "w")
    writer = csv.writer(f)
    writer.writerow(["medicine_name","common_name","wdid","indication","diseases"])
    for record in d[:10]:
        record['indication_html'] = highlight_text(record['Indication'], record['diseases'])
        #print(json.dumps(record, indent=2))
        # "http://purl.obolibrary.org/obo/DOID_9351|diabetes mellitus (diabetes, adf);http://purl.obolibrary.org/obo/DOID_2222|khkhsd"

        field = {k: v[0] + " (" + ", ".join(v[1:]) + ")" if len(v)>1 else v[0] for k,v in record['doids'].items()}
        record['disease_str'] = ';'.join([k + "|" + v for k,v in field.items()])
        writer.writerow([record['Medicine Name'], record['Common name'], record['wdid'],
                         record['indication_html'], record['disease_str']])
    f.close()

    with open(os.path.join(DATA_DIR, "ema2.json"), "w") as f:
        json.dump(d, f, indent=2)