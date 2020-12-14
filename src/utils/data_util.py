import os
from utils.nlp_util import Tag

# This function simply saves a dialog in a text file
def save_dialog_in_file(dialog, file_path):
    dirname = os.path.dirname(file_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(file_path, "w+") as f:
        f.write(dialog)
        f.close()
    return

# This function saves tagged dialog (POS tags) in a file
def save_tags_in_file(tags, file_path):
    dirname = os.path.dirname(file_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(file_path, "w+") as f:
        for tag in tags:
            if type(tag) is Tag:
                f.write(tag.original + " " + tag.lemma + " " + tag.tag + "\n")
            else:
                f.write(os.linesep)
        f.close()
    return

# This function exports a dataframe to a csv file.
def export_dataframe(df, output_path="/"): 
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    df.to_csv(output_path)
