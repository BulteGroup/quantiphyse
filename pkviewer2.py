import argparse
from PySide import QtGui
from pkview.pkviewer import MainWin1
import sys

if __name__ == '__main__':
    """
    Run the application
    """

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', help='DCE-MRI nifti file location', default=None, type=str)
    parser.add_argument('--roi', help='ROI nifti file location', default=None, type=str)
    parser.add_argument('--overlay', help='Overlay nifti file location', default=None, type=str)
    args = parser.parse_args()


    app = QtGui.QApplication(sys.argv)
    ex = MainWin1(args.image, args.roi, args.overlay)
    sys.exit(app.exec_())