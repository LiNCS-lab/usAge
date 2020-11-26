import os
import re
from utils.nlp_util import Tag
from nltk.tokenize import sent_tokenize

# This function will return classes found in corpus data set
# E.g. : AD_101-1.txt file indicates there's a AD class in corpus
def obtain_corpus_classes(corpus_path):
    classes_set = set()

    for file_name in os.listdir(corpus_path):
        class_name = file_name.split("_", 1)[0]

        if class_name.isalpha():
            classes_set.add(class_name)
    
    return classes_set

# This function will return transcript info based on file name
# E.g. : AD_101-1.txt
# Status -> AD
# Participant nb -> 101
# Inteview nb -> 1
def extract_participant_info(file_name):
    participant_info = {}
    pattern = re.compile(r'(.*)_([0-9]+)-([0-9a-z])+')
    re_participant_info = re.search(pattern, file_name)

    if len(re_participant_info.groups()) != 3:
        print("File name with wrong format :", file_name)
        print("Should be status_idParticipant-interviewNumber.*")
    else:
        participant_info["status"] = re_participant_info.group(1)
        participant_info["idParticipant"] = re_participant_info.group(2)
        participant_info["interviewNumber"] = re_participant_info.group(3)

    return participant_info

# This function extracts lines of transcripts as sentences. This method is dependant on the transcript format.
def extract_transcript_lines(file_path, is_chat_file=True):
    with open(file_path, 'r') as file:
        lines = file.read()
    
    if is_chat_file:
        lines = lines.replace('\r', '').split('\n')
    else:
        lines = sent_tokenize(lines)

    file.close()
    
    return lines

# This function extracts lines of transcripts as sentences. This method is dependant on the transcript format.
def extract_freeling_tags(file_path):
    tags = []

    file = open(file_path, 'r')
    for line in file:
        if len(line.split(' ')) == 4: # 
            tag = line.split(' ')
            tags.append(Tag(tag[0], tag[1], tag[2], tag[3]))
        else:
            tags.append("\n")
        
    file.close()
    return tags

# This function extract dialogs from transcripts of a 2-speaker dialog.
def extract_two_speaker_dialogs(lines, speaker_1_code, speaker_2_code):
    speaker_1_dialog = []
    speaker_2_dialog = []
    morph_code = '%mor:\t'
    count = 0 # count will register the order of each dialog
    is_morph_code = False
    curr_dialog = [''] * 4

    iter_lines = iter(lines) # create an iterative object
    for line in iter_lines:
        tagged = '' # tagged will save the morphological tagging
        
        # If there is no code at the start of the line we append to the current dialog
        if line.startswith("\t"):
            line = line.replace("\t", " ")
            if is_morph_code:
                curr_dialog[1] += line
            else:
                curr_dialog[0] += line

        # Extracting morphology
        elif line.startswith(morph_code):
            curr_dialog[1] = line[6:] # taking out the %mor:\t tag
            is_morph_code = True

        else:
            is_morph_code = False
            if count > 0 and curr_dialog[0]:
                curr_dialog[2] = count
                if curr_dialog[3] == speaker_1_code:
                    speaker_1_dialog.append(curr_dialog)
                elif curr_dialog[3] == speaker_2_code:
                    speaker_2_dialog.append(curr_dialog)
                curr_dialog = [''] * 4

            # Extracting the dialog of the participant
            if line.startswith(speaker_1_code):
                curr_dialog[0] = line[len(speaker_1_code) + 1 :] # taking out the speaker1 code
                count += 1
                curr_dialog[3] = speaker_1_code

            # Extracting the dialog of the investigator (interviewer)
            elif line.startswith(speaker_2_code):
                curr_dialog[0] = line[len(speaker_2_code) + 1 :] # taking out the speaker2 code
                count += 1
                curr_dialog[3] = speaker_2_code

    return (speaker_1_dialog, speaker_2_dialog)