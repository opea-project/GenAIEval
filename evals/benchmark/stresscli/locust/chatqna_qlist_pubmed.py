# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import random
import time

import tokenresponse as token

# Add debug logging
logging.basicConfig(level=logging.DEBUG)


DATASET = os.getenv("DATASET", "pubmed_q1000.txt")
MAX_LINES = os.getenv("MAX_LINES", 1000)
MAX_TOKENS = os.getenv("MAX_TOKENS", 128)
MAX_WORDS = os.getenv("MAX_WORDS", 1024)
PROMPT = os.getenv(
    "PROMPT",
    f". Give me the content related to this title and please repeat the answer multiple times till the word count exceeds {MAX_WORDS}.",
)

# Initialize the data
cwd = os.path.dirname(os.path.abspath(__file__))
filename = os.path.abspath(DATASET)
logging.info(f"The dataset filename: {filename}")
logging.info(f"MAX_LINES: {MAX_LINES}")
logging.info(f"MAX_TOKENS: {MAX_TOKENS}")
logging.info(f"MAX_WORDS: {MAX_WORDS}")

# filename = os.path.join(cwd, "..", "dataset", "pubmed_q1000_fix.txt")
prompt_suffix = PROMPT

# Global dictionary to store data
data_dict = {}
max_lines = 0


def load_pubmed_data(filename):
    """Load PubMed data into a dictionary and determine max lines."""
    global data_dict, max_lines
    # create timestamp t1, t2 in the end of this function print the consumed time by t2-t1
    t1 = time.time()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    line = line.strip()

                    if not line:  # Skip empty lines
                        continue

                    data = json.loads(line)
                    data_dict[line_num] = data
                    max_lines = line_num

                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON at line {line_num}: {line[:100]}...")
                except (IndexError, ValueError) as e:
                    logging.warning(f"Invalid ID format at line {line_num}: {str(e)}")
                except Exception as e:
                    logging.warning(f"Error processing line {line_num}: {str(e)}")
            print(f"Current length of data_dict: {len(data_dict)}")

        logging.info(f"Loaded {len(data_dict)} items. Max ID: {max_lines}")

        # Add validation check
        if len(data_dict) < 2:  # Assuming we should have more than 10 items
            logging.error("Suspiciously few items loaded. Possible data loading issue.")
            return False
        t2 = time.time()
        print(f"load_pubmed_data time:{t2-t1:.4f} seconds")
        return True
    except Exception as e:
        logging.error(f"Error loading file: {str(e)}")
        return False


if not load_pubmed_data(filename):
    exit()


def getDataByLine(line_num):
    """Get document by its line number."""
    return data_dict[line_num]
    # return data_dict.get(line_num)


def getRandomDocument():
    """Get a random document using line numbers."""
    if not data_dict:
        logging.error("No data loaded")
        return None

    # get min of max_lines and MAX_LINES
    random_max = min(max_lines, int(MAX_LINES))
    logging.info(f"random_max={random_max}")

    random_line = random.randint(1, random_max)
    doc = getDataByLine(random_line)
    if doc:
        return doc

    logging.error("Failed to find valid document after ")
    return None


def getUrl():
    return "/v1/chatqna"


def getReqData():
    doc = getRandomDocument()
    message = f"{doc['title']}{prompt_suffix}"
    logging.debug(f"Selected document: {message}")
    return {"messages": f"{message}", "max_tokens": int(MAX_TOKENS), "top_k": 1, "temperature": 0}


def respStatics(environment, reqData, respData):
    return token.respStatics(environment, reqData, respData)


def staticsOutput(environment, reqlist):
    token.staticsOutput(environment, reqlist)


# write a function to get the title of each line of the data_dict
def get_title(data_dict):
    titles = []
    # get the length of the data_dict first, then iterate the data_dict get each line, each line is a doc
    length = len(data_dict)
    print(f"length={length}")
    for i in range(length):
        i = i + 1
        doc = data_dict.get(i)
        # print the length of doc json
        total_chars = 0
        for key, value in doc.items():
            if isinstance(value, str):  # Check if the value is a string
                total_chars += len(value)

        id = doc["id"]
        title = doc["title"]
        # print(f"title={title},length={len(title)}")

        print(f"i={i}, id={id}, total_chars={total_chars}, doclenth length={len(doc)},length={len(title)}")
        titles.append(title)
    return titles


# test
if __name__ == "__main__":
    logging.info("Starting the program")
    # getRandomDocument()
    get_title(data_dict)
    # filename = "../dataset/pubmed_q1000.json"
    # test_parse_pubmed(filename)
    # Test the random document retrieval
    for _ in range(3):  # Test 3 random retrievals
        doc = getRandomDocument()
        if doc:
            logging.info(f"Retrieved document: ID={doc['id']}, Title={doc['title'][:50]}...")
        else:
            logging.warning("No document found for generated ID")
