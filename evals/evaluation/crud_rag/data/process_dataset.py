import os

path = os.path.join(os.path.dirname(__file__), "80000_docs")
for file in os.listdir(path):
    src_file = os.path.join(path, file)
    os.rename(src_file, src_file + ".txt")