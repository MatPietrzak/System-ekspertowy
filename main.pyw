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
import traceback

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
def examineFile(dbFilePath, classifier, configure_progress, report_progress, is_learnig=True, targetColName="Y", save_converted=False):
    """
    Loads file and examine each entry

    :Args:
        * dbFilePath: path to the database file [path]
        * targetColName: name of the target column [str]
    """

    configure_progress(0, 0.05, "Ładowanie danych")
    # prepare data
    all_records = [] # all avaiable data but without TARGET COLUMN
    target_values = [] # moved target column

    with open(dbFilePath, mode="r", encoding="utf-8") as database:
        database_reader = reader(database, delimiter=",",
                                quotechar='"', quoting=QUOTE_MINIMAL)
        all_count = len(list(database_reader)) - 1
        reporter = utility.ProgressCounter(all_count, report_progress)

        database.seek(0)
        columns = list(next(database_reader, None))

        if targetColName not in columns:
            raise Exception(f"Sorry, files doesn't contain target column '{targetColName}',"
                            + f" found following columns: {columns}")
        for row in database_reader:
            row_dict = dict(zip(columns, row))
            target_values.append(row_dict[targetColName])
            if not is_learnig:
                del row_dict[targetColName]
            all_records.append(row_dict)
            reporter.next()

    # on validating don't call is_learning
    q = [0.4, 45]
    if is_learnig:
        configure_progress(5, 0.4, "Trenowanie")
        classifier.learn(all_records, report_progress)
    else:
        q = [0.8, 5]
    configure_progress(q[1], q[0], "Przetwarzanie")
    processed_data = classifier.process_database(all_records, report_progress)

    configure_progress(85, 0.05, "Zapisywanie bazy")
    if save_converted:
        _columns = processed_data[0].keys()
        with open("learning.csv", mode="w", encoding="utf-8") as converted:
            converted.write(",".join(_columns) + "\n")
            converted.write("\n".join([",".join([str(value[col]) for col in _columns]) for value in processed_data]))

    configure_progress(95, 0.1, "Klasyfikacja")
    resultOkWrong = dict()
    for i, expected in enumerate(target_values):
        result = classifier.classify(processed_data[i])
        if expected not in resultOkWrong:
            resultOkWrong[expected] = {"ok": 0, "wrong": 0}
        resultOkWrong[expected]["ok" if expected == result else "wrong"] += 1

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
            self.cmbDataTrain = window.FindName("cmbDataTrain")
            self.cmbDataValid = window.FindName("cmbDataValid")
            self.cmbEval = window.FindName("cmbEval")
            self.viewScore = window.FindName("viewScore")
            self.btnStart = window.FindName("btnStart")
            self.btnStart.Click += lambda s, e: self.run_in_background(self.start_eval)
            self.prog = window.FindName("prog")
            self.lblStatus = window.FindName("lblStatus")

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
        self.refreshCombobox(self.cmbDataTrain, files, "train")
        self.refreshCombobox(self.cmbDataValid, files, "valid")
        
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

    def currentTrainCsvFile(self):
        """
        Current file name of CSV database
        """

        result = self.cmbDataTrain.SelectedValue + ".csv"
        self.GLOBAL_RESULT = result
        return result

    def currentValidCsvFile(self):
        """
        Current file name of CSV database
        """

        result = self.cmbDataValid.SelectedValue + ".csv"
        self.GLOBAL_RESULT = result
        return result

    def currentCsvFilePath(self, train=False):
        """
        Current file path to CSV database
        """

        result = os.path.join(self.currentPath(), self.currentTrainCsvFile() if train else self.currentValidCsvFile())
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

    def refreshCombobox(self, obj, data, select=None):
        """
        Refreshes combo box 'obj' items based on 'data'

        :Args:
            * obj: ComboBox object [str]
            * data: list of object to be put on combobox options [list of obj]
            * select: which data to select [obj]
        """

        def setItems(obj, data):
            obj.Items.Clear()
            for entry in data:
                obj.Items.Add(entry)
            if len(data):
                pos = data.index(select) if select is not None and select in data else 0
                obj.SelectedIndex = pos
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
            self.configure_progress_tasks(0, 0.5, 9)

            self.execute_on_gui(
                f"Initializing evaluation",
                lambda: init(self.viewScore)
            )
            self.configure_progress(0, 0, "Inicjalizacja..", False)
            self.reportProgress(0)

            self.execute_on_gui(f"Get Train CSV file path", lambda: self.currentCsvFilePath(True))
            csvTrainFilePath = self.GLOBAL_RESULT
            self.execute_on_gui(f"Get Validation CSV file path", lambda: self.currentCsvFilePath())
            csvValidFilePath = self.GLOBAL_RESULT
            self.execute_on_gui(f"Get classifier file path", lambda: self.currentEvalModulePath())
            evalFilePath = self.GLOBAL_RESULT

            classifier = importlib.import_module(evalFilePath)


            examineFile(
                dbFilePath=csvTrainFilePath,
                classifier=classifier,
                configure_progress=self.configure_progress,
                report_progress=self.reportProgress,
                is_learnig=True,
                save_converted=True)

            self.configure_progress_tasks(50, 0.5, 9, 6)
            result_validating = examineFile(
                dbFilePath=csvValidFilePath,
                classifier=classifier,
                configure_progress=self.configure_progress,
                report_progress=self.reportProgress,
                is_learnig=False)

            self.execute_on_gui(
                f"Updating score",
                lambda: setItems(self.viewScore, result_validating)
            )
            self.configure_progress(100, 0, "Wynik gotowy!")
            self.reportProgress(100)
        except Exception as ex:
            LOGGER.error(ex)
            traceback.print_exc()
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
            reported = val
            val = self.report_global_base + self.report_global_multiplier*(self.report_base + self.report_multiplier*val)
            if val < 0:
                val = 0
            if val > 100:
                val = 100
            self.prog.Value = val
            msg = f"{self.report_name} "
            if self.report_current_task >= 1 and self.report_current_task <= self.report_task_all:
                msg += f"({self.report_current_task}/{self.report_task_all}) "
            msg += f"[{reported}%]"
            self.lblStatus.Content = msg

        try:
            self.execute_on_gui(
                f"Updating progress",
                lambda: setProgress(prog)
            )
        except Exception as ex:
            LOGGER.error(ex)

    def configure_progress(self, base, multiplier, name, update=True):
        """
        Prepares for displating additional status info

        :Args:
            * base: currently used up progress [float 0:100]
            * multiplier: max progress of current operation relative to all [float 0:100]
            * name: name of status to be displayed [float 0:100]
            * current_task: current task id [int]
        """

        self.report_base = base
        self.report_multiplier = multiplier
        self.report_name = name
        if update:
            self.report_current_task += 1
        self.reportProgress(0)

    def configure_progress_tasks(self, global_base, global_multiplier, task_count, current_task=0):
        """
        Prepares for displating additional status info

        :Args:
            * task_base: base for current task base [int]
        """

        self.report_global_base = global_base
        self.report_global_multiplier = global_multiplier
        self.report_task_all = task_count
        self.report_current_task = current_task

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
