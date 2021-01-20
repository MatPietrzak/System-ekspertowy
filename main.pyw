## IMPORTS
import os
import sys
from csv import reader, QUOTE_MINIMAL
from pathlib import Path
import datetime
import logging
import importlib
import utility
import math

## Initialization
# Save logs to Logs directory
try:
    Path("Logs\\").mkdir(parents=True, exist_ok=True)
    LOGGER = logging.getLogger('main_logger')
    LOGGER.setLevel(logging.DEBUG)
    FORMATTER = logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s')
    LOG_FILE = (datetime.datetime.now()).strftime(f'Logs\\%Y%m%d_App.txt')
    FH = logging.FileHandler(LOG_FILE)
    FH.setFormatter(FORMATTER)
    LOGGER.addHandler(FH)
    CH = logging.StreamHandler()
    CH.setFormatter(FORMATTER)
    LOGGER.addHandler(CH)
    LOGGER.info("Created log folders and log handler")
except Exception as ex:
    print("Couldn't create logs")
    print(ex)

# Load WPF module to enable GUI
try:
    import clr
    clr.AddReference(r"wpf\PresentationFramework")

    from System.IO import StreamReader # pylint: disable=import-error
    from System import Action, Tuple # pylint: disable=import-error
    from System.Windows.Markup import XamlReader # pylint: disable=import-error
    from System.Windows import Application # pylint: disable=import-error
    from System.Threading import Thread, ThreadStart, ApartmentState # pylint: disable=import-error
    from System.Collections.Generic import Dictionary # pylint: disable=import-error

    if getattr(sys, "frozen", False):
        PATH = os.path.abspath(os.path.dirname(sys.executable))
    else:
        PATH = os.path.abspath(os.path.dirname(__file__))
    LOGGER.info("Imported all libraries")
except Exception as ex:
    LOGGER.error("Couldn't load libraries")
    LOGGER.error(ex)

## General methods
def convertedDb(dbFilePath, dbConvertedFilePath, evaluator, targetColName="Y"):
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
            row_converted = evaluator.parseRow(row_dict)
            row_converted[targetColName] = row_dict[targetColName]
            if columnsTarget is None:
                columnsTarget = list(row_converted.keys())
            value = [str(row_converted[key]) for key in columnsTarget]
            values.append(value)

    with open(dbConvertedFilePath, mode="w", encoding="utf-8") as converted:
        converted.write(",".join(columnsTarget) + "\n")
        converted.write("\n".join([",".join(value) for value in values]))

def examineFile(dbFilePath, evaluator, targetColName="Y", reportProgress=None):
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

        # check how many entries
        all_items_count = len(list(database_reader)) - 1
        report_every = all_items_count / 100
        current_counter = report_every
        prog = 0

        # reread file and  find key words in all data
        database.seek(0)
        columns = list(next(database_reader, None))

        if targetColName not in columns:
            raise Exception(f"Sorry, files doesn't contain target column '{targetColName}',"
                            + f" found following columns: {columns}")

        keywords = dict()
        for row in database_reader:
            row_dict = dict(zip(columns, row))
            if row_dict["Y"] in ["HQ", "LQ_CLOSE"]:
                words = evaluator.trimBodyWords(row_dict)
                words = utility.clearMeaningless(words)
                for word in words:
                    if word not in keywords:
                        keywords[word] = 0
                    keywords[word] += 1

        for key, value in keywords.items():
            keywords[key] = math.log10(all_items_count/value)
        
        evaluator.keywords = keywords

      # reread file and analyze data
        database.seek(0)
        columns = list(next(database_reader, None))

        if targetColName not in columns:
            raise Exception(f"Sorry, files doesn't contain target column '{targetColName}',"
                            + f" found following columns: {columns}")
        for row in database_reader:
            row_dict = dict(zip(columns, row))
            expected = row_dict[targetColName]
            del row_dict[targetColName]
            row_converted = evaluator.parseRow(row_dict)
            result = evaluator.examineEntry(row_converted)
            if expected not in resultOkWrong:
                resultOkWrong[expected] = {"ok": 0, "wrong": 0}
            resultOkWrong[expected]["ok" if expected == result else "wrong"] += 1
            current_counter -= 1
            if current_counter <= 0:
                prog += 1
                reportProgress(prog)
                current_counter = report_every

    rowOk = sum(entry["ok"] for _, entry in resultOkWrong.items())
    rowWrong = sum(entry["wrong"] for _, entry in resultOkWrong.items())

    result = dict()
    result["ALL"] = createEntry(rowOk, rowWrong)
    for name, entry in resultOkWrong.items():
        nameOk = entry["ok"]
        nameWrong =  entry["wrong"]
        result[name] = createEntry(nameOk, nameWrong)
    return result

def createEntry(ok, wrong):
    """
    Creates entry saved to summary

    :Args:
        * ok: how many entries recognized correctly [int]
        * wrong: how many entries recognized incorrectly [int]
    """

    _all = ok + wrong
    return {
        "ok": ok,
        "wrong": wrong,
        "all": _all,
        "ok_pct": "-" if _all == 0 else round((ok / _all) * 100, 2),
        "wrong_pct": "-" if _all == 0 else round((wrong / _all) * 100, 2)
    }

def returnListFile(path, extension):
    """
    Returns list of file from given 'path' ended with 'extension'

    :Args:
        * path: where to search for files [str]
        * extension: extension of filter for found files
    """

    if not extension.startswith("."):
        extension = "." + extension
    files = [
        file.replace(extension, "") for file in os.listdir(path)
        if os.path.isfile(os.path.join(path, file)) and file.endswith(extension)]
    return files


def conv2wpfDict(key, data):
    """
    Converts python dictionary to Tuple which can be displayed on GUI

    :Args:
        * key : method to execute in background [method]
        * data : method to execute in background [method]
    """
    return Tuple.Create(key, data["ok"], data["ok_pct"], data["wrong"], data["wrong_pct"])

## Logic of appplication
class ExpertSystemGUI():
    """
    GUI class for managing data
    """

    def __init__(self):
        """
        Loads GUI, find all controls and show window
        """

        try:
            LOGGER.info("Activating GUI")
            stream = StreamReader(r"MainWindow.xaml")
            window = XamlReader.Load(stream.BaseStream)

            self.cmbProject = window.FindName("cmbProject")
            self.cmbProject.IsEnabled=True
            self.cmbData = window.FindName("cmbData")
            self.cmbEval = window.FindName("cmbEval")
            self.viewScore = window.FindName("viewScore")
            self.btnStart = window.FindName("btnStart")
            self.btnStart.Click += lambda s, e: self.run_in_background(self.start_eval)
            self.prog = window.FindName("prog")

            self.window_obj = window.FindName("window")
            self.window_obj.Loaded += lambda s, e: self.window_init()

            self.cmbProject.SelectionChanged += lambda s, e: self.refreshData()

            LOGGER.info("Running window")
            Application().Run(window)
        except Exception as ex:
            LOGGER.error(ex)

    def window_init(self):
        """
        Initializing window
        """
        
        LOGGER.info(f"Initializing window")
        def todo():
            self.refreshProjects()

        self.execute_on_gui("Initializing window", todo)
        return True

    def execute_on_gui(self, name, method):
        """
        Executes method on GUI thread

        :Args:
            * name: name of performed action (for log purposes) [str]
            * method: method to be executed on main thread [method]
        """

        try:
            self.GLOBAL_RESULT = None
            Application.Current.Dispatcher.Invoke(
                Action(method)
            )
        except Exception as ex:
            LOGGER.error(f"Can't perform action '{name}' on GUI")
            LOGGER.error(ex)
        return self.GLOBAL_RESULT

    def refreshProjects(self):
        """
        Refreshes current list of available projects
        """
        
        self.btnStart.IsEnabled = True
        path = "Data\\"
        projects = [
            folder for folder in os.listdir(path)
            if not os.path.isfile(os.path.join(path, folder))]
        self.refreshCombobox(self.cmbProject, projects)

    def refreshData(self):
        """
        Refreshes current list of available databases
        """
        
        path = self.currentPath()
        files = returnListFile(path, "csv")
        self.refreshCombobox(self.cmbData, files)
        
        files = returnListFile(path, "py")
        self.refreshCombobox(self.cmbEval, files)

    def currentProject(self):
        """
        Name of currently selected database
        """

        result = self.cmbProject.SelectedValue
        self.GLOBAL_RESULT = result
        return result

    def currentPath(self):
        """
        Relative folder to selected database
        """

        result = "Data\\" + self.currentProject() + "\\"
        self.GLOBAL_RESULT = result
        return result

    def currentCsvFile(self):
        """
        Current file name of CSV database
        """

        result = self.cmbData.SelectedValue + ".csv"
        self.GLOBAL_RESULT = result
        return result

    def currentCsvFilePath(self):
        """
        Current file path to CSV database
        """

        result = os.path.join(self.currentPath(), self.currentCsvFile())
        self.GLOBAL_RESULT = result
        return result

    def currentEvalModulePath(self):
        """
        Returns python module path to selected evaluator
        """

        proj = self.currentProject()
        evalFile = self.cmbEval.SelectedValue
        result = f"Data.{proj}.{evalFile}"
        self.GLOBAL_RESULT = result
        return result

    def refreshCombobox(self, obj, data):
        """
        Refreshes combo box 'obj' items based on 'data'

        :Args:
            * obj: ComboBox object [str]
            * data: list of object to be put on combobox options [list of obj]
        """

        def setItems(obj, data):
            obj.Items.Clear()
            for entry in data:
                obj.Items.Add(entry)
            if len(data):
                obj.SelectedIndex = 0
            else:
                obj.Items.Add("err: not found any matches")
                self.btnStart.IsEnabled = False
            obj.IsEnabled = len(data) > 1

        self.execute_on_gui(
            f"Updating object {obj.Name} with new entries",
            lambda: setItems(obj, data)
        )
        
    def start_eval(self):
        """
        Begins evaluation and manages GUI
        """

        def init(obj):
            obj.Items.Clear()
            self.btnStart.IsEnabled = False

        def setItems(obj, data):
            for key, val in data.items():
                obj.Items.Add(conv2wpfDict(key, val))
            if len(data):
                obj.SelectedIndex = 0
            self.btnStart.IsEnabled = True

        try:
            self.execute_on_gui(
                f"Initializing evaluation",
                lambda: init(self.viewScore)
            )
            self.reportProgress(0)

            self.execute_on_gui(f"Get CSV file name", lambda: self.currentCsvFile())
            csvFile = self.GLOBAL_RESULT
            self.execute_on_gui(f"Get CSV file path", lambda: self.currentCsvFilePath())
            csvFilePath = self.GLOBAL_RESULT
            self.execute_on_gui(f"Get evaluator file path", lambda: self.currentEvalModulePath())
            evalFilePath = self.GLOBAL_RESULT

            evaluator = importlib.import_module(evalFilePath)

            # summary of testing
            result = examineFile(
                csvFilePath, evaluator=evaluator,
                reportProgress=self.reportProgress)

            # unlock to see each recognized row
            #convertedDb(csvFilePath, "_" + csvFile, evaluator=evaluator)

            self.execute_on_gui(
                f"Updating score",
                lambda: setItems(self.viewScore, result)
            )
            self.reportProgress(100)
        except Exception as ex:
            LOGGER.error(ex)
            self.reportProgress(0)

    def run_in_background(self, method):
        """
        Runs selected method in background so not to block GUI

        :Args:
            * method : method to execute in background [method]
        """

        self.background_task = Thread(ThreadStart(method))
        self.background_task.Start()

    def reportProgress(self, prog):
        """
        Sets current value of progress bar

        :Args:
            * method : method to execute in background [method]
        """

        def setProgress(val):
            if val < 0:
                val = 0
            if val > 100:
                val = 100
            self.prog.Value = val

        try:
            self.execute_on_gui(
                f"Updating progrses",
                lambda: setProgress(prog)
            )
        except Exception as ex:
            LOGGER.error(ex)

## Run GUI if main.py is run directly
if __name__ == "__main__":
    try:
        LOGGER.info("> Running app")
        THREAD = Thread(ThreadStart(ExpertSystemGUI))
        LOGGER.info("> Settings apartment state")
        THREAD.SetApartmentState(ApartmentState.STA)
        LOGGER.info("> Starting")
        THREAD.Start()
        LOGGER.info("> Waiting for close")
        THREAD.Join()
        LOGGER.info("> App Closed")
    except Exception as ex:
        LOGGER.error("There was a problem with Python service")
