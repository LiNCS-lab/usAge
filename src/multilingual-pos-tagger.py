# -*- coding: utf-8 -*-

"""
The :mod:`src.multilingual-pos-tagger` implements a multilingual module that annotate words with POS tags (using spaCy).
It tags words and punctiation markers in transcriptions.

Tool parameters
----------
corpus_path: path to the folder containing CLEANED transcriptions (MUST contain only transcription files)
language_code: language code that represents the language in which we wanna tag words
universal_tag: path to a universal map configuration file (refer to README.md for more info)
is_verbose: for debugging purpose

This module is part of the work on a multilingual approach for extracting measures out of transcriptions and audios 
for evaluating and monitor patient's linguistic/phonetic functions.
"""

# Author: Frédéric Abiven <fredericabiveninfo@gmai.com>, 2020
#         Laura Hernandez-Dominguez <laura.hzdz@gmail.com>, 2018
#         Laboratoire d'ingénierie Cognitive et Sémantique (LiNCS)
#         http://lincs.etsmtl.ca
#         École de technologie supérieure (ÉTS)
#
# Free software: MIT license

import argparse
import os
import subprocess
import sys

import spacy

from utils.corpus_util import obtain_corpus_classes
from utils.nlp_util import UniversalPOS

# Spacy Models (Supports Chinese, Danish, Dutch, English, French, German, Greek, Italian, 
# Japanese, Lithuanian, Norwegian Bokmål, Polish, Portuguese, Romanian & Spanish)
# https://spacy.io/usage/models for mor info

# CONSTANTS
TAGGED_DIALOG_OUTPUT_PATH = "out/TaggedDialogs"

def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual pos distribution calculator.')
    parser.add_argument(dest='corpus_path',
                    help='path to the folder containing all normalized transcripts')
    parser.add_argument(dest='language_code',
                    help='Language code (zh, da, nl, en, fr, de, el, it, ja, lt, nb, pl, pt, ro, es)')
    parser.add_argument('-u', '--universal_tag', default=False, action='store_true',
                    help='if you want the universal form of tags or with the morphological complexity of tags')
    parser.add_argument('-v', '--verbose', dest='is_verbose', default=False, action='store_true',
                    help='print processing info')
    return parser.parse_args()

def main():
    args = parse_args()

    if not os.path.isdir(args.corpus_path):
        print("Given corpus path is not a directory")
        sys.exit(1)
    if not os.path.exists(args.corpus_path):
        print("Given corpus path doesn't exist.")
        sys.exit(1)
    if not args.language_code:
        print("Missing language code.")
        sys.exit(1)

    spacy_model = get_spacy_model(language_code=args.language_code)

    corpus_classes = obtain_corpus_classes(args.corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    process_corpus(args.corpus_path, spacy_model, universal_tag=args.universal_tag)

    print("-------------------")
    print("POS tagging task done.")

def process_corpus(corpus_path, spacy_model, universal_tag=True, is_verbose=False):
    """
    This is the main function that processes given corpus to tag it. It iterates thru every transcriptions and tag them.
    Finally, it converts some tag to there universal form (e.g.: VBG --> VERB)

    Parameters
    ----------
    corpus_path: path to a folder containing all transcriptions
    spacy_model: spaCy model used for POS tagging
    universal_tag: if you want universal tag or morphological tag
    is_verbose: boolean value to print processing info to console
    """

    if not os.path.exists(TAGGED_DIALOG_OUTPUT_PATH):
        os.makedirs(TAGGED_DIALOG_OUTPUT_PATH)
    
    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)

        # To make sure we don't process hidden files
        if not file_name.startswith("."):
            if is_verbose:
                    print("Processing transcript", file_name)

            file_path = corpus_path + "/" + file_name
            output_file_path = TAGGED_DIALOG_OUTPUT_PATH + "/" + file_name

            input_file = open(file_path, "r")
            doc = spacy_model(input_file.read())
                
            with open(output_file_path, 'w') as output_file:
                for token in doc:
                    if universal_tag:
                        output_file.write(token.text + " " + token.lemma_ + " " + token.pos_ + "\n")
                    else:
                        output_file.write(token.text + " " + token.lemma_ + " " + token.tag_ + "\n")


def get_spacy_model(language_code):
    """
    This function will fetch the good spaCy model depending on the given language code.

    Parameters
    ----------
    language_code: language code (e.g. fr, en, es)
    universal_tag: if we want the universal tag or keep the morphological complexity of tags
    """
    switcher = {
        "zh": lambda: spacy.load("zh_core_web_sm"),
        "da": lambda: spacy.load("da_core_news_sm"),
        "nl": lambda: spacy.load("nl_core_news_sm"),
        "en": lambda: spacy.load("en_core_web_sm"),
        "fr": lambda: spacy.load("fr_core_news_sm"),
        "de": lambda: spacy.load("de_core_news_sm"),
        "el": lambda: spacy.load("el_core_news_sm"),
        "it": lambda: spacy.load("it_core_news_sm"),
        "ja": lambda: spacy.load("ja_core_news_sm"),
        "lt": lambda: spacy.load("lt_core_news_sm"),
        "nb": lambda: spacy.load("nb_core_news_sm"),
        "pl": lambda: spacy.load("pl_core_news_sm"),
        "pt": lambda: spacy.load("pt_core_news_sm"),
        "ro": lambda: spacy.load("ro_core_news_sm"),
        "es": lambda: spacy.load("es_core_news_sm")
    }
    model = switcher[language_code]()

    if not model:
        return spacy.load("en_core_web_sm")
    return model

if __name__ == "__main__":
    main()
