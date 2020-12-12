import re
import os
import json

# This function removes pauses from dialogs.
# Pauses should be marked as following : 
# Short pause : (.), Medium pause : (..), Long pause : (...), Other pause : (....) or more dots
def remove_pauses(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    nb_pauses = {}
    
    nb_pauses["nbPausesTotal"] = 0
    nb_pauses["nbPausesShort"] = 0
    nb_pauses["nbPausesMedium"] = 0
    nb_pauses["nbPausesLong"] = 0
    nb_pauses["nbPausesOther"] = 0
    
    # CASE 1: short pauses: (.)
    p = re.compile('\\(\\.\\)')
    pauses = len(re.findall(p, clean))
    clean = re.sub(p, '', clean)
    nb_pauses["nbPausesTotal"] = nb_pauses["nbPausesTotal"] + pauses
    nb_pauses["nbPausesShort"] = pauses
    
    # CASE 2: medium pauses: (..)
    p = re.compile('\\(\\.\\.\\)')
    pauses = len(re.findall(p, clean))
    clean = re.sub(p, '', clean)
    nb_pauses["nbPausesTotal"] = nb_pauses["nbPausesTotal"] + pauses
    nb_pauses["nbPausesMedium"] = pauses
    
    # CASE 3: long pauses: (...)
    p = re.compile('\\(\\.\\.\\.\\)')
    pauses = len(re.findall(p, clean))
    clean = re.sub(p, '', clean)
    nb_pauses["nbPausesTotal"] = nb_pauses["nbPausesTotal"] + pauses
    nb_pauses["nbPausesLong"] = pauses
    
    # CASE 4: other (longer) pauses: 
    p = re.compile('\\(\\.\\.\\.(\\.+)\\)')
    pauses = len(re.findall(p, clean))
    clean = re.sub(p, '', clean)
    nb_pauses["nbPausesTotal"] = nb_pauses["nbPausesTotal"] + pauses
    nb_pauses["nbPausesOther"] = pauses
    
    return (clean, nb_pauses)

# This function simply removes any parantheses found in dialog
def remove_parentheses(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    
    p = re.compile('[\\(\\)]')
    clean = re.sub(p, '', clean)

    return (clean)

# This function removes interjections found in dialog based on a configuration file provided.
# Configuration file should simply list (line by line) every interjections that could be found in the dialog.
# Chat files mark interjections as following : &-interjection or &=interjection (e.g. &-uh or &=uh)
# Text files could simply have interjections without markers
def remove_interjections(dialog, interjections_conf_file):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    nb_interjections = 0
    
    if os.path.exists(interjections_conf_file or ""):
        f = open(interjections_conf_file, "r")
        curr_interjection = ""
        
        # Going thru interjection config file
        for curr_interjection in list(f):
            curr_interjection = curr_interjection.rstrip("\n\r")
            p = re.compile(r'\b(\&[-])*' + curr_interjection + r'\b', flags=re.IGNORECASE)
            nb_interjections += len(re.findall(p, clean))
            clean = re.sub(p, '', clean)
            
        f.close()

    return (clean, nb_interjections)

# This function removes expressions found in dialog based on a configuration file provided.
# Configuration file should simply list (line by line) every expressions that could be found in the dialog.
# Chat files mark expressions as following : &=expression (e.g. &=laugh)
def remove_expressions(dialog, expressions_conf_file):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    nb_expressions = 0
    
    if os.path.exists(expressions_conf_file or ""):
        f = open(expressions_conf_file, "r")
        curr_expression = ''
        
        for curr_expression in list(f):
            curr_expression = curr_expression.rstrip("\n\r")
            p = re.compile(r'&=\b' + curr_expression + r'\b', flags=re.IGNORECASE)
            nb_expressions += len(re.findall(p, clean))
            clean = re.sub(p, '', clean)
            
        f.close()
    
    return (clean, nb_expressions)

# This function removes incomplete words and phrases
# In chat files, incomplete words are marked as following : &incomplete_word or &+incomplete_word
def remove_incomplete_words_and_phrases(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    nb_incomplete_words = 0
    
    p = re.compile('&([a-zA-Z0-9À-ÿ_+-]+)')
    nb_incomplete_words = len(re.findall(p, clean))
    clean = re.sub(p, '', clean)
    
    p = re.compile('\\.\\.\\.')
    nb_incomplete_phrases = len(re.findall(p, clean))
    clean = re.sub(p, '.', clean)
    
    return (clean, nb_incomplete_words, nb_incomplete_phrases)

# This function removes errors found in dialogs
def remove_errors(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    no_errors = 0
 
    # CASE 1: Multiple words:
    # EXAMPLE: *CHI: It was <de composed> [: decomposed] [*]  .
    p = re.compile('(.*)<.+?>\s\\[:(.+?)\\](.*)')
    while re.search(p, clean):
        no_errors = no_errors + 1
        clean = re.sub(p,r'\1\2\3',clean)

    # CASE 2: A single word:
    # EXAMPLE: *CHI:  he had two mouses [: mice] [*]  .
    p = re.compile('(.*?)([a-zA-Z0-9À-ÿ_\']+?)\s\\[:(.+?)\\](.*)')
    while re.search(p, clean):
        no_errors = no_errors + 1
        clean = re.sub(p,r'\1\3\4',clean)    
    
    return (clean, no_errors)

# This function removes repititions found in dialog
def remove_repetitions(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    nb_repititions = 0 
    
    # [/] is used in those cases when a speaker repeats the earlier material without change.

    # CASE 1: MULTIPLE WORDS
    # Chat files (.cha) repititions marked by "<>" and "[/]"
    # EXAMPLE: *CHI: <I wanted> [/] I wanted to invite Margie .
    p = re.compile('<.+?> \\[/\\]')
    nb_repititions = len(re.findall(p, clean))
    clean = re.sub(r'<.+?> \[/\]', '', clean)
    
    # CASE 2: SINGLE WORD
    # Chat files (.cha) repititions marked by "[/]"
    # EXAMPLE: *CHI: it's [/] (.) um (.) it's [/] it's like (.) a um (.) dog .  
    p = re.compile('[a-zA-Z0-9À-ÿ_\']+ \\[/\\]')
    nb_repititions = nb_repititions + len(re.findall(p, clean))
    clean = re.sub(r'[a-zA-Z0-9À-ÿ_\']+ \[/\]', '', clean)
    
    # CASE 3: Text file (.txt) repititions marked by ","
    # EXAMPLE: la voiture, la voiture
    p = re.compile(r'(\b[a-z,A-Z ]+\s*), (?=.*\1)')
    nb_repititions = nb_repititions + len(re.findall(r'(\b\w+\b\s*)+\,*(?=.*\1)', clean))
    clean = re.sub(p, r'', clean)
    
    return (clean, nb_repititions)

# This function removes all retracings found in dialog
def remove_retracings(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # emoving multiple spacing
    nb_retracing = 0 
    
    # [//]  is used when a speaker starts to say something, stops, repeats the 
    # basic phrase, but changes any part of the phrase.

    # CASE 1: Multiple words:
    # EXAMPLE: *CHI: <I wanted> [//] uh I thought I wanted to invite Margie .
    nb_retracing = len(re.findall(r'<.+?> \[//\]', clean))
    clean = re.sub(r'<.+?> \[//\]', '', clean)

    # CASE 2: A single word:
    # EXAMPLE: *CHI: I [//] uh I thought I wanted to invite Margie .
    nb_retracing = nb_retracing + len(re.findall(r'[a-zA-Z0-9À-ÿ_\']+ \[//\]', clean))
    clean = re.sub(r'[a-zA-Z0-9À-ÿ_\']+ \[//\]', '', clean)

    return (clean, nb_retracing)

# This function removes multiple markers and symbols in dialogs
def remove_markers_and_symbols(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
 
    # In some french transcripts, composed word such as "cerf-volant" are written as following "cerf+volant"
    # We change it to it's normal form "cerf-volant"
    clean = re.sub(r'([a-z]+)(\+)([a-z]+)', r'\1-\3', clean)

    p = re.compile('^(\+,)|^(\,)|\\[.+?\\]|<.+?>|[<>\\[\\]+=\\"/]|&=[a-zA-ZÀ-ÿ0-9_-]+|.+')
    clean = re.sub(p, '', clean)
    
    p = re.compile('[^a-zA-Z0-9À-ÿ\u00C0-\u00FF\\s,\\._;-\\?!\'\’\œ-]')
    clean = re.sub(p, '', clean)
    
    # In the french transcripts, some words starts with the character '0'. We will remove it
    p = re.compile(r'(\b0)([a-zA-ZÀ-ÿ0-9_-])')
    clean = re.sub(p, r"\2", clean)
    
    return (clean)

# This function normalize in a sentence like format for all lines from dialog
def normalize_sentence(dialog):
    clean = re.sub(r'\s\s+', ' ', dialog) # removing multiple spacing
    
    # Removing the white spaces at the beginning or end:
    clean = clean.strip()
    
    # Capitalizing the first letter to make it sentence-like:
    if clean != '':
        clean = clean[0].upper() + clean[1:]
    
    # Separating again the named-entities:
    clean = re.sub('_', ' ', clean)
    
    # Removing spaces before punctuation marks
    clean = re.sub(' \.', '.', clean)
    clean = re.sub(' ,', ',', clean)
    clean = re.sub(' \?', '?', clean)
    clean = re.sub('\!', '!', clean)
    
    # Removing multiple spacing
    clean = re.sub(r'\s\s+', ' ', clean) 

    # Adding a comma if there's none
    if not clean.endswith(".") and not clean.endswith("?") and not clean.endswith("!"):
        clean += "."
    
    # Verify if the sentence contains characters
    if not re.search('[a-zA-Z]', clean):
        return

    return (clean)

# This function is used to reduce synonyms to one single word. This task is mainly to reduce complexity of POS tags when analyzing 
# basic syntaxic patterns. 
# NOTE : We also keep track of non- synonym reduced transcripts, since valuable information can be found within synonyms.
#
# A configuration file should define rules for reducing synonyms.
# Here's an example of a configuration file. All words assigned to the word 'women' will be changed for 'women':
# {
#   "women": ["girl", "mother", "wife"]
# }
def reduce_synonyms(dialog, syn_conf_file):
    clean_syn = dialog
    nb_synonyms = 0

    synonym_dict = json.load(open(syn_conf_file))

    for curr_synonym in synonym_dict.keys():
        pattern = r"\b("+'|'.join(synonym_dict[curr_synonym])+r")\b"
        nb_synonyms += len(re.findall(pattern, clean_syn, re.IGNORECASE))
        clean_syn = re.sub(pattern, curr_synonym, clean_syn, re.IGNORECASE)
    
    return (clean_syn, nb_synonyms)