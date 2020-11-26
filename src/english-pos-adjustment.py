# -*- coding: utf-8 -*-

"""
The :mod:`src.english-pos-adjustment` implements an english FreeLing POS tag adjustment task.
It is used to modify some tags that might have been wrongfully tagged by FreeLing 
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

from utils.corpus_util import extract_freeling_tags, obtain_corpus_classes, extract_participant_info
from utils.data_util import save_tags_in_file
from utils.nlp_util import Tag
from utils.pickle_util import read_pickle
from utils.nlp_util import UniversalPOS

# CONSTANTS
ADJUSTED_DIALOG_OUTPUT_PATH = "out/TaggedDialogsAdjusted/PAR/"

class Results:
    compose_count: int = 0
    conj_count: int = 0
    tag_reduction_count: int = 0
    looks_like_count: int = 0
    aux_verb_count: int = 0
    
def parse_args():
    parser = argparse.ArgumentParser(description='Multilingual pos distribution calculator.')
    parser.add_argument(dest='corpus_path', 
                    help='path to the folder containing all transcripts tagged by FreeLing')
    parser.add_argument('-v', '--verbose', dest='is_verbose', default=False, action='store_true',
                    help='print processing info')
    return parser.parse_args()

def main():
    args = parse_args()

    # On vérifie que les path sont valide
    if not os.path.isdir(args.corpus_path):
        print("Given corpus path is not a directory")
        sys.exit(1)
    if not os.path.exists(args.corpus_path):
        print("Given corpus path doesn't exist.")
        sys.exit(1)

    # On énumère les différentes classes du dataset (e.g : AD, SD, CTRL, etc.)
    corpus_classes = obtain_corpus_classes(args.corpus_path)

    if args.is_verbose:
        print("CORPUS CLASSES")
        print("------------------------")
        print(corpus_classes)

    adjustment_results = process_corpus(args.corpus_path, args.is_verbose)

    print_results(adjustment_results)
    
def process_corpus(corpus_path, is_verbose=False):
    """
    This is the main function that processes given corpus to adjust tags. It iterates thru every transcriptions and process tag adjustments.

    Parameters
    ----------
    corpus_path: path to a folder containing all transcriptions
    is_verbose: boolean value to print processing info to console

    Returns
    -------
    results: list of different types of adjustment made on the corpus
    """

    adjustment_count = 0
    results = Results()

    for file in os.listdir(corpus_path):
        file_name = os.fsdecode(file)  

        # To make sure we don't process hidden files
        if not file_name.startswith("."): 
            if is_verbose:
                print("Processing transcript", file_name)

            participant_info = extract_participant_info(file_name)

            freeling_tags = extract_freeling_tags(os.path.join(corpus_path, file_name))

            adjusted_dialog_tags, results = adjust_pos_tags(freeling_tags, results, is_verbose=is_verbose)

            export_file_path = ADJUSTED_DIALOG_OUTPUT_PATH + file_name
            save_tags_in_file(adjusted_dialog_tags, export_file_path)

    return results

def adjust_pos_tags(pos_tags, results, is_verbose=False):
    """
    This function adjust POS tags made by FreeLing.

    Parameters
    ----------
    pos_tags: list of POS tags
    results: list of previous results (increments current results)
    is_verbose: boolean value to print processing info to console

    Returns
    -------
    adjusted_pos_tags: list of adjusted POS tags
    results: list of different types of adjustment made on the current list of POS tags
    """

    adjusted_pos_tags = []

    dialog = []
    curr_sentence = []
    for tag in pos_tags:
        if type(tag) is Tag:
            curr_sentence.append(tag)
        else:
            dialog.append(curr_sentence)
            curr_sentence = []

    for sentence in dialog:
        adjusted_sentence, results.compose_count = compose_tagging(sentence, results.compose_count)
        #adjusted_sentence, results.conj_count = resolve_conjunctions(adjusted_sentence, results.conj_count)
        #adjusted_sentence, results.tag_reduction_count = recude_tags(adjusted_sentence, results.tag_reduction_count)
        adjusted_sentence, results.looks_like_count = extract_looks_like(adjusted_sentence, results.looks_like_count)
        adjusted_sentence, results.aux_verb_count = identify_auxiliary_verbs(adjusted_sentence, results.aux_verb_count)

        adjusted_pos_tags.extend(adjusted_sentence)
        adjusted_pos_tags.append("\n")
    
    return adjusted_pos_tags, results

def compose_tagging(current_sentence, adjustment_count):
    """
    This function compose POS tags made by FreeLing.

    Parameters
    ----------
    current_sentence: list of words in the current sentence to be processed
    adjustment_count: previous count of the number of adjustments made in the current sentence for the compose_tagging function

    Returns
    -------
    adjusted_sentence: list of adjusted POS tags
    adjusted_count: number of adjustments made in the current sentence for the compose_tagging function
    """

    be_pos_flag = False

    adjusted_sentence = []

    for current_tag in current_sentence:
        adjusted_tag = current_tag
        # We don't incorporate the word "throat", because in DementiaBank
        # it is a mark of participants clearing their throats
        if(current_tag.lemma == "throat"):
            del current_tag
            continue
        
        if(current_tag.tag == UniversalPOS.VERB_TAG and current_tag.original == "\'re" and current_tag.lemma == "\'re"):
            # For those cases in which the verb "be"
            # in the form "'re" is not lemmatized as "be"
            adjusted_tag = Tag(current_tag.original, "be", current_tag.tag, current_tag.certainty)
            adjustment_count += 1
        
        if(be_pos_flag):
            # Some verbs ending in "ing" (VBG) were incorrectly marked as nouns
            # Example: "while/IN woman/NN 's/POS walking/NN with/IN ..."
            # Should be: "while/IN woman/NN 's/POS walking/VBG with/IN ..."
            if(current_tag.original.endswith("ing") and current_tag.tag != UniversalPOS.VERB_TAG):
                adjusted_tag = Tag(current_tag.original, current_tag.lemma, UniversalPOS.VERB_TAG, current_tag.certainty)
                adjustment_count += 1

            if(current_tag.lemma != "throat"):
                be_pos_flag = False
                
        if(current_tag.tag == UniversalPOS.ADP_TAG and current_tag.original == "\'s" and current_tag.lemma == "\'s"):
            # For those cases in which the verb "be" in the form "'s" was tagged
            # as "POS" -possesive adposition- (vast majority of 's/POS mentions in DementiaBank)
            adjusted_tag = Tag(current_tag.original, "be", UniversalPOS.VERB_TAG, current_tag.certainty)
            be_pos_flag = True
            adjustment_count += 1

        adjusted_sentence.append(adjusted_tag)

    return adjusted_sentence, adjustment_count

def resolve_conjunctions(current_sentence, adjustment_count):
    # TODO - Should we take this in concideration or not? If yes, we have to do universalisation after adjusting.
    # Regular expressions for tags:
    # Nouns:
    noun_p = "[a-zA-Z0-9_-]*/[a-zA-Z0-9_-]*/N[a-zA-Z0-9_-]*" 
    # Verbs: No third person
    verb_nothird_p = "[a-zA-Z0-9_-]*/[a-zA-Z0-9_-]*/VBP"
    # Verbs: Any verb
    verb_p = "[a-zA-Z0-9_-]*/[a-zA-Z0-9_-]*/V[a-zA-Z0-9_-]*"
    # Conjunction "and":
    and_p  = "and/and/CC"
    
    # Pattern: N1 'and' N2 V
    p = re.compile(noun_p + ' ' + and_p + ' ' + noun_p + ' ' + verb_nothird_p + '[ ' + verb_p + ']?')
    # Pattern for capturing the elements of interest inside the pattern (N1, N2 and V)
    p_capture = re.compile('(' + noun_p + ') ' + and_p + ' (' + noun_p + ') (' + verb_nothird_p + '[ ' + verb_p + ']?)')
    
    adjusted_sentence = []

    adjusted_sentence = current_sentence
    
    utterance = ""
    for pos_tag in adjusted_sentence:
        if(pos_tag.tag == UniversalPOS.NOUN_TAG or  
            pos_tag.tag == UniversalPOS.VERB_TAG or  
            pos_tag.tag == UniversalPOS.CONJ_TAG or
            pos_tag.tag == UniversalPOS.ADP_TAG or 
            pos_tag.tag == UniversalPOS.PRON_TAG):
                utterance += pos_tag.original + "/" + pos_tag.lemma + "/" + pos_tag.tag + " "
    
    # Finding coincidences with the pattern N1 'and' N2 V in the utterance:
    coincidences = re.findall(p, utterance)
    
    if(len(coincidences) > 0):
        adjusted_sentence = []

        # Divide the utterance in 2 parts: 'before' (utterance_split[0]) and 'after' (utterance_split[1]) the pattern
        utterance_split = utterance.split(coincidences[0])
        
        # Captures the elements of interest inside the pattern 
        # (N1 = coincidences[0][0], N2 = coincidences[0][1] and V = coincidences[0][2])
        coincidences = re.findall(p_capture, utterance)
        
        # Generates two new sentences: N1 V, and N2 V
        #    Sentence 1: before the pattern + N1 V + after the pattern
        sentence = utterance_split[0] + ' ' + coincidences[0][0] + ' ' + coincidences[0][2] + utterance_split[1]
        tuplas = convertIntoTuples(sentence)
        adjusted_sentence.append(tuplas)
        adjusted_sentence.append("\n")
        
        #    Sentence 2: before the pattern + N2 V + after the pattern
        sentence = utterance_split[0] + ' ' + coincidences[0][1] + ' ' + coincidences[0][2] + utterance_split[1]
        tuplas = convertIntoTuples(sentence)
        adjusted_sentence.append(tuplas)
        adjusted_sentence.append("\n")

    return adjusted_sentence, adjustment_count

def recude_tags(current_sentence, adjustment_count):
    adjusted_sentence = current_sentence
    previous_tag = ""
    existential_flag = 0
    pronoun_flag = 0
    be_plus_adj_flag = False
    
    # To read tuple by tuple (token,tag):
    for pos_tag in current_sentence:
        if be_plus_adj_flag:
            # Turn off be+Adj flag
            be_plus_adj_flag = False
            
            if pos_tag.tag == UniversalPOS.NOUN_TAG:
                tupla_be = Tag(adjusted_sentence[-1].original, "be", adjusted_sentence[-1].tag, "1")
                # Deleting the "+Adj" tuple from the lemmatization
                del adjusted_sentence[-1]
                # Recovering the original "be" verb tuple:
                adjusted_sentence.append(tupla_be)
                adjustment_count += 1
        
        # To add nouns and prepositions (without restrictions)
        if pos_tag.tag == UniversalPOS.NOUN_TAG or pos_tag.tag == UniversalPOS.ADP_TAG:
            adjusted_sentence.append(pos_tag)
            previous_tag = pos_tag.tag
            existential_flag = 0
            pronoun_flag = 0
        
        # To add a verb no preceded by "there is" or "it" (without restrictions)
        # The verb "seems" is irrelevant for this task.
        if pos_tag.tag == UniversalPOS.VERB_TAG and pos_tag.lemma != "seem":
            if pronoun_flag == 0 and existential_flag == 0:
                adjusted_sentence.append(pos_tag)
                previous_tag = pos_tag.tag
                existential_flag = 0
                pronoun_flag = 0
        
        # For adding adjectives, only preceded by the verb "to be":
        # Edit the last tuple, so that the lemma is "be/adjective":
        if pos_tag.tag == UniversalPOS.ADJ_TAG and previous_tag == UniversalPOS.VERB_TAG:
            if adjusted_sentence[-1].lemma == "be":
                adjusted_pos_tag = Tag(adjusted_sentence[-1].original, adjusted_sentence[-1].lemma+"+" + pos_tag.lemma, adjusted_sentence[-1].tag, adjusted_sentence[-1].certainty)
                del adjusted_sentence[-1]
                adjusted_sentence.append(adjusted_pos_tag)
                previous_tag = adjusted_pos_tag.tag
                be_plus_adj_flag = True
                existential_flag = 0
                pronoun_flag = 0
                adjustment_count += 1
        
        # To add the "and" conjunction (only conjunction allowed): 
        if pos_tag.tag == UniversalPOS.CONJ_TAG and pos_tag.lemma == "and": 
            adjusted_sentence.append(pos_tag)
            previous = pos_tag.tag
            existential_flag = 0
            pronoun_flag = 0
                
        # +++++++++++++++++++++++++++++++++++++++++++++++++++
        # For "there is" / "there are" 
        # change 'EX' or 'RB' tag for noun 'NN' tag
        # For the pronoun "it"/PR .*/V:
        # such as "it is" / "it was" / "it seems"
        # change 'PRP' tag for noun 'NN' tag
        # Don't consider the pronoun 'I' with it's verb (I/PR .*V):
        # such as "I think" / "I guess" / "I see"
        
        if pos_tag.lemma == "there":
            existential_tag = pos_tag
            existential_flag = 1
            pronoun_flag = 0
            
        if pos_tag.tag == UniversalPOS.PRON_TAG:
            if pos_tag.lemma == "it":
                pronoun_flag = 1
            else:
                if pos_tag.lemma == "i":
                    pronoun_flag = 2
                '''
                else:
                    reducedLine.append(tupla)
                    previous = tupla[2]
                    pronounFlag=0
                '''
            pronoun_tag = pos_tag
            existential_flag = 0
        
        if pos_tag.tag == UniversalPOS.VERB_TAG:
            if existential_flag == 1 and pos_tag.lemma == "be":
                existential_tag.tag = UniversalPOS.NOUN_TAG
                adjusted_sentence.append(existential_tag) # Adding the existential 'there'
                adjusted_sentence.append(pos_tag) # Adding the verb
                previous_tag = pos_tag.tag
                existential_flag = 0
                adjustment_count += 1
            else:
                if existential_flag == 1 and pos_tag.lemma != "seem":
                    # We won't add the existential tuple; just the verb
                    adjusted_sentence.append(pos_tag) # Adding the verb
                    previous_tag = pos_tag.tag
                    existential_flag = 0
            
            # To avoid entering "it seems"
            if pronoun_flag == 1 and pos_tag.lemma != "seem":
                pronoun_tag.tag = UniversalPOS.NOUN_TAG
                adjusted_sentence.append(pronoun_tag) # Adding the pronoun 'it' with the 'NN' tag
                adjusted_sentence.append(pos_tag) # Adding the verb
                previous_tag = pos_tag.tag
                pronoun_flag = 0
                adjustment_count += 1
                
            if pronoun_flag == 2:
                # We don't register the verb for phrases with the pronoun 'I'
                # such as 'I think', 'I know', 'I see'
                pronoun_flag = 0

    return adjusted_sentence, adjustment_count

def extract_looks_like(current_sentence, adjustment_count):
    """
    This function removes "looks like" form found in transcriptions as it is not wanted in the context of the
    Cookie Theft Picture description task.

    Parameters
    ----------
    current_sentence: list of words in the current sentence to be processed
    adjustment_count: previous count of the number of adjustments made in the current sentence for the compose_tagging function

    Returns
    -------
    adjusted_sentence: list of adjusted POS tags
    adjusted_count: number of adjustments made in the current sentence for the compose_tagging function
    """

    adjusted_sentence = []
    look_flag = False
    it_flag = False
    as_flag = False

    for pos_tag in current_sentence:
        if(pos_tag.lemma == "it"):
            # Adding the 'it' tuple:
            adjusted_sentence.append(pos_tag)
            # turning on the "it" flag
            it_flag = True
        else:
            if(pos_tag.lemma == "look"):
                # Adding the 'look' tuple:
                adjusted_sentence.append(pos_tag)
                # turning on the "Look" flag
                look_flag = True
            else:
                if(pos_tag.lemma == "like"):
                    if(look_flag):
                        # deleting the verb 'look'
                        del adjusted_sentence[-1]
                        adjustment_count += 1
                        if(it_flag):
                            # deleting the preposition "it" (marked as a noun)
                            del adjusted_sentence[-1]
                            adjustment_count += 1
                    else:
                        # Adding the tuple "like":
                        adjusted_sentence.append(pos_tag)
                        
                    look_flag = False
                    it_flag = False
                    as_flag = False
                else:
                    if(pos_tag.lemma =="as"):
                        if(look_flag):
                            as_flag = True
                        # Adding the 'as' tuple:
                        adjusted_sentence.append(pos_tag)
                    else:
                        if(pos_tag.lemma == "though" or pos_tag.lemma == "if"):
                            if(as_flag):
                                # deleting 'as'
                                del adjusted_sentence[-1]
                                adjustment_count += 1
                                # deleting 'look'
                                del adjusted_sentence[-1]
                                adjustment_count += 1
                                if(it_flag):
                                    # deleting the preposition "it" (marked as a noun)
                                    del adjusted_sentence[-1]
                                    adjustment_count += 1
                            look_flag = False
                            it_flag = False
                            as_flag = False                        
                        else:
                            adjusted_sentence.append(pos_tag)
                            look_flag = False
                            it_flag = False
                            as_flag = False
    
    return adjusted_sentence, adjustment_count

def identify_auxiliary_verbs(current_sentence, adjustment_count):
    """
    This function identifies auxiliary verbs as they are not explicitly tagged with FreeLing
    This rule-based function is made accordingly with https://en.wikipedia.org/wiki/Auxiliary_verb#List_of_auxiliaries_in_English
    We cover most of the auxiliary verbs, but this is part of an incremental work and can be adapted.

    Parameters
    ----------
    current_sentence: list of words in the current sentence to be processed
    adjustment_count: previous count of the number of adjustments made in the current sentence for the compose_tagging function

    Returns
    -------
    adjusted_sentence: list of adjusted POS tags
    adjusted_count: number of adjustments made in the current sentence for the compose_tagging function
    """

    adjusted_sentence = []

    for idx, current_tag in enumerate(current_sentence):
        adjusted_tag = current_tag
        # "Be" (progressive) E.g.: He is sleeping.
        # "Be" (passive) E.g.: They were seen.
        # "Can" (deontic) E.g.: I can swim.
        # "Can" (epistemic) E.g.: Such things can help.
        # "Could" (deontic) E.g.: I could swim..
        # "Could" (epistemic) E.g.: That could help.
        # "Have" (perfect aspect) E.g.: They have understood.
        # "May" (epistemic modality) E.g.: That may take place.
        # "Might" (epistemic modality) E.g.: We might give it a try.
        # "Must" (epistemic modality) E.g.: It must have rained.
        # "Should" (deontic modality) E.g.: You should listen.
        # "Should" (epistemic modality) E.g.: That should help.
        # "Will" (epistemic modality) E.g.: We will eat pie.
        # "Will" (future tense) E.g.: The sun will rise tomorrow at 6:03.
        # "Will" (habitual aspect) E.g.: He will make that mistake every time.
        # "Would" (epistemic modality) E.g.: Nothing would accomplish that.
        # "Would" (future-in-the-past tense) E.g.: After 1990, we would do that again.
        if (current_tag.lemma == "be" or current_tag.lemma == "can" or current_tag.lemma == "have" or current_tag.lemma == "may" or current_tag.lemma == "must" 
                or current_tag.lemma == "should" or current_tag.lemma == "will") and (current_tag.tag == UniversalPOS.VERB_TAG 
                and (idx < len(current_sentence) - 1) and current_sentence[idx + 1].tag == UniversalPOS.VERB_TAG):
            adjusted_tag = Tag(current_tag.original, current_tag.lemma, UniversalPOS.AUX_VERB_TAG, current_tag.certainty)
            adjustment_count += 1
            
        # "Do" (do-support/emphasis) E.g.: You did not understand.
        # "Do" (question) E.g.: Do you like it?
        # "May" (deontic modality) E.g.: May I stay?
        # "Must" (deontic modality) E.g.: You must not mock me.
        # "Need" (deontic modality) E.g.: You need not water the grass. 
        # "Ought" (deontic modality) E.g.: You ought to play well.
        # "Shall" (deontic modality) E.g.: You shall not pass.
        # "Would" (habitual aspect) E.g.: Back then we would always go there.
        elif (current_tag.lemma == "do" or current_tag.lemma == "may" or current_tag.lemma == "must" or current_tag.lemma == "need" or current_tag.lemma == "shall"
                or current_tag.lemma == "would") and (current_tag.tag == UniversalPOS.VERB_TAG 
                and (idx < len(current_sentence) - 2) and current_sentence[idx + 2].tag == UniversalPOS.VERB_TAG):
            adjusted_tag = Tag(current_tag.original, current_tag.lemma, UniversalPOS.AUX_VERB_TAG, current_tag.certainty)
            adjustment_count += 1
        
        adjusted_sentence.append(adjusted_tag)

    return adjusted_sentence, adjustment_count


# Prints results in console
def print_results(adjustement_results):
    print("")
    print("POS ADJUSTMENT RESULTS")
    print("------------------------")
    for attr, value in adjustement_results.__dict__.items():
        print(attr, value)
    
if __name__ == "__main__":
    main()
