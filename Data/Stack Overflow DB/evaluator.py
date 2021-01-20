import utility

keywords = dict()
all_tags = ['javascript', 'python', 'java', 'android', 'php', 'c#', 'html', 'c++', 'css', 'jquery', 'c', 'arrays', 'ios', 'sql', 'mysql', 'swift', 'angular', 'python-3.x', 'reactjs', 'r', 'regex', 'node.js', 'sql-server', 'string', 'json', 'typescript', 'linux', 'excel', 'docker', '.net', 'list', 'pandas', 'android-studio', 'react-native', 'ruby', 'vba', 'asp.net', 'laravel', 'xcode', 'git', 'flutter', 'database', 'firebase', 'go', 'amazon-web-services', 'bash', 'angularjs', 'kotlin', 'algorithm', 'visual-studio', 'django', 'function', 'python-2.7', 'vue.js', 'spring', 'wordpress', 'ruby-on-rails', 'oracle', 'windows']    

TAG_BODY_LENGTH = "BodyLength"
TAG_CLEANBODY_LENGTH = "CleanBodyLength"
TAG_TITLE_LENGTH = "TitleLength"
TAG_BODY_WORDS = "BodyWords"
TAG_CLEANBODY_WORDS = "CleanBodyWords"
TAG_TITLE_WORDS = "TitleWords"
TAG_CONTAINS_CODE = "ContainsCode"
TAG_NUMBER_PARAGRAPHS = "ParagraphsCount"
TAG_LINK_COUNT = "LinkCount"
TAG_LINKELIVE_COUNT = "LinkLiveCount"
TAG_AVG_WORDS_PER_PARAGRAPH = "AvgWordsPerParagraph"
TAG_TITLE_WORDS_IN_TEXT = "TitleWordsInCount"
TAG_TAGSCOUNT = "TagsCount"
TAG_HQ_COUNTER = "HqCount"
TAG_LQ_COUNTER = "LqCount"
TAG_TAG_POPULAR = "IsPopularTag"
TAG_TAG_PYTHON = "IsPython"
TAG_TAG_JAVA_JQUERY = "JavaJquery"
TAG_KEYWORDS = "TagsKeywords"
TAG_GESTOSC = "TagsGestosc"
TAG_GESTOSC_WEKTORA_SLOW = "TagsGestoscWektoraSlow"
TAG_WORDS_CLEANED = "TagsWordsCleaned"
TAG_WORDS_COUNT = "TagsWordsCount"

COUNTER = 0

def parseRow(data):
    """
    Parses row and return dictionary to be examined

    :Args:
        * data: data to be converted to dictionary
    """
    global COUNTER

    text = utility.removeBetweenTags(data["Body"], "pre")
    text = utility.cleanHtmlTags(text)
    words = utility.getWords(text)

    tags = utility.getAllInstances(data["Tags"], r"<([^>]*)>")
    words_title = utility.getWords(data["Title"])

    # słowa kluczowe
    words_freq = formatKeyWords(words)
    for key, _ in words_freq.items():
        words_freq[key] /= len(words)
    
    words_significant = list()
    for key, value in words_freq.items():
        if key in keywords:
            words_significant.append((keywords[key] * value, key))

    words_significant.sort(reverse=True)

    # stosunek usuniętych słów do wszystkich słów
    words_cleaned = utility.clearMeaningless(words)

    result = {
        # TAG_BODY_LENGTH: len(data["Body"]),
        # TAG_CLEANBODY_LENGTH: len(text),
        # TAG_TITLE_LENGTH: len(data["Title"]),
        # TAG_BODY_WORDS: len(data["Body"].split(" ")),
        # TAG_CLEANBODY_WORDS: len(data["Body"].split(" ")),
        # TAG_TITLE_WORDS: len(data["Title"].split(" ")),
        # TAG_CONTAINS_CODE: "<code>" in data["Body"],
        # TAG_LINK_COUNT: len(data["Body"].split("<a ")) - 1,
        # TAG_LINKELIVE_COUNT: sum([utility.countInstances(data["Body"], regex) for regex in [r"jsfiddle.net"]]),
        # TAG_NUMBER_PARAGRAPHS: len(data["Body"].split("<p>")) - 1,
        # TAG_TAGSCOUNT: utility.countInstances(data["Tags"], r"<[^>]*>"),
        # TAG_KEYWORDS: sum([1 for word in words if word in keywords]) / len(words) if len(words) > 0 else 0,
        # TAG_TAG_POPULAR: any([x in tags for x in all_tags]),
        # TAG_TAG_PYTHON: "python" in tags,
        TAG_GESTOSC: len(words_significant) / len(words) if len(words) > 0 else 0,
        TAG_GESTOSC_WEKTORA_SLOW: len(words_significant) / len(words_cleaned) if len(words) > 0 else 0,
        TAG_WORDS_CLEANED: (len(words) - len(words_cleaned)) / len(words) if len(words) > 0 else 0,
        TAG_WORDS_COUNT: len(words)
    }

    #result[TAG_AVG_WORDS_PER_PARAGRAPH] = result[TAG_BODY_WORDS]/result[TAG_NUMBER_PARAGRAPHS] if result[TAG_NUMBER_PARAGRAPHS] > 0 else 0
    return result

def examineEntry(data):
    """
    Returns expected result for entry

    :Args:
        * data: converted row of data to dictionary [dict]
    """

    # if data[TAG_NUMBER_PARAGRAPHS] == 0:
    #     return "LQ_EDIT"

    #if data[TAG_HQ_COUNTER] > 3 and data[TAG_CONTAINS_CODE]:
    #    return "HQ"

    #if data[TAG_HQ_COUNTER] == 0 and not data[TAG_CONTAINS_CODE]:
    #    return "LQ_CLOSE"

    # if data[TAG_LINK_COUNT] > 0:
    #     return "HQ"

    # if data[TAG_CLEANBODY_LENGTH] <= 580:
    #     return "LQ_CLOSE"

    # return "HQ" 


def trimBodyWords(data):
    row = utility.removeBetweenTags(data["Body"], "pre")
    row = utility.cleanHtmlTags(row)
    row=row.lower()
    wordList=utility.getWords(row)
    #wordList= row.split()
    #wordList = list(set(wordList))
    return wordList

def getDuplicatesWithCount(wordList):
    ''' Get frequency count of duplicate elements in the given list 

        :Args:
        * wordList: converted row of data to dictionary [dict]
    '''
    wordDict = dict()
    # Iterate over each element in list
    for elem in wordList:
        # If element exists in dict then increment its value else add it in dict
        if elem in wordDict:
            wordDict[elem] += 1
        else:
            wordDict[elem] = 1    
 
    # Filter key-value pairs in dictionary. Keep pairs whose value is greater than 1 i.e. only duplicate elements from list.
    wordDict = { key:value for key, value in wordDict.items() if value > 1}
    # Returns a dict of duplicate elements and thier frequency count
    return wordDict
    
def formatKeyWords(keyWords):
    keyWords = [x for x in keyWords if len(x) > 2]
    keyWords = utility.clearMeaningless(keyWords)
    keyWords=getDuplicatesWithCount(keyWords)
    
    #Sort dictionary by values
    # sorted_values = sorted(keyWords.values()) # Sort the values
    # sorted_dict = {}
    # for i in sorted_values:
    #     for k in keyWords.keys():
    #         if keyWords[k] == i:
    #             sorted_dict[k] = keyWords[k]
    #             break

    return keyWords