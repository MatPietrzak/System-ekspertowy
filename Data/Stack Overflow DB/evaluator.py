import utility
import math

TAG_KEYWORDCOUNTFIRSTPAR = "KeywordCountFirstPar"
TAG_KEYWORDCOUNTLASTPAR = "KeywordCountLastPar"
TAG_KEYWORDCOUNT20PCT = "KeywordCount20Pct"
TAG_KEYWORDCOUNT50PCT = "KeywordCount50Pct"
TAG_KEYWORDDENSITY = "KeywordDensity"
TAG_ALLWORDSCOUNT = "AllWordsCount"
TAG_RATIOREMOVEDTOALL = "RatioRemovedToAll"
TAG_TEXTVECTORDENSITY = "TextVectorDensity"
TAG_FIRSTKEYWORD = "FirstKeyword"
TAG_MOSTFREQUENTKEYWORD = "MostFrequentKeyword"

COLUMNS_OPTIONS = [
    #(TAG_KEYWORDCOUNTFIRSTPAR, True),
    #(TAG_KEYWORDCOUNTLASTPAR, True),
    (TAG_KEYWORDCOUNT20PCT, True),
    (TAG_KEYWORDCOUNT50PCT, True),
    (TAG_KEYWORDDENSITY, True),
    (TAG_ALLWORDSCOUNT, True),
    (TAG_RATIOREMOVEDTOALL, True),
    (TAG_TEXTVECTORDENSITY, True),
    (TAG_FIRSTKEYWORD, False),
    (TAG_MOSTFREQUENTKEYWORD, False)
]

COLUMNS = [option[0] for option in COLUMNS_OPTIONS]

IDFS = dict()
KEYWORD_THRESHOLD = 0.1

def learn(data, report_progress):
    global IDFS

    reporter = utility.ProgressCounter(len(data), report_progress)

    # computing Inverse Document Frequency
    words_counters = dict()
    all_items_count = len(data)
    for row_dict in data:
        if row_dict["Y"] in ["HQ", "LQ_CLOSE"]:
            words = utility.trim_body_words(row_dict["Body"])
            words = utility.clear_meaningless(words)
            words = list(set(words)) # no duplicats, we need unique occurences of words
            for word in words:
                if word not in words_counters:
                    words_counters[word] = 0
                words_counters[word] += 1

        reporter.next()

    for key, value in words_counters.items():
        IDFS[key] = math.log10(all_items_count/value)

    return ["HQ"] * len(data)

def process_database(data, report_progress):
    processed_data = []

    reporter = utility.ProgressCounter(len(data), report_progress)

    for record in data:
        words_all = utility.trim_body_words(record["Body"])
        words_clean = utility.clear_meaningless(words_all)
        words_counter = utility.count_objects_instances(words_all)

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
        words_only_keywords = [word for word in words_clean if word in keywords]

        # 2.1.1  count of keywords in first paragraph
        #C1 = None
        # 2.1.2  count of keywords in last paragraph
        #C2 = None
        # 2.1.3  count of keywords in first 20%
        words_20pct = words_all[:int(0.2*L)]
        keywords_20pct = [word for word in words_20pct if word in keywords]
        C3 = len(keywords_20pct)
        # 2.1.4  count of keywords in first 50%
        words_50pct = words_all[:int(0.5*L)]
        keywords_50pct = [word for word in words_50pct if word in keywords]
        C4 = len(keywords_50pct)
        # 2.1.5  density of keywords
        Q = sum([words_counter[word] for word in keywords if word in words_counter])
        C5 = Q / L if L > 0 else 0
        # 2.1.6  count of all words
        C6 = L
        # 2.1.7  ratio of removed words to all words
        C7 = Z / L if L > 0 else 0
        # 2.1.8  density of text vector
        T = sum([words_counter[word] for word in words_clean])
        C8 = Q / T if T > 0 else 0
        # 2.1.9  first keyword in text
        C9 = words_only_keywords[0] if words_only_keywords else ""
        # 2.1.10 most frequent keyword in text
        words_only_keywords_counter = utility.count_objects_instances(words_only_keywords)
        k_vector = [(counter, word) for word, counter in words_only_keywords_counter.items()]
        k_vector.sort(reverse=True)
        C10 = k_vector[0][1] if k_vector else ""

        ready_vector = [C3, C4, C5, C6, C7, C8, C9, C10]
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

    if data[TAG_TEXTVECTORDENSITY] <= 99.88:
        return "LQ_EDIT"
    else:
        if data[TAG_KEYWORDCOUNT50PCT] <= 1.04 and data[TAG_KEYWORDDENSITY] <= 1.02:
            return "LQ_CLOSE"

    return "HQ"