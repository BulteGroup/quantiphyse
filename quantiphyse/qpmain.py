"""
Main program entry point for Quantiphyse

Copyright (c) 2013-2018 University of Oxford
"""
import sys
import warnings
if "--debug" not in sys.argv:
    # Avoid ugly warnings from some third party packages unless we are debugging
    warnings.simplefilter("ignore")

import argparse
import multiprocessing
import signal
import traceback

from PySide import QtCore, QtGui
import pyqtgraph as pg

from quantiphyse.test import run_tests
from quantiphyse.utils import QpException, debug, warn, set_local_file_path, set_debug
from quantiphyse.utils.batch import BatchScript
from quantiphyse.gui import MainWindow
from quantiphyse.gui.dialogs import error_dialog, set_main_window

# Required to use resources in theme. Check if 2 or 3.
if sys.version_info[0] > 2:
    from .resources import resource_py3
else:
    from .resources import resource_py2

def my_catch_exceptions(exc_type, exc, tb):
    """
    Catch exceptions and format appropriately

    QpException can occur due to bad user input so scary tracebacks are not included.
    Other exception types are bugs so give full traceback
    """
    if issubclass(exc_type, QpException):
        detail = exc.detail
    else:
        detail = traceback.format_exception(exc_type, exc, tb)
    error_dialog(str(exc), title="Error", detail=detail)

def main():
    """
    Parse any input arguments and run the application
    """

    # Enable multiprocessing on windows frozen binaries. Does nothing on other systems
    multiprocessing.freeze_support()

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='Load data file', default=None, type=str)
    parser.add_argument('--roi', help='Load ROI file', default=None, type=str)
    parser.add_argument('--batch', help='Run batch file', default=None, type=str)
    parser.add_argument('--debug', help='Activate debug mode', action="store_true")
    parser.add_argument('--test-all', help='Run all tests', action="store_true")
    parser.add_argument('--test', help='Specify test suite to be run (default=run all)', default=None)
    parser.add_argument('--fast', help='Run only fast tests', action="store_true")
    parser.add_argument('--qv', help='Activate quick-view mode', action="store_true")
    args = parser.parse_args()

    set_debug(args.debug)
    if args.debug:
        pg.systemInfo()

    # Set the local file path, used for finding icons, plugins, etc
    set_local_file_path()

    # OS specific changes
    if sys.platform.startswith("darwin"):
        QtGui.QApplication.setGraphicsSystem('native')

    app = QtGui.QApplication(sys.argv)
    app.setStyle('plastique')
    QtCore.QCoreApplication.setOrganizationName("ibme-qubic")
    QtCore.QCoreApplication.setOrganizationDomain("eng.ox.ac.uk")
    QtCore.QCoreApplication.setApplicationName("Quantiphyse")

    # Handle CTRL-C correctly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Check whether any batch processing arguments have been called
    if args.test_all or args.test:
        run_tests(args.test)
        sys.exit(0)
    elif args.batch is not None:
        runner = BatchScript()
        # Add delay to make sure script is run after the main loop starts, in case
        # batch script is completely synchronous
        QtCore.QTimer.singleShot(200, lambda: runner.execute({"yaml-file" : args.batch}))
    else:
        # Create window and start main loop
        win = MainWindow(load_data=args.data, load_roi=args.roi, widgets=not args.qv)
        sys.excepthook = my_catch_exceptions
        set_main_window(win)

    sys.exit(app.exec_())
