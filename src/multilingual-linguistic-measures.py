# -*- coding: utf-8 -*-

"""
The :mod:`src.multilingual-linguistic-measures` implements a multilingual tool that calculates linguistic metrics from transcriptions.
Transcriptions must be tagged as it need the POS tags information for some metrics.
Here's a list of the calculated metrics:
- Text size
- Vocabulary size
- Hapax legomena
- Hapax dislegomena
- Brunet's W index
- Honoré's R statistics
- Type Token Ratio (TTR)
- Sichel's S
- Yule's K
- Entropy

Tool parameters
----------
corpus_path: path to the folder containing TAGGED transcriptions (MUST contain only transcription files)
language: specify language of the transcriptions to be processed. (e.g.: en_CA, fr_CA, etc.)"
features_output_path (optionnal): file path for the extracted measures in a .csv file (e.g.: out/pos-distribution-measures.csv
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
import math
import os
import sys
from collections import Counter

import enchant
import pandas as pd

from utils.corpus_util import extract_freeling_tags, obtain_corpus_classes, extract_participant_info
from utils.data_util import export_dataframe
from utils.nlp_util import Tag
from utils.pickle_util import read_pickle

# Constants
DIALOG_INFO_PATH = "out/DialogsInfo/PAR/"
LINGUISTIC_FEATURES_EXPORT_PATH = "out/ExtractedFeatures/linguistic_features.csv"
LINGUISTIC_FEATURES = ["idParticipant", "interviewNumber", "text_size", "vocab_size", "hapax_legomena", "hapax_dislegomena", 
                "brunet_index", "honore_r_statistics", "ttr", "sichel_s", "yule_k", "entropy", "status"]

def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual pos distribution calculator.')
    parser.add_argument(dest='corpus_path',
                    help='path to the folder containing all normalized transcripts')
    parser.add_argument(dest='language', default="en_CA",
                    help='specify language of the transcriptions used by the Enchant Python tool. Available languages : ' + str(enchant.list_languages()) + ". More can be installed via Homebrew.")
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

    linguistic_matrix = process_corpus(args.corpus_path, args.language, args.is_verbose)

    df_linguistic_results = pd.DataFrame(linguistic_matrix, columns=LINGUISTIC_FEATURES)
    
    print_results(df_linguistic_results)

    output_path = args.features_output_path if args.features_output_path else LINGUISTIC_FEATURES_EXPORT_PATH
    export_dataframe(df_linguistic_results, output_path)

def process_corpus(corpus_path, language, is_verbose=False):
    """
    This is the main function that processes given transcriptions corpus to calculate linguistic measures.

    Parameters
    ----------
    corpus_path: path to a folder containing all TAGGED transcriptions.
    language: language of the processed corpus (e.g.: en_CA, en_US, fr_CA, etc.)
    is_verbose: boolean value to print processing info to console

    Returns
    ----------
    linguistics_matrix: array of linguistic metrics.
    """

    linguistics_matrix = []

    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)
        
        # To make sure we don't process hidden files
        if not file_name.startswith("."):
            if is_verbose:
                print("Processing transcript", file_name)
            
            participant_info = extract_participant_info(file_name)

            file_path = corpus_path + "/" + file_name

            cleaned_tags = extract_freeling_tags(file_path)

            linguistics_matrix.append((participant_info["idParticipant"],) 
                                        + (participant_info["interviewNumber"],)
                                        + estimate_linguistics(cleaned_tags, language) 
                                        + (participant_info["status"],))

    return linguistics_matrix

def estimate_linguistics(cleaned_tags, language):
    """
    This function estimates linguistic metrics of a transcription's POS tags. (Refer to the files documentation for information on those metrics)

    Parameters
    ----------
    cleaned_tags: POS tags to process
    language: language of the processed corpus (e.g.: en_CA, en_US, fr_CA, etc.)

    Returns
    ----------
    linguistics_features: array of linguistic metrics for the given dialog
    """

    linguistics_features = []
    
    d = enchant.Dict(language)
    
    ## Hyper-Parameters
    # Used for Brunet's W Index (Brunet, 1978). 0.172 is the original value proposed by Brunet
    c = 0.172
    
    ## Initial states
    text_size = 0
    vocab_size = 0
    hapax_legomena = 0
    hapax_dislegomena = 0
    brunet_index = 0
    honore_r_statistics = 0
    ttr = 0
    sichel_s = 0
    yule_k = 0
    entropy = 0
    
    words = []
    lemmas = []
    
    for tag in cleaned_tags:
        if type(tag) is Tag and d.check(tag.original):
            ## TEXTSIZE
            text_size += 1
            
            words.append(tag.original)
            lemmas.append(tag.lemma)

    ## VOCAB SIZE : Number of different lemmas
    lemmas_counts = Counter(lemmas)
    vocab_size = len(lemmas_counts)
    
    ## LEMMAS
    for (lemma, count) in lemmas_counts.items():
        ## HAPAX LEGOMENA : Number of lemmas mentioned only once
        if count == 1: 
            hapax_legomena += 1 
        ## HAPAX DISLEGOMENA : Number of lemmas mentioned exactly twice
        if count == 2:
            hapax_dislegomena += 1
            
    ## BRUNET'S W INDEX
    if text_size > 0 and vocab_size > 0:
        brunet_index = text_size ** vocab_size ** (-c)
        
    ## HONORÉ'S R STATISTICS
    if text_size > 0 and vocab_size > 0 and (1 - (hapax_legomena / vocab_size) > 0):
        honore_r_statistics = (100 * math.log(text_size)) / (1 - (hapax_legomena / vocab_size))
         
    ## TYPE TOKEN RATION
    if vocab_size > 0:
        ttr = hapax_legomena / vocab_size
        
    ## SICHEL'S S
    if vocab_size > 0:
        sichel_s = hapax_dislegomena / vocab_size
  
    ## YULE'S CHARACTERISTIC K
    words_count = Counter(words)
    n = sum(words_count.values())
    n2 = sum([i ** 2 for i in words_count.values()])
    if n > 0:
        yule_k = 10000 * ((n2-n) / (n**2)) - (1 / n)
        
    ## ENTROPY
    if text_size > 0:
        entropy = -sum(count / text_size * math.log(count / text_size, 2) for count in words_count.values())

    return (text_size, vocab_size, hapax_legomena, hapax_dislegomena, brunet_index, honore_r_statistics, ttr, sichel_s, yule_k, entropy)
    
def print_results(results):
    print("")
    print("LINGUISTIC MEASURES RESULTS (Avg.)")
    print("------------------------")
    print(results.drop('idParticipant', 1).drop('interviewNumber', 1).drop('status', 1).mean())

if __name__ == "__main__":
    main()
