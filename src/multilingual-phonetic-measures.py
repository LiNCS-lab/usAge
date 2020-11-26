# -*- coding: utf-8 -*-

"""
The :mod:`src.multilingual-phonetic-measures` implements a multilingual tool that calculates phonetic metrics from audio signals.
It calculates the first 13 MFCCs (Mel-frequency cepstral coefficients) and extracts the mean, skewness, kurtosis and variance of those.
Those measures are widely used in the litterature of cognitive impairment as it contains valuable information about a patients current health.
It is mainly used to add more information when comes to modeling and analyzing progression of a disease in a cohort of patients.

Tool parameters
----------
audio_corpus_path: path to the folder containing audio files (.mp3 or .wav)
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
import os
import re
import sys

import numpy as np
import pandas as pd
import scipy.io.wavfile as wav
from pydub import AudioSegment
from python_speech_features import mfcc
from scipy.stats import kurtosis, skew

from utils.corpus_util import obtain_corpus_classes, extract_participant_info
from utils.data_util import export_dataframe
from utils.pickle_util import read_pickle

# Constants
DIALOG_INFO_PATH = "out/DialogsInfo/PAR/"
AUDIO_CUT_OUTPUT_PATH = "out/AudioCuts/"
PHONETIC_FEATURES_EXPORT_PATH = "out/ExtractedFeatures/phonetic_features.csv"
PHONETIC_FEATURES = ["idParticipant", "interviewNumber", 
               "mean_1", "mean_2", "mean_3", "mean_4", "mean_5", "mean_6", "mean_7", "mean_8", 
               "mean_9", "mean_10", "mean_11", "mean_12", "mean_13",
               "kurtosis_1", "kurtosis_2", "kurtosis_3", "kurtosis_4", "kurtosis_5", "kurtosis_6", 
               "kurtosis_7", "kurtosis_8", "kurtosis_9", "kurtosis_10", "kurtosis_11", "kurtosis_12", 
               "kurtosis_13",
               "skewness_1", "skewness_2", "skewness_3", "skewness_4", "skewness_5", "skewness_6", 
               "skewness_7", "skewness_8", "skewness_9", "skewness_10", "skewness_11", "skewness_12", 
               "skewness_13",
               "variance_1", "variance_2", "variance_3", "variance_4", "variance_5", "variance_6", 
               "variance_7", "variance_8", "variance_9", "variance_10", "variance_11", "variance_12", 
               "variance_13",
               "status"]
# MFCC parameters               
WINLEN = 0.025
NFFT = 1200

def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual phonetic measures calculator.')
    parser.add_argument(dest='audio_corpus_path',
                    help='path to the folder containing all audios of the corpus')
    parser.add_argument('-f', '--features_output_path', dest='features_output_path',
                    help='path to folder where phonetic features will be stored (.csv file)')
    parser.add_argument('-v', '--verbose', dest='is_verbose', default=False, action='store_true',
                    help='print processing info')
    return parser.parse_args()

def main():
    args = parse_args()

    if not os.path.isdir(args.audio_corpus_path):
        print("Given audio corpus path is not a directory")
        sys.exit(1)
    if not os.path.exists(args.audio_corpus_path):
        print("Given audio corpus path doesn't exist.")
        sys.exit(1)

    corpus_classes = obtain_corpus_classes(args.audio_corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    phonetic_matrix = process_corpus(args.audio_corpus_path, is_verbose=args.is_verbose)

    df_phonetic_results = pd.DataFrame(phonetic_matrix, columns=PHONETIC_FEATURES)
    
    print_results(df_phonetic_results)

    output_path = args.features_output_path if args.features_output_path else PHONETIC_FEATURES_EXPORT_PATH
    export_dataframe(df_phonetic_results, output_path)

def process_corpus(audio_corpus_path, is_verbose=False):
    """
    This is the main function that processes given audio corpus to calculate phonetic measures. (13 first MFCCs)

    Parameters
    ----------
    audio_corpus_path: path to a folder containing all audios (.mp3 or .wav)
    is_verbose: boolean value to print processing info to console

    Returns
    ----------
    phonetics_matrix: array of phonetic metrics of the 13 first MFCCs (mean, skewness, kurtosis and variance)
    """

    phonetics_matrix = []

    for file in os.listdir(audio_corpus_path):
        file_name = os.fsdecode(file)

        if not file_name.startswith("."): 
            if is_verbose:
                print("Processing transcript", file_name)

            file_path = audio_corpus_path + "/" + file_name

            # If file is mp3, convert to wav
            if file_name.lower().endswith(".mp3"):
                try:
                    song = AudioSegment.from_mp3(file_path)
                    song = song[: 30 * 1000 ]
                    song.export(file_path[:-3] + "wav", format="wav")
                    pattern = re.compile(file_path, re.IGNORECASE)
                    pattern.sub(".mp3", ".wav")
                except Exception as e:
                    print(e)

            participant_info = extract_participant_info(file_name)

            # To make sure it doesn't process a file other than .wav format
            if file_path.lower().endswith(".wav"):
                phonetics = estimate_phonetics(file_path)
                phonetics_matrix.append(np.concatenate([[participant_info["idParticipant"]], 
                                                        [participant_info["interviewNumber"]], 
                                                        np.mean(phonetics, axis=0),
                                                        kurtosis(phonetics, axis=0),
                                                        skew(phonetics, axis=0),
                                                        np.var(phonetics, axis = 0),
                                                        [participant_info["status"]]]))

    return phonetics_matrix

def estimate_phonetics(dialog_audio_path):
    """
    This function estimates phonetic metrics of an audio. It uses the tool mfcc of the python_speech_features library.
    We hardcoded the number of cepstrum since in most of cases we only want the 13 first ones.

    Parameters
    ----------
    dialog_audio_path: path to a an audio file

    Returns
    ----------
    mfcc_features: 13 first mfcc measures
    """

    (rate, sig) = wav.read(dialog_audio_path)
    
    mfcc_features = mfcc(sig, rate, winlen=WINLEN, nfft=NFFT, numcep=13)
    
    return mfcc_features

def print_results(results):
    print("")
    print("PHONETIC MEASURES RESULTS (Avg.)")
    print("------------------------")
    print(results.drop('idParticipant', 1).drop('interviewNumber', 1).drop('status', 1).astype(float).mean())

if __name__ == "__main__":
    main()
