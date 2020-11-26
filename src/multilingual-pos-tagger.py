# -*- coding: utf-8 -*-

"""
The :mod:`src.multilingual-pos-tagger` implements a multilingual FreeLing tagger.
It tags words and punctiation markers in transcriptions.
Then, it will convert most (not all) tags to there universal form to simplify there analysis.

n.b. FreeLing 4.0 must be installed in order to use this tool

Tool parameters
----------
corpus_path: path to the folder containing CLEANED transcriptions (MUST contain only transcription files)
freeling_config_path: path to the FreeLing configuration file (varies from one language to another)
universal_map_path: path to a universal map configuration file (refer to README.md for more info)
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

from utils.corpus_util import obtain_corpus_classes
from utils.nlp_util import UniversalPOS

# CONSTANTS
TAGGED_DIALOG_OUTPUT_PATH = "out/TaggedDialogs/PAR/"

def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual pos distribution calculator.')
    parser.add_argument(dest='corpus_path',
                    help='path to the folder containing all normalized transcripts')
    parser.add_argument(dest='freeling_config_path',
                    help='path to FreeLing configuration file')
    parser.add_argument('-u', '--universal_map_path', dest='universal_map_path',
                    help='path to universal mapping of POS tags from FreeLing')
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
    if not os.path.exists(args.freeling_config_path):
        print("Given FreeLing config path doesn't exist.")
        sys.exit(1)
    if args.universal_map_path and not os.path.exists(args.universal_map_path):
        print("Given universal map path doesn't exist.")
        sys.exit(1)

    corpus_classes = obtain_corpus_classes(args.corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    if args.universal_map_path:
        universal_mapper = UniversalPOS(args.universal_map_path)
    else:
        universal_mapper = None

    process_corpus(args.corpus_path, args.freeling_config_path, universal_mapper, args.is_verbose)

    print("-------------------")
    print("FreeLing tagging task done.")

def process_corpus(corpus_path, freeling_config_path, universal_mapper=None, is_verbose=False):
    """
    This is the main function that processes given corpus to tag it. It iterates thru every transcriptions and tag them.
    Finally, it converts some tag to there universal form (e.g.: VBG --> VERB)

    Parameters
    ----------
    corpus_path: path to a folder containing all transcriptions
    freeling_config_path: path to the FreeLing configuration file.
    universal_mapper: path to the universal mapping file (refer to README.md for more info)
    is_verbose: boolean value to print processing info to console
    """

    # FREELING command (must have FreeLing installed on computer)
    command = "analyze -f " + freeling_config_path
    
    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)

        # To make sure we don't process hidden files
        if not file_name.startswith("."):
            if is_verbose:
                    print("Processing transcript", file_name)

            file_path = corpus_path + "/" + file_name
            output_file_path = TAGGED_DIALOG_OUTPUT_PATH + "/" + file_name

            tag_dialogs(file_path, output_file_path, freeling_config_path)

            if universal_mapper:
                universalize_tags(output_file_path, universal_mapper)

def tag_dialogs(dialog_file_path, output_file_path, freeling_config_path):
    """
    This function calls FreeLing tool.

    Parameters
    ----------
    dialog_file_path: path to the transcription that will be tagged
    output_file_path: output path of the tagged transcription
    freeling_config_path: FreeLing configuration file
    """

    dirname = os.path.dirname(output_file_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    command = "analyze -f " + freeling_config_path + " <" + dialog_file_path + " >" + output_file_path
    
    # We call the FreeLing command in a subprocess
    try:
        p = subprocess.run(command, shell=True, check=True, universal_newlines=True, stdout = subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    
    return 

def universalize_tags(dialog_file_path, universal_mapper):
    """
    This function will go thru each tagged dialogs and simply tags to their universal form
    In our case, we only simplify the following tags : ADJ, CONJ, NOUN, ADP, VERB, AUX_VERB

    Parameters
    ----------
    dialog_file_path: path to the transcription that will be universalized
    universal_mapper: the universal mapper object
    """

    tags = []
    sentence_tags = []

    with open(dialog_file_path, "r") as tag_file:
        for line in tag_file:
            columns = line.replace('\n','').split(' ')
                
            # If there are at least two columns, then it is tagged in the form: "falling fall VBG [1]"
            if(len(columns) == 4):
                # tupla: (Original_word, lemma, tag, confidence)
                universal_tag = universal_mapper.get_universal_tag(columns[2])
                # if there's a universal tag, we set it
                if universal_tag:
                    tupla = (columns[0], columns[1], universal_tag, columns[3])
                else:
                    tupla = (columns[0], columns[1], columns[2], columns[3])
                # We add the tupla to the sentence list
                sentence_tags.append(tupla)

            # If it is an empty line, then it is the end of a sentence (columns:['']):
            elif(len(columns) == 1):
                # If there is something tagged in the sentence, save it in tags
                if(len(sentence_tags) > 0):
                    tags.append(sentence_tags)
                # Clean the sentence list to beggin with the next sentence
                sentence_tags = []
    tag_file.close()

    # Now we re-write the file with the universal tags
    with open(dialog_file_path, 'w') as tag_file:
        for tag in tags:
            tag_file.write('\n'.join('%s %s %s %s' % x for x in tag)) 
            tag_file.write('\n\n')
    tag_file.close()        
    
if __name__ == "__main__":
    main()
