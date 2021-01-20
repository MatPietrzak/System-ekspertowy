import utility

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
TAG_TAGSCOUNT = "TagsCount"

def parseRow(data):
    """
    Parses row and return dictionary to be examined

    :Args:
        * data: data to be converted to dictionary
    """

    text = utility.removeBetweenTags(data["Body"], "pre")
    text = utility.cleanHtmlTags(text)

    return {
        TAG_BODY_LENGTH: len(data["Body"]),
        TAG_CLEANBODY_LENGTH: len(text),
        TAG_TITLE_LENGTH: len(data["Title"]),
        TAG_BODY_WORDS: len(data["Body"].split(" ")),
        TAG_CLEANBODY_WORDS: len(data["Body"].split(" ")),
        TAG_TITLE_WORDS: len(data["Title"].split(" ")),
        TAG_CONTAINS_CODE: "<code>" in data["Body"],
        TAG_LINK_COUNT: len(data["Body"].split("<a ")) - 1,
        TAG_LINKELIVE_COUNT: sum([utility.countInstances(data["Body"], regex) for regex in [r"jsfiddle.net"]]),
        TAG_NUMBER_PARAGRAPHS: len(data["Body"].split("<p>")) - 1,
        TAG_TAGSCOUNT: utility.countInstances(data["Tags"], r"<[^>]*>")
    }

def examineEntry(data):
    """
    Returns expected result for entry

    :Args:
        * data: converted row of data to dictionary [dict]
    """

    if data[TAG_NUMBER_PARAGRAPHS] == 0:
        return "LQ_EDIT"

    if data[TAG_LINK_COUNT] > 0:
        return "HQ"

    if data[TAG_CLEANBODY_LENGTH] <= 580:
        return "LQ_CLOSE"

    return "HQ" 


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
    keyWords=getDuplicatesWithCount(keyWords)
    
    #Sort dictionary by values
    sorted_values = sorted(keyWords.values()) # Sort the values
    sorted_dict = {}
    for i in sorted_values:
        for k in keyWords.keys():
            if keyWords[k] == i:
                sorted_dict[k] = keyWords[k]
                break

    return sorted_dict