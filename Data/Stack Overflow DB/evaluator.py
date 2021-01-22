import utility
import math
import os


TAG_KEYWORDCOUNT20PCT = "KeywordCount20Pct"
TAG_KEYWORDCOUNT50PCT = "KeywordCount50Pct"
TAG_KEYWORDDENSITY = "KeywordDensity"
TAG_ALLWORDSCOUNT = "AllWordsCount"
TAG_RATIOREMOVEDTOALL = "RatioRemovedToAll"
TAG_TEXTVECTORDENSITY = "TextVectorDensity"

TAG_PARAGRAPHS_COUNT = "ParagraphsCount"
TAG_CODE_FIELDS = "CodeParagraphsCount"
TAG_POPULAR_TAG = "MostPopularTag"
TAG_AVG_POS_TAG = "AveragePositionOfAllTags"

COLUMNS_OPTIONS = [
    (TAG_KEYWORDCOUNT20PCT, True),
    (TAG_KEYWORDCOUNT50PCT, True),
    (TAG_KEYWORDDENSITY, True),
    (TAG_ALLWORDSCOUNT, False),
    (TAG_RATIOREMOVEDTOALL, True),
    (TAG_TEXTVECTORDENSITY, True),

    (TAG_PARAGRAPHS_COUNT, False),
    (TAG_CODE_FIELDS, False),
    (TAG_POPULAR_TAG, False),
    (TAG_AVG_POS_TAG, False)
]

COLUMNS = [option[0] for option in COLUMNS_OPTIONS]

IDFS = dict()
TAGS = list()
KEYWORD_THRESHOLD = 0
MINIMUM_DFI = 100

def learn(data, report_progress):
    global IDFS, TAGS

    reporter = utility.ProgressCounter(len(data), report_progress)

    all_items_count = len(data)
    # computing Inverse Document Frequency
    words_counters = dict()
    tags_counter = dict()

    for row_dict in data:
        words = utility.trim_body_words(row_dict["Body"])
        words = utility.clear_meaningless(words)
        words = list(set(words)) # no duplicats, we need unique occurences of words
        for word in words:
            if word not in words_counters:
                words_counters[word] = 0
            words_counters[word] += 1

        tags = utility.get_all_instances(row_dict["Tags"], r"<([^>]*)>")
        for tag in tags:
            if tag not in tags_counter:
                tags_counter[tag] = 0
            tags_counter[tag] += 1

        reporter.next()

    for key, value in words_counters.items():
        if key not in utility.MEANINGLESS_WORDS:
            IDFS[key] = math.log10(all_items_count/value)

    TAGS = [(v, k) for k, v in tags_counter.items()]
    TAGS.sort(reverse=True)
    TAGS = [x[1] for x in TAGS]

def process_database(data, report_progress):
    global IDFS, TAGS
    processed_data = []

    reporter = utility.ProgressCounter(len(data), report_progress)

    for record in data:
        words_all = utility.trim_body_words(record["Body"])
        words_clean = utility.clear_meaningless(words_all)
        words_counter = utility.count_objects_instances(words_all)
        tags = utility.get_all_instances(record["Tags"], r"<([^>]*)>")

        L = len(words_all)
        Z = L - len(words_clean)

        # computing keywords
        keywords = []
        for word in words_all:
            if word in IDFS:
                IDF = IDFS[word]
                S = words_counter[word]
                TF = S / L if L > 0 else 0
                V = IDF * TF
                if V > KEYWORD_THRESHOLD:
                    keywords.append(word)

        # all keywords in text, duplicates, same order
        #words_only_keywords = [word for word in words_clean if word in keywords]

        # C.1  count of keywords in first 20%
        words_20pct = words_all[:int(0.2*L)]
        keywords_20pct = [word for word in words_20pct if word in keywords]
        C1 = len(keywords_20pct)
        # C.2  count of keywords in first 50%
        words_50pct = words_all[:int(0.5*L)]
        keywords_50pct = [word for word in words_50pct if word in keywords]
        C2 = len(keywords_50pct)
        # C.3  density of keywords
        Q = sum([words_counter[word] for word in keywords if word in words_counter])
        C3 = Q / L if L > 0 else 0
        # C.4  count of all words
        C4= L
        # C.5  ratio of removed words to all words
        C5 = Z / L if L > 0 else 0
        # C.6  density of text vector
        T = sum([words_counter[word] for word in words_clean])
        C6 = Q / T if T > 0 else 0
        # C.7 count of paragraphs
        C7 = len(record["Body"].split("<p>")) - 1
        # C.8 count of <code> tag
        C8 = len(record["Body"].split("<code>")) - 1
        filtered_tags = [TAGS.index(tag) for tag in tags if tag in TAGS]
        C9 = min(filtered_tags) if filtered_tags else 0
        C10 = sum(filtered_tags)/len(filtered_tags) if filtered_tags else 0

        ready_vector = [C1, C2, C3, C4, C5, C6, C7, C8, C9, C10]
        if "Y" in record:
            ready_vector.append(record["Y"])
            COLUMNS_OPTIONS.append(("Y", False))
            COLUMNS.append("Y")
        processed_data.append(dict(zip(COLUMNS, ready_vector)))
        reporter.next()

    for i, col in enumerate(COLUMNS):
        if COLUMNS_OPTIONS[i][1]:
            values = [vector[col] for vector in processed_data]
            values = utility.normalize(values)
            for j, vector in enumerate(processed_data):
                vector[col] = values[j]

    return processed_data

def classify(data):
    """
    Classifies data to some group

    :Args:
        * data: data to be assigned [converted entry]
    
    **Returns**
        Recognized category
    """
    #Catch LQ_EDIT
    if data[TAG_PARAGRAPHS_COUNT] <= 0:
        return "LQ_EDIT"
    #Catch LQ_CLOSE
    if data[TAG_AVG_POS_TAG] <= 15.8:
        return "LQ_CLOSE"
    if data[TAG_POPULAR_TAG] <= 10:
        if data[TAG_CODE_FIELDS] <= 2:
            if data[TAG_KEYWORDCOUNT50PCT] < 0.00880705:
                return "LQ_CLOSE"
            elif data[TAG_POPULAR_TAG] > 4:
                return "LQ_CLOSE"
    elif data[TAG_CODE_FIELDS] <= 1 and data[TAG_AVG_POS_TAG] <= 58 and data[TAG_POPULAR_TAG] <= 21:
        return "LQ_CLOSE"
    #Catch HQ
    return "HQ"
