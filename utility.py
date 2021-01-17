import re

def removeBetweenTags(txt, tag):
    regex = r"(<" + tag + ">.+?<\/" + tag + ">)"
    matches = re.finditer(regex, txt, re.MULTILINE | re.DOTALL)
    result = txt

    for matchNum, match in enumerate(matches, start=1):   
        for groupNum in range(0, len(match.groups())):
            found = match.group(groupNum)
            result = result.replace(found, "")

    return result

def cleanHtmlTags(txt):
    regex = r"(<\/?[a-z]*(\s*\/)?>)"
    matches = re.finditer(regex, txt, re.MULTILINE | re.DOTALL)
    result = txt

    for matchNum, match in enumerate(matches, start=1):   
        found = match.group(0)
        result = result.replace(found, "")

    return result

def countInstances(txt, toFind):
    result = len(re.findall(toFind, txt))
    return result
