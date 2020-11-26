# -*- coding: utf-8 -*-

"""
The :mod:`src.pseudonymise-participants` implements a processing task that pseudonymise personnal data of patients.

This is an incremental process which can be modified as desired.

Tool parameters
----------
corpus_path: path to the folder containing transcriptions (MUST be a .cha format and contain personnal data in a standardized format, see documentation)
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
from cryptography.fernet import Fernet
import json
import re
from utils.corpus_util import (extract_participant_info,
                               extract_transcript_lines)

PSEUDONYMISED_DIALOGS_INFO_PATH = 'out/PseudonymisedInfo/PAR/'
SECRET_KEY_PATH = 'out/secret.key'

def parse_args():
    parser = argparse.ArgumentParser(description='Extract participants\' information and pseudonymise it.')
    parser.add_argument(dest='corpus_path',
                        help='Path to the folder containing all transcripts')
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

    participants_info = extract_participant_info(args.corpus_path, args.is_verbose)

def extract_participant_info(corpus_path, is_verbose=True):
    """
    Main function that processes every file of the dataset
    """
    participants_info = []
    crypt_key = generate_key()

    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)

        participant_info = {}

        # To make sure we don't process hidden files
        if not file_name.startswith("."):
            if is_verbose:
                print("Processing transcript", file_name)

            transcript_lines = extract_transcript_lines(os.path.join(corpus_path, file_name), is_chat_file=True)

            participant_info = extract_info_from_transcript(file_name, transcript_lines)
            
            pseudonymised_info = pseudonymise_info(participant_info, crypt_key)

            export_pseudonymised_info(pseudonymised_info, file_name)

    print("-------------------")
    print("Pseudonymization task done.")

def extract_info_from_transcript(file_name, lines):
    """
    Extracts participant information from .cha file
    """
    participant_info = {}
    speaker_code = '@ID'
    participant_code = 'PAR'
    iter_lines = iter(lines)
    for line in iter_lines:
        # Extracting the info of the speaker
        if line.startswith(speaker_code):
            p = re.compile('((' + speaker_code + ')|[;\\s])')
            clean = re.sub(p, '', line)      
            info = clean.split('|')

            # To verify that it is the info of the participant (and not the investigator's)
            if(info[2] == participant_code):
                participant_info["age"] = info[3]
                participant_info["gender"] = info[4]
                participant_info["mentalTest"] = info[8]
                break

    return participant_info

def pseudonymise_info(participant_info, key):
    """
    Encrypt participants information
    """
    f = Fernet(key)
    return f.encrypt(json.dumps(participant_info).encode())

def generate_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open(SECRET_KEY_PATH, "wb+") as key_file:
        key_file.write(key)
    return key

def export_pseudonymised_info(pseudonymised_info, file_name):
    """
    Exports pseudonymised information to text file
    """
    file_path = PSEUDONYMISED_DIALOGS_INFO_PATH + re.sub(r'\.\w+$', ".txt", file_name)
    dirname = os.path.dirname(file_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(file_path, "wb") as f:
        f.write(pseudonymised_info)
        f.close()
    return

if __name__ == "__main__":
    main()
