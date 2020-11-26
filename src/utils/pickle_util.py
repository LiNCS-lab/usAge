import pickle
import os

# To read from pickle files
def read_pickle(file_path):
    with open(file_path, "rb") as pickle_file:
        pickle_obj = pickle.load(pickle_file)
    pickle_file.close()

    return pickle_obj

# To write pickle files
def write_pickle(data, file_path):
    dirname = os.path.dirname(file_path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(file_path, "wb") as pickle_file:
        pickle.dump(data, pickle_file)
        pickle_file.close()
