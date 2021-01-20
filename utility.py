import re
import os

MEANINGLESS_WORDS_FILE = r"Resources\meaningless_words.txt"

MEANINGLESS_WORDS = []
if os.path.exists(MEANINGLESS_WORDS_FILE):
    with open(MEANINGLESS_WORDS_FILE, mode="r") as f:
        MEANINGLESS_WORDS = [x.strip() for x in f.readlines()]

print(MEANINGLESS_WORDS)

def removeBetweenTags(txt, tag):
    regex = r"(<" + tag + ">.+?<\/" + tag + ">)"
    matches = re.finditer(regex, txt, re.MULTILINE | re.DOTALL)
    result = txt

    for _, match in enumerate(matches, start=1):   
        for groupNum in range(0, len(match.groups())):
            found = match.group(groupNum)
            result = result.replace(found, "")

    return result

def cleanHtmlTags(txt):
    regex = r"(<\/?[a-z]*(\s*\/)?>)"
    matches = re.finditer(regex, txt, re.MULTILINE | re.DOTALL)
    result = txt

    for _, match in enumerate(matches, start=1):   
        found = match.group(0)
        result = result.replace(found, "")

    return result

def getWords(txt):
    regex = r"[a-zA-Z][a-zA-Z']*"
    matches = re.finditer(regex, txt, re.MULTILINE)
    result = []

    for _, match in enumerate(matches, start=1):
        found = match.group(0).strip()
        result.append(found)
    return result

def countInstances(txt, toFind):
    result = len(re.findall(toFind, txt))
    return result

def clearMeaningless(words):
    """
    Removes all meaningless words from the list based on 'meaningless_words.txt' file

    :Args:
        * words: list of words to filter out, all words must be lowered [arr of str]
    """

    return [word for word in words if word not in MEANINGLESS_WORDS]
