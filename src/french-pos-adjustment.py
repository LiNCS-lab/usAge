# -*- coding: utf-8 -*-

"""
The :mod:`src.french-pos-adjustment` implements a french POS tag adjustment task.
It is used to modify some tags that might have been wrongfully tagged by spaCy 
or to arrange some tags as desired for a specific context.

This is an incremental process which can be modified as desired.

Tool parameters
----------
corpus_path: path to the folder containing TAGGED transcriptions (MUST contain only transcription files)
is_verbose: for debugging purpose

This module is part of the work on a multilingual approach for extracting measures out of transcriptions and audios 
for evaluating and monitor patient's linguistic/phonetic functions.
"""

# Author: Frédéric Abiven <fredericabiveninfo@gmai.com>, 2020
#         Laboratoire d'ingénierie Cognitive et Sémantique (LiNCS)
#         http://lincs.etsmtl.ca
#         École de technologie supérieure (ÉTS)
#
# Free software: MIT license

import argparse
import os
import sys
import re

from utils.corpus_util import extract_tags, obtain_corpus_classes, extract_participant_info
from utils.data_util import save_tags_in_file
from utils.pickle_util import read_pickle
from utils.nlp_util import Tag, UniversalPOS

# CONSTANTS
ADJUSTED_DIALOG_OUTPUT_PATH = "out/TaggedDialogsAdjusted/"

def main():
    args = parse_args()

    if not os.path.isdir(args.corpus_path):
        print("Given corpus path is not a directory")
        sys.exit(1)
    if not os.path.exists(args.corpus_path):
        print("Given corpus path doesn't exist.")
        sys.exit(1)

    corpus_classes = obtain_corpus_classes(args.corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    adjustment_results = process_corpus(args.corpus_path, args.is_verbose)

    print_results(adjustment_results)
    
def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual pos distribution calculator.')
    parser.add_argument(dest='corpus_path', 
                    help='path to the folder containing all transcripts with POS tags')
    parser.add_argument('-v', '--verbose', dest='is_verbose', default=False, action='store_true',
                    help='print processing info')
    return parser.parse_args()

def process_corpus(corpus_path, is_verbose=False):
    """
    This is the main function that processes given corpus to adjust tags. It iterates thru every transcriptions and process tag adjustments.

    Parameters
    ----------
    corpus_path: path to a folder containing all transcriptions
    is_verbose: boolean value to print processing info to console

    Returns
    -------
    adjustment_count: the number of adjustments made on the corpus
    """

    adjustment_count = 0

    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)

        # To ignore hidden files
        if not file_name.startswith("."):
            if is_verbose:
                print("Processing transcript", file_name)

            participant_info = extract_participant_info(file_name)

            tags = extract_tags(os.path.join(corpus_path, file_name))

            adjusted_dialog_tags, dialog_adjustment_count = adjust_pos_tags(tags, is_verbose=is_verbose)

            export_file_path = ADJUSTED_DIALOG_OUTPUT_PATH + file_name
            save_tags_in_file(adjusted_dialog_tags, export_file_path)

            adjustment_count += dialog_adjustment_count

    return adjustment_count

def adjust_pos_tags(pos_tags, is_verbose=False):
    """
    This function adjust POS tags made by spaCy.

    Parameters
    ----------
    pos_tags: list of POS tags
    is_verbose: boolean value to print processing info to console

    Returns
    -------
    pos_tags: list of adjusted POS tags
    adjustment_count: the number of adjustments made on the list of POS tags
    """
    adjustment_count = 0
    
    for previous_tag, current_tag in zip(pos_tags, pos_tags[1:]):
        if type(current_tag) is Tag and type(previous_tag) is Tag:
            # For a pattern like "des --> de les"
            if current_tag.original.lower() == "les" and previous_tag.original.lower() == "de":
                current_tag.original = "des"
                current_tag.lemma = "de les"
                current_tag.tag = "ADP"
                adjustment_count += 1
                pos_tags.remove(previous_tag)
            
            # For a pattern like "du --> de le"
            elif current_tag.original.lower() == "le" and previous_tag.original.lower() == "de":
                current_tag.original = "du"
                current_tag.lemma = "de le"
                current_tag.tag = "ADP"
                adjustment_count += 1
                pos_tags.remove(previous_tag)
            
            # For a pattern like "sommes --> sommer" précédé par "nous"
            elif current_tag.original.lower() == "sommes" and current_tag.lemma.lower() == "sommer" and previous_tag.original.lower() == "nous":
                current_tag.lemma = "être"
                current_tag.tag = "ADP"
                adjustment_count += 1
            
            # We extract determinants for the information coverage task (will be used for information coverage task)
            # if current_tag.tag == UniversalPOS.DET_TAG:
            #     pos_tags.remove(current_tag)
            #     adjustment_count += 1

    return pos_tags, adjustment_count

def print_results(fix_count):
    print("")
    print("POS ADJUSTMENT RESULTS")
    print("------------------------")
    print("Fixed", fix_count, "POS tags.")
    
if __name__ == "__main__":
    main()
