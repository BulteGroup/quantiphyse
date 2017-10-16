from __future__ import print_function, division, absolute_import

from PySide import QtGui, QtCore
from ..gui.widgets import HelpButton
from ..utils import get_icon
from .._version import __version__
from . import QpWidget

class OverviewWidget(QpWidget):

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(name="Volumes", icon="volumes", desc="Overview of volumes loaded", group="DEFAULT", position=0, **kwargs)

        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        b1 = HelpButton(self)
        hbox.addWidget(b1)
        layout.addLayout(hbox)

        ta = QtGui.QLabel("\n\nThe GUI enables analysis of an MRI volume, and multiple ROIs and data "
                          "with pharmacokinetic modelling, subregion analysis and statistics included. "
                          "Please use help (?) buttons for more online information on each widget and the entire GUI. "
                          " \n \n"
                          "Creator: Benjamin Irving (mail@birving.com) \n"
                          "Contributors: Benjamin Irving, Martin Craig, Michael Chappell")
        layout.addWidget(ta)

        box = QtGui.QGroupBox()
        vbox = QtGui.QVBoxLayout()
        box.setLayout(vbox)
        disc = QtGui.QLabel("<font size=2> Disclaimer: This software has been developed for research purposes only, and "
                          "should not be used as a diagnostic tool. The authors or distributors will not be "
                          "responsible for any direct, indirect, special, incidental, or consequential damages "
                          "arising of the use of this software. The current intention of this software is for "
                          "'in house' use only and should not be distributed without the explicit consent of the "
                          "authors."
                          "\n\n"
                          "By using the this software you agree to this disclaimer (see help for more information)</font>")
        vbox.addWidget(disc)
        ta.setWordWrap(True)
        disc.setWordWrap(True)
        layout.addWidget(box)

        self.vols = DataListWidget(self)
        layout.addWidget(self.vols)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton("Rename")
        btn.clicked.connect(self.rename)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Delete")
        btn.clicked.connect(self.delete)
        hbox.addWidget(btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def delete(self):
        if self.vols.selected is not None:
            ok = QtGui.QMessageBox.warning(self, "Delete data", "Delete '%s'?" % self.vols.selected,
                                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if ok:
                if self.vols.selected_type.startswith("Data"):
                    self.ivm.delete_data(self.vols.selected)
                elif self.vols.selected_type == "ROI":
                    self.ivm.delete_roi(self.vols.selected)
                else:                
                    # Delete main volume by doing a reset
                    self.ivm.reset()

    def rename(self):
        if self.vols.selected is not None:
            text, result = QtGui.QInputDialog.getText(self, "Renaming '%s'" % self.vols.selected, "New name", 
                                                      QtGui.QLineEdit.Normal, self.vols.selected)
            if result:
                if self.vols.selected_type.startswith("Data"):
                    self.ivm.rename_data(self.vols.selected, text)
                elif self.vols.selected_type == "ROI":
                    self.ivm.rename_roi(self.vols.selected, text)
                else:
                    # Nothing else should care about the name of the main volume
                    self.ivm.main.name = text
                    self.vols.update_list(None)
       
class DataListWidget(QtGui.QTableWidget):
    """
    Table showing loaded volumes
    """
    def __init__(self, parent):
        super(DataListWidget, self).__init__(parent)
        self.ivm = parent.ivm
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Name", "Type", "File"])
        header = self.horizontalHeader();
        header.setResizeMode(2, QtGui.QHeaderView.Stretch);
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.cellClicked.connect(self.clicked)
        self.ivm.sig_main_data.connect(self.update_list)
        self.ivm.sig_current_data.connect(self.update_list)
        self.ivm.sig_all_data.connect(self.update_list)
        self.ivm.sig_current_roi.connect(self.update_list)
        self.ivm.sig_all_rois.connect(self.update_list)
        self.selected = None
        self.selected_type = None

    def get_name(self, vol):
        if vol.fname is not None:
            name = vol.fname
        else:
            name = vol.name
        return name

    def add_volume(self, row, vol_type, vol, current=False):
        self.setItem(row, 0, QtGui.QTableWidgetItem(vol.name))
        self.setItem(row, 1, QtGui.QTableWidgetItem(vol_type))
        if vol.fname is not None:
            self.setItem(row, 2, QtGui.QTableWidgetItem(vol.fname))
            item = self.item(row, 0)
            if item is not None:
                item.setToolTip(vol.fname)
            else:
                print("Weird - item is None ", vol.name)
        if current:
            font = self.item(row, 0).font()
            font.setBold(True)
            self.item(row, 0).setFont(font)
            self.item(row, 1).setFont(font)
            if vol.fname is not None: self.item(row, 2).setFont(font)
        
    def update_list(self, list1):
        try:
            self.blockSignals(True)
            n = len(self.ivm.data) + len(self.ivm.rois)
            self.setRowCount(n)
            row = 0
            for name in sorted(self.ivm.data.keys()):
                ovl = self.ivm.data[name]
                t = "Data"
                if self.ivm.main is not None and self.ivm.main.name == ovl.name:
                    t += "*"
                self.add_volume(row, t, ovl, self.ivm.is_current_data(ovl))
                row += 1
            for name in sorted(self.ivm.rois.keys()):
                roi = self.ivm.rois[name]
                self.add_volume(row, "ROI", roi, self.ivm.is_current_roi(roi))
                row += 1
        finally:
            self.blockSignals(False)

    def clicked(self, row, col):
        self.selected_type = self.item(row, 1).text()
        self.selected = self.item(row, 0).text()
        if self.selected_type.startswith("Data"):
            self.ivm.set_current_data(self.selected)
        elif self.selected_type == "ROI":
            self.ivm.set_current_roi(self.selected)

QP_WIDGETS =  [OverviewWidget]
