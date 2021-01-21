import re
import os

# try to load list of meaningless words
MEANINGLESS_WORDS_FILE = r"Resources\meaningless_words.txt"
MEANINGLESS_WORDS = []
if os.path.exists(MEANINGLESS_WORDS_FILE):
    with open(MEANINGLESS_WORDS_FILE, mode="r") as f:
        MEANINGLESS_WORDS = [x.strip() for x in f.readlines()]

def remove_between_tags(content, tag):
    """
    Remove all content between certain 'tag' and them

    :Args:
        * content: content in which to remove text [str]
        * tag: tag between which removal should be performed [str]

    **Returns**
        'Content' without text between 'tag' and wihout them
    """

    regex = r"(<" + tag + r">.+?<\/" + tag + r">)"
    matches = re.finditer(regex, content, re.MULTILINE | re.DOTALL)
    result = content

    for _, match in enumerate(matches, start=1):   
        for groupNum in range(0, len(match.groups())):
            found = match.group(groupNum)
            result = result.replace(found, "")

    return result

def clean_html_tags(content):
    """
    Cleand html tags in 'content'

    :Args:
        * content: content in which to remove html tags [str]

    **Returns**
        'Content' without any html tags
    """

    regex = r"(<\/?[a-z]*(\s*\/)?>)"
    matches = re.finditer(regex, content, re.MULTILINE | re.DOTALL)
    result = content

    for _, match in enumerate(matches, start=1):   
        found = match.group(0)
        result = result.replace(found, "")

    return result

def get_words(content):
    """
    Extracts words from content

    :Args:
        * content: content in which to search for pattern [str]

    **Returns**
        All words found in 'content'
    """

    regex = r"[a-zA-Z][a-zA-Z']*"
    matches = re.finditer(regex, content, re.MULTILINE)
    result = []

    for _, match in enumerate(matches, start=1):
        found = match.group(0).strip()
        result.append(found)
    return result

def get_all_instances(content, to_find):
    """
    Counts instances of 'to_find' in 'content'

    :Args:
        * content: content in which to search for pattern [str]
        * to_find: pattern which should be found in 'text' [regex]

    **Returns**
        All occurences of 'to_find' in 'content'
    """

    result = re.findall(to_find, content)
    return list(result)

def count_instances(content, to_find):
    """
    Counts instances of 'to_find' in 'content'

    :Args:
        * content: content in which to search for pattern
        * to_find: pattern which should be found in 'text' [regex]

    **Returns**
        Counter of occurences of 'to_find' in 'content'
    """

    result = len(re.findall(to_find, content))
    return result

def clear_meaningless(words):
    """
    Removes all meaningless words from the list based on 'meaningless_words.txt' file

    :Args:
        * words: list of words to filter out, all words must be lowered [arr of str]

    **Returns**
        Returnes text with cleaned from meaningless words
    """

    return [word for word in words if word not in MEANINGLESS_WORDS]

def normalize(values, mn=100):
    """
    Normalizes all values on the list

    :Args:
        * values: values to be normalized [list of floats]

    **Returns**
        Returnes normalized list of values
    """

    minimum = min(values)
    maximum = max(values)
    difference = maximum - minimum
    return [minimum] * len(values) if difference == 0 else [(val - minimum)/(difference)*mn for val in values]

def trim_body_words(content):
    """
    Cleans all code tags, lowers letters and returns all found words

    :Args:
        * content: data to be converted [str]

    **Returns**
        Returns list of words in text part of post.
    """

    text = remove_between_tags(content, "pre")
    text = clean_html_tags(text)
    text = text.lower()
    return get_words(text)

def count_objects_instances(values):
    """
    Counts how many instances of each value is in values

    :Args:
        * values: data to be analyzed [str]

    **Returns**
        Returns dictionary where keys are objects from 'values'
        and value for each key is count of object instances in 'values'
    """

    counters = dict()
    for val in values:
        if val not in counters:
            counters[val] = 0
        counters[val] += 1
    return counters

class ProgressCounter():

    def __init__(self, maximum, report_progress):
        self.maximum = maximum
        self.report_progress = report_progress
        self.report_counter = 0
        self.report_every = max(int(self.maximum / 100), 1)
        self.current_progress = 0

    def next(self):
        self.current_progress += 1
        if self.current_progress % self.report_every == 0:
            self.current_progress = 0
            self.report_counter += 1
            self.report_progress(self.report_counter)
