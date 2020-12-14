# -*- coding: utf-8 -*-

"""
The :mod:`src.multilingual-pos-distribution` implements a multilingual tool that calculates POS tag distribution metrics.
Those POS tag have been previously made by the :mod:`src.multilingual-pos-tagger` tool.

It calculates FREQUENCIES and RATIOS of the following tags: ADJ, CONJ, NOUN, ADP, VERB, AUX_VERB.

Tool parameters
----------
corpus_path: path to the folder containing TAGGED (with universal tags) transcriptions (MUST contain only transcription files)
features_output_path (optionnal): file path for the extracted measures in a .csv file (e.g.: out/pos-distribution-measures.csv)
verbose (optionnal): for debugging purpose

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
import re
import sys
from collections import defaultdict

import pandas as pd

from utils.corpus_util import extract_tags, obtain_corpus_classes, extract_participant_info
from utils.data_util import export_dataframe
from utils.pickle_util import read_pickle
from utils.nlp_util import UniversalPOS, Tag

# CONSTANTS
POS_DISTRIBUTION_FEATURES_PATH = "out/ExtractedFeatures/pos_distribution.csv"

def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual pos distribution calculator.')
    parser.add_argument(dest='corpus_path',
                    help='path to the folder containing all transcripts with POS tags')
    parser.add_argument('-f', '--features_output_path', dest='features_output_path',
                    help='path to folder where normalizing features will be stored (.csv file)')
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

    corpus_classes = obtain_corpus_classes(args.corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    pos_distribution = process_corpus(args.corpus_path, args.is_verbose)

    df_pos_distribution = pd.DataFrame(pos_distribution)
    
    print_results(df_pos_distribution)

    output_path = args.features_output_path if args.features_output_path else POS_DISTRIBUTION_FEATURES_PATH
    export_dataframe(df_pos_distribution, output_path)

def process_corpus(corpus_path, is_verbose=False):
    """
    This is the main function that processes given corpus to calculate POS tag distribution.

    Parameters
    ----------
    corpus_path: path to a folder containing all transcriptions
    is_verbose: boolean value to print processing info to console

    Returns
    ----------
    corpus_pos_distribution: array of float values corresponding the POS tag distribution (frequency and ratio)
    """

    corpus_pos_distribution = []

    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)

        # To make sure we don't process hidden files
        if not file_name.startswith("."):
            if is_verbose:
                    print("Processing transcript", file_name)

            results = defaultdict(int)
            
            participant_info = extract_participant_info(file_name)

            tags = extract_tags(os.path.join(corpus_path, file_name))

            pos_distribution, total_word_count = calculate_pos_frequency(tags, is_verbose=is_verbose)

            results["idParticipant"] = participant_info["idParticipant"]
            results["interviewNumber"] = participant_info["interviewNumber"]
            for measure in UniversalPOS.UNIVERSAL_TAGSET:
                freq_idx = measure.lower() + "Freq"
                ratio_idx = measure.lower() + "Ratio"
                results[freq_idx] = pos_distribution[measure]
                results[ratio_idx] = (pos_distribution[measure] * 100) / total_word_count
            results["totalWordCount"] = total_word_count 
            results["status"] = participant_info["status"]

            corpus_pos_distribution.append(results)

    return corpus_pos_distribution

def calculate_pos_frequency(pos_tags, is_verbose=False):
    """
    This function calculates the distribution of the UNIVERSAL POS tags (frequency).
    For better results, make sure the tags have been universalized before.

    Parameters
    ----------
    pos_tags: array of tags to calculate distribution
    is_verbose: boolean value to print processing info to console

    Returns
    ----------
    pos_distribution: array of float values corresponding the POS tag distribution (frequency and ratio)
    total_word_count: word count the current POS tags list
    """

    pos_distribution = defaultdict(int)
    missed_tag_count = 0
    total_word_count = 0

    for pos_tag in pos_tags:
        if type(pos_tag) is Tag:
            if pos_tag.tag:
                if pos_tag.tag != UniversalPOS.PUNCT_TAG:
                    total_word_count += 1
                if pos_tag.tag in UniversalPOS.UNIVERSAL_TAGSET:
                    pos_distribution[pos_tag.tag] += 1

    total_word_count += missed_tag_count
    return pos_distribution, total_word_count

def print_results(results):
    print("")
    print("POS DISTRIBUTION RESULTS (Average per transcription)")
    print("------------------------")
    print(results[[x for x in results if x.endswith('Freq')]].mean())
    
if __name__ == "__main__":
    main()
