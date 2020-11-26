# -*- coding: utf-8 -*-

"""
The :mod:`src.multilingual-text-normalizer` implements a multilingual pipeline architecture of cleaning and normalizing transcriptions.
It removes discursive markers that were previously annotated by a human or in an automatic process.
The definition of those markers can be found in the README.md.
Finally, measures of the extraction of those markers and cleaning/normalizing task (frequencies and ratios) are exported to a csv file
for evaluation and monitoring purpose.

For the moment, .txt and .chat files are supported. Here are the expected format:
--.txt file--: Participant's dialog ONLY in a simple text written format.
--.cha file--: Participant's and interviewer's dialog (two-speaker dialog) with or without dialog information.
n.b. more format can be supported as it is an iterative work

Tool parameters
----------
corpus_path: path to the folder containing transcriptions (MUST contain only transcription files)
synonym_conf_path (optionnal): file path of the synonym reducing task configuration file (refer to README.md for more info)
interjections_conf_path (optionnal): file path of the interjections extraction task configuration file (refer to README.md for more info)
expressions_conf_path (optionnal): file path of the expressions extraction task configuration file (refer to README.md for more info)
features_output_path (optionnal): file path for the extracted measures in a .csv file (e.g.: out/extracted-measures.csv)
verbose (optionnal): for debugging purpose

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
import re
import sys
from collections import defaultdict

import pandas as pd

from utils.cleaning_util import *
from utils.corpus_util import (extract_participant_info,
                               extract_transcript_lines,
                               extract_two_speaker_dialogs,
                               obtain_corpus_classes)
from utils.data_util import export_dataframe, save_dialog_in_file
from utils.pickle_util import write_pickle

## CONSTANTS ##
CLEANED_DIALOG_PAR_PATH = 'out/CleanedDialogs/PAR/Original/'
CLEANED_DIALOG_INT_PATH = 'out/CleanedDialogs/INT/Original/'

CLEANED_DIALOG_PAR_SYN_PATH = 'out/CleanedDialogs/PAR/SynonymReduced/'
CLEANED_DIALOG_INT_SYN_PATH = 'out/CleanedDialogs/INT/SynonymReduced/'

MARKERS_DISTRIBUTION_PATH = 'out/ExtractedFeatures/discursive_markers_distribution.csv'

CLEANING_MEASURES_DICT = {"nbPausesTotal", "nbPausesShort", "nbPausesMedium", "nbPausesLong",
                          "nbPausesOther", "nbExpressions", "nbInterjections", "nbIncWords",
                          "nbIncPhrases", "nbErrors", "nbRepetitions", "nbRetracings", "nbSynonyms"}


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(dest='corpus_path',
                        help='path to the folder containing all transcripts')
    parser.add_argument('-s', '--synonyms_conf_path', dest='synonyms_conf_path', default=None,
                        help='file path to config file for synonym reduction task')
    parser.add_argument('-i', '--interjections_conf_path', dest='interjections_conf_path', default=None,
                        help='file path to config file for interjection removal task')
    parser.add_argument('-e', '--expressions_conf_path', dest='expressions_conf_path', default=None,
                        help='file path to config file for expression removal task')
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
    if args.interjections_conf_path and not os.path.exists(args.interjections_conf_path):
        print("Given interjections config file path doesn't exist.")
        sys.exit(1)
    if args.expressions_conf_path and not os.path.exists(args.expressions_conf_path):
        print("Given expressions config file path doesn't exist.")
        sys.exit(1)

    corpus_classes = obtain_corpus_classes(args.corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    cleaning_results = process_corpus(args.corpus_path, args.synonyms_conf_path,
                                      args.interjections_conf_path, args.expressions_conf_path, args.is_verbose)

    df_cleaning_results = pd.DataFrame(cleaning_results)

    print_results(df_cleaning_results)

    output_path = args.features_output_path if args.features_output_path else MARKERS_DISTRIBUTION_PATH
    export_dataframe(df_cleaning_results, output_path)


def process_corpus(corpus_path, synonyms_conf_path=None, interjections_conf_path=None, expressions_conf_path=None, is_verbose=False):
    """
    This is the main function that processes given corpus to normalize it and clean it. It iterates thru every transcriptions and clean them while
    extracting cleaning/normalizing measures as FREQUENCIES and RATIOS which can be use for evaluating participant's dialogs.

    Parameters
    ----------
    corpus_path: path to a folder containing all transcriptions
    synonyms_conf_path: path to a configuration file for synonym reducing task (refer to README.md for more info)
    interjections_conf_path: path to a configuration file for interjection extraction task (refer to README.md for more info)
    expressions_conf_path: path to a configuration file for expression extraction task (refer to README.md for more info)
    is_verbose: boolean value to print processing info to console

    Returns
    -------
    cleaning results: a list of all cleaning/normalizing measures extracted during this process
    """
    cleaning_results = []

    # We iterate thru all files in corpus (all transcriptions)
    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)
        is_chat_file = file_name.endswith(".cha")
        is_txt_file = file_name.endswith(".txt")

        participant_dialog = {}
        interviewer_dialog = {}
        results = defaultdict(int)
        participant_info = {}

        # To make sure we don't process hidden files
        if not file_name.startswith("."):
            # For now, text files and chat files are supported
            if is_txt_file or is_chat_file:
                if is_verbose:
                    print("Processing transcript", file_name)

                transcript_lines = extract_transcript_lines(
                    os.path.join(corpus_path, file_name), is_chat_file)

                participant_info = extract_participant_info(file_name)

                # Chat files normaly contains two speaker dialog which has to be extracted seperatly
                if is_chat_file:
                    participant_dialog, interviewer_dialog = extract_two_speaker_dialogs(
                        transcript_lines, '*PAR:', '*EXP:')

                    cleaning_measures_int, clean_interviewer_dialog, clean_interviewer_dialog_syn = clean_transcription(interviewer_dialog,
                                                                                                                        synonyms_conf_path,
                                                                                                                        interjections_conf_path,
                                                                                                                        expressions_conf_path,
                                                                                                                        is_chat_file=is_chat_file)
                    # Save interviewer's dialog with and wihtout synonym reducing
                    file_path = CLEANED_DIALOG_INT_PATH + \
                        re.sub(r'\.\w+$', ".txt", file_name)
                    save_dialog_in_file(clean_interviewer_dialog, file_path)

                    if synonyms_conf_path is not None:
                        file_path = CLEANED_DIALOG_INT_SYN_PATH + \
                            re.sub(r'\.\w+$', ".txt", file_name)
                        save_dialog_in_file(
                            clean_interviewer_dialog_syn, file_path)

                # In the case of a text file, there's no dialog information to extract nor a interviewer's dialog, only a participant's dialog.
                elif is_txt_file:
                    participant_dialog = transcript_lines

                cleaning_measures_par, clean_participant_dialog, clean_participant_dialog_syn = clean_transcription(participant_dialog,
                                                                                                                    synonyms_conf_path,
                                                                                                                    interjections_conf_path,
                                                                                                                    expressions_conf_path,
                                                                                                                    is_chat_file=is_chat_file)

                # Save the participant's cleaned dialogs with and without synonym reducing
                file_path = CLEANED_DIALOG_PAR_PATH + \
                    re.sub(r'\.\w+$', ".txt", file_name)
                save_dialog_in_file(clean_participant_dialog, file_path)

                if synonyms_conf_path is not None:
                    file_path = CLEANED_DIALOG_PAR_SYN_PATH + \
                        re.sub(r'\.\w+$', ".txt", file_name)
                    save_dialog_in_file(
                        clean_participant_dialog_syn, file_path)

                # We then add the participant's ID, interview number and status (class) to our results
                results["idParticipant"] = participant_info["idParticipant"]
                results["interviewNumber"] = participant_info["interviewNumber"]
                total_word_count = sum(
                    transcript["totalWordCount"] for transcript in cleaning_measures_par)

                for measure in CLEANING_MEASURES_DICT:
                    measure_value = sum(transcript[measure]
                                        for transcript in cleaning_measures_par)
                    results[measure] = measure_value
                    results[measure + "Ratio"] = measure_value / \
                        total_word_count
                results["totalWordCount"] = total_word_count
                results["status"] = participant_info["status"]

                cleaning_results.append(results)

    return cleaning_results


def clean_transcription(transcription, syn_conf_file=None, interjection_conf_file=None, expression_conf_file=None, is_chat_file=False):
    """
    This function cleans dialogs by extracting symbols, marking and words that reduces transcript's informative value.
    Note that all extracted values are considered as measures that will be exported as FREQUENCY and RATIO for evaluation purpose.

    Parameters
    ----------
    transcription: the transcription that will be cleaned
    synonyms_conf_path: path to a configuration file for synonym reducing task (refer to README.md for more info)
    interjections_conf_path: path to a configuration file for interjection extraction task (refer to README.md for more info)
    expressions_conf_path: path to a configuration file for expression extraction task (refer to README.md for more info)
    is_verbose: boolean value to print processing info to console

    Returns
    -------
    cleaning_measures: array of frequencies of different markers found in the transcription
    complete_clean_dialog: cleaned transcription without synonym reducing
    complete_clean_dialog_syn: cleaned transcription with synonym reducing
    """
    complete_clean_dialog = ''
    complete_clean_dialog_syn = ''
    cleaning_measures = []
    nb_interjections, nb_expressions, nb_synonyms = 0, 0, 0

    for line in transcription:
        curr_cleaning_measures = {}

        # Chat file dialog contains morphological data in the dialog array so we just want the raw dialog
        if is_chat_file:
            clean = line[0]
        else:
            clean = line

        # Here we clean the dialogs in a pipeline of cleaning tasks (view README.md for more info)
        clean, nb_pauses = remove_pauses(clean)
        clean = remove_parentheses(clean)
        if interjection_conf_file is not None:
            clean, nb_interjections = remove_interjections(
                clean, interjection_conf_file)
        if expression_conf_file is not None:
            clean, nb_expressions = remove_expressions(
                clean, expression_conf_file)
        clean, nb_incomplete_words, nb_incomplete_phrases = remove_incomplete_words_and_phrases(
            clean)
        clean, nb_errors = remove_errors(clean)
        clean, nb_repetitions = remove_repetitions(clean)
        clean, nb_retracing = remove_retracings(clean)
        clean = remove_markers_and_symbols(clean)

        total_word_count = len(re.findall(
            r'(?:^|(?<= ))[a-zA-ZÀ-ÿ-,\']+(?= |$)', clean))

        clean = normalize_sentence(clean)

        # To make sure the transcription isn't empty
        if not clean:
            continue

        complete_clean_dialog = complete_clean_dialog + clean + '\n'

        # WE ONLY APPLY SYNONYM REDUCING IF CONF FILE IS PROVIDED
        # We reduce synonyms based on synonym configuration file
        # Synonym reducing helps reduce the dialogs sparcity
        if syn_conf_file is not None:
            clean_syn, nb_synonyms = reduce_synonyms(clean, syn_conf_file)
            clean_syn = normalize_sentence(clean_syn)
            complete_clean_dialog_syn = complete_clean_dialog_syn + clean_syn + '\n'

        # This represents transcript's morphological taggig. Can be used for specific cases.
        # if is_chat_file:
        #     cleaning_measures['originalPosition'] = dialog[2]
        #     cleaning_measures['originalDialog'] = dialog[0]
        #     cleaning_measures['originalTagging'] = dialog[1]

        # Now we save all the cleaning measures extracted from the previous tasks as features for predictive modeling
        for pause_type, value in nb_pauses.items():
            curr_cleaning_measures[pause_type] = value
        curr_cleaning_measures['nbInterjections'] = nb_interjections
        curr_cleaning_measures['nbExpressions'] = nb_expressions
        curr_cleaning_measures['nbIncWords'] = nb_incomplete_words
        curr_cleaning_measures['nbIncPhrases'] = nb_incomplete_phrases
        curr_cleaning_measures['nbErrors'] = nb_errors
        curr_cleaning_measures['nbRepetitions'] = nb_repetitions
        curr_cleaning_measures['nbRetracings'] = nb_retracing
        curr_cleaning_measures['nbSynonyms'] = nb_synonyms
        curr_cleaning_measures['totalWordCount'] = total_word_count

        cleaning_measures.append(curr_cleaning_measures)

    return cleaning_measures, complete_clean_dialog, complete_clean_dialog_syn


def print_results(results):
    print("")
    print("CLEANING RESULTS (Avg. per transcription)")
    print("------------------------")
    print(results[[x for x in results if not x.endswith("Ratio")]].drop(
        'idParticipant', 1).drop('interviewNumber', 1).drop('status', 1).mean())


if __name__ == "__main__":
    main()
