import os
from csv import reader, QUOTE_MINIMAL
from evaluator import *

# HERE WE WILL MAKE GUI

def convertedDb(dbFilePath, dbConvertedFilePath, targetColName="Y"):
    """
    Converts raw database to full CSV

    :Args:
        * dbFilePath: path to the database file [path]
        * dbConvertedFilePath: path where to save generated file [path]
        * targetColName: name of the target column [str]
    """

    columnsTarget = None
    values = []

    with open(dbFilePath, mode="r", encoding="utf-8") as database:

        database_reader = reader(database, delimiter=",",
                                quotechar='"', quoting=QUOTE_MINIMAL)
        columns = list(next(database_reader, None))
        for row in database_reader:
            row_dict = dict(zip(columns, row))
            row_converted = parseRow(row_dict)
            row_converted[targetColName] = row_dict[targetColName]
            if columnsTarget is None:
                columnsTarget = list(row_converted.keys())
            value = [str(row_converted[key]) for key in columnsTarget]
            values.append(value)

    with open(dbConvertedFilePath, mode="w", encoding="utf-8") as converted:
        converted.write(",".join(columnsTarget) + "\n")
        converted.write("\n".join([",".join(value) for value in values]))

def examineFile(dbFilePath, targetColName="Y"):
    """
    Loads file and examine each entry

    :Args:
        * dbFilePath: path to the database file [path]
        * targetColName: name of the target column [str]
    """

    resultOkWrong = dict()

    with open(dbFilePath, mode="r", encoding="utf-8") as database:
        database_reader = reader(database, delimiter=",",
                                quotechar='"', quoting=QUOTE_MINIMAL)
        columns = list(next(database_reader, None))

        if targetColName not in columns:
            raise Exception(f"Sorry, files doesn't contain target column '{targetColName}',"
                            + f" found following columns: {columns}")

        for row in database_reader:
            row_dict = dict(zip(columns, row))
            expected = row_dict[targetColName]
            del row_dict[targetColName]
            row_converted = parseRow(row_dict)
            result = examineEntry(row_converted)
            if expected not in resultOkWrong:
                resultOkWrong[expected] = {"ok": 0, "wrong": 0}
            resultOkWrong[expected]["ok" if expected == result else "wrong"] += 1

    rowOk = sum(entry["ok"] for _, entry in resultOkWrong.items())
    rowWrong = sum(entry["wrong"] for _, entry in resultOkWrong.items())
    rowAll = rowOk + rowWrong
    print(f"Recognized correctly {rowOk} z {rowAll} ({round((rowOk / rowAll) * 100, 2)})")
    for name, entry in resultOkWrong.items():
        nameOk = entry["ok"]
        nameWrong =  entry["wrong"]
        print(f"  {name}: {nameOk}/{nameWrong} ({round((nameOk / (nameOk + nameWrong)) * 100, 2)})")

if __name__ == "__main__":
    convertedDb("train.csv", "sample_expanded.csv")
    convertedDb("valid.csv", "valid_expanded.csv")
    examineFile("train.csv")
