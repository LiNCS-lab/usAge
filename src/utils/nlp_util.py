# -*- coding: utf-8 -*-

"""
The :mod:`src.nlp_util` defines the basic structure of the most
used classes for NLP applications.
"""

# Author: Frédéric Abiven <fredericabiveninfo@gmai.com>, 2020
#         Laura Hernandez-Dominguez <laura.hzdz@gmail.com>, 2018
#         Laboratoire d'ingénierie Cognitive et Sémantique (LiNCS)
#         http://lincs.etsmtl.ca
#         École de technologie supérieure (ÉTS)
#
# Free software: MIT license

# -*- coding: utf-8 -*-

class UniversalPOS:
    # POS Universal tags
    ADJ_TAG = "ADJ"
    ADP_TAG = "ADP"
    ADV_TAG = "ADV"
    AUX_TAG = "AUX"
    CONJ_TAG = "CONJ"
    CCONJ_TAG = "CCONJ"
    DET_TAG = "DET"
    INTJ_TAG = "INTJ"
    NOUN_TAG = "NOUN"
    NUM_TAG = "NUM"
    PART_TAG = "PART"
    PRON_TAG = "PRON"
    PUNCT_TAG = "PUNCT"
    SCONJ_TAG = "SCONJ"
    VERB_TAG = "VERB"
    UNIVERSAL_TAGSET = [ADJ_TAG, ADP_TAG, ADV_TAG, AUX_TAG, CONJ_TAG, CCONJ_TAG, DET_TAG, INTJ_TAG, NOUN_TAG, NUM_TAG, PART_TAG, PRON_TAG, PUNCT_TAG, SCONJ_TAG, VERB_TAG]

    def __init__(self, universal_map_file):
        self.universal_map = {}
        self.init_universal_map(universal_map_file)

    def init_universal_map(self, universal_map_file): 
        with open(universal_map_file) as f:
            for line in f:
                (pos_tag, universal_pos_tag) = line.split()
                self.universal_map[pos_tag] = universal_pos_tag
        f.close()
    
    def get_universal_tag(self, tag):
        tag = tag.lower()
        if tag in self.universal_map:
            return self.universal_map[tag]
        else:
            return

class Tag:
    """
    A tag object will be composed of four elements:
    The original word, the lemma, the tag.
    """
    def __init__(self, original="", lemma="", tag=""):
        """Initializes the data."""
        self.original = original
        self.lemma = lemma
        self.tag = tag


class Parse:
    """
    A parse object will be composed of:
    The parsing (could be a whole parsing or a fragment, such as an utterance) and
    the maximum depth of the parsing.
    """
    def __init__(self, parsing="", max_depth=-1):
        """Initializes the data."""
        self.parsing = parsing
        self.max_depth = max_depth
