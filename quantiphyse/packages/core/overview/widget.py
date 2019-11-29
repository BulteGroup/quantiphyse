"""
Quantiphyse - Widget which displays list of all data loaded

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import print_function, division, absolute_import

import os

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data.qpdata import Visible
from quantiphyse.data import save
from quantiphyse.gui.widgets import QpWidget, HelpButton, TextViewerDialog
from quantiphyse.utils import default_save_dir, get_icon, get_local_file
from quantiphyse import __contrib__, __acknowledge__

SUMMARY = "\nCreators: " + ", ".join([author for author in __contrib__]) \
          + "\nAcknowlegements: " + ", ".join([ack for ack in __acknowledge__])

class OverviewWidget(QpWidget):
    """
    QpWidget which displays welcome info and a list of current data sets
    """

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(name="Volumes", icon="volumes", desc="Overview of volumes loaded",
                                             group="DEFAULT", position=0, **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        help_btn = HelpButton(self)
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)

        summary_label = QtGui.QLabel(SUMMARY)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        box = QtGui.QGroupBox()
        hbox = QtGui.QHBoxLayout()
        box.setLayout(hbox)
        disc = QtGui.QLabel("<font size=2> Disclaimer: This software has been developed for research purposes only, and "
                            "should not be used as a diagnostic tool. The authors or distributors will not be "
                            "responsible for any direct, indirect, special, incidental, or consequential damages "
                            "arising of the use of this software. By using the this software you agree to this disclaimer."
                            "<p>"
                            "Please read the Quantiphyse License for more information")
        disc.setWordWrap(True)
        hbox.addWidget(disc, 10)
        license_btn = QtGui.QPushButton("License")
        license_btn.clicked.connect(self._view_license)
        hbox.addWidget(license_btn)
        layout.addWidget(box)

        self.data_list = DataListWidget(self)
        layout.addWidget(self.data_list)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton()
        btn.setIcon(QtGui.QIcon(get_icon("up.png")))
        btn.setFixedSize(16, 16)
        btn.setToolTip("Raise data set in viewing order")
        btn.clicked.connect(self._up)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton()
        btn.setIcon(QtGui.QIcon(get_icon("down.png")))
        btn.setFixedSize(16, 16)
        btn.setToolTip("Lower data set in viewing order")
        btn.clicked.connect(self._down)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Rename")
        btn.clicked.connect(self._rename)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Delete")
        btn.clicked.connect(self._delete)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Save")
        btn.clicked.connect(self._save)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Set as main data")
        btn.clicked.connect(self._set_main)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Toggle ROI")
        btn.clicked.connect(self._toggle_roi)
        hbox.addWidget(btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def _view_license(self):
        license_file = get_local_file("licence.md")
        with open(license_file, "r") as f:
            text = f.read()
        dlg = TextViewerDialog(self, "Quantiphyse License", text=text)
        dlg.exec_()

    def _delete(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            ok = QtGui.QMessageBox.warning(self, "Delete data", "Delete '%s'?" % name,
                                           QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if ok:
                self.ivm.delete(name)

    def _rename(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            text, result = QtGui.QInputDialog.getText(self, "Renaming '%s'" % name, "New name",
                                                      QtGui.QLineEdit.Normal, name)
            if result:
                self.ivm.rename(name, text)

    def _save(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            data = self.ivm.data[name]
            if hasattr(data, "fname") and data.fname is not None:
                fname = data.fname
            else:
                fname = os.path.join(default_save_dir(), name + ".nii")
            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=fname,
                                                         filter="NIFTI files (*.nii *.nii.gz)")
            if fname != '':
                save(self.ivm.data[name], fname)
            else: # Cancelled
                pass

    def _set_main(self):
        if self.data_list.selected is not None:
            self.ivm.set_main_data(self.data_list.selected.name)

    def _toggle_roi(self):
        if self.data_list.selected is not None:
            self.data_list.selected.roi = not self.data_list.selected.roi
            self.ivm.sig_all_data.emit(list(self.ivm.data.keys()))

    def _down(self):
        # FIXME code duplication
        if self.data_list.selected is not None:
            last_data = None
            for data in sorted(self.ivm.data.values(), key=lambda x: x.view.z_order):
                if data == self.data_list.selected and last_data is not None:
                    current_z = data.view.z_order
                    data.view.z_order = last_data.view.z_order
                    last_data.view.z_order = current_z
                last_data = data

    def _up(self):
        if self.data_list.selected is not None:
            last_data = None
            for data in sorted(self.ivm.data.values(), key=lambda x: x.view.z_order):
                if last_data == self.data_list.selected:
                    current_z = data.view.z_order
                    data.view.z_order = last_data.view.z_order
                    last_data.view.z_order = current_z
                last_data = data

class DataListWidget(QtGui.QTableView):
    """
    Table showing loaded volumes
    """
    def __init__(self, parent):
        super(DataListWidget, self).__init__(parent)
        self.setStyleSheet("font-size: 10px; alternate-background-color: #6c6c6c;")

        self.ivm = parent.ivm
        self.ivl = parent.ivl
        self._selected = None
        self._known_data = []
        self._roi_icon = QtGui.QIcon(get_icon("roi_data.png"))
        self._data_icon = QtGui.QIcon(get_icon("data.png"))
        self._main_icon = QtGui.QIcon(get_icon("main_data.png"))
        self._vis_icon = QtGui.QIcon(get_icon("visible.png"))
        self._main_vis_icon = QtGui.QIcon(get_icon("main_ovl.png"))

        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        self._update_list()

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setTextElideMode(QtCore.Qt.ElideLeft)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().minimumSectionSize()+2)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)

        self.clicked.connect(self._clicked)
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivm.sig_main_data.connect(self._update_vis_icons)
        self.ivm.sig_current_data.connect(self._update_current)
        self.ivm.sig_current_roi.connect(self._update_current)

    @property
    def selected(self):
        """ Currently selected QpData """
        return self._selected

    def _update_current(self, data):
        # FIXME highlight row
        pass

    def _data_changed(self, data_names):
        for name in data_names:
            qpdata = self.ivm.data[name]
            if qpdata not in self._known_data:
                self._known_data.append(qpdata)
                qpdata.view.sig_changed.connect(self._view_metadata_changed)
        
        for qpdata in self._known_data[:]:
            if qpdata.name not in data_names:
                qpdata.view.sig_changed.disconnect(self._view_metadata_changed)
                self._known_data.remove(qpdata)

        self._update_list()

    def _view_metadata_changed(self, key, _value):
        if key == "visible":
            self._update_vis_icons()
        elif key == "z_order":
            self._update_list()

    def _get_table_items(self, data):
        fname = ""
        if hasattr(data, "fname") and data.fname is not None:
            fname = data.fname

        items = [
            QtGui.QStandardItem(""),
            QtGui.QStandardItem(data.name),
            QtGui.QStandardItem(fname)
        ]

        if fname:
            tooltip = fname
        else:
            tooltip = "Not saved to file"

        for item in items:
            item.setToolTip(tooltip)
        return items

    def _update_list(self):
        try:
            self.blockSignals(True)
            scroll_pos = self.verticalScrollBar().value()

            self.model.clear()
            self.model.setColumnCount(3)
            self.model.setHorizontalHeaderLabels(["", "Name", "File"])
            self.model.setHeaderData(0, QtCore.Qt.Horizontal, self._vis_icon, QtCore.Qt.DecorationRole)
            self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
            for row, data in enumerate(sorted(self.ivm.data.values(), key=lambda x: -x.view.z_order)):
                self.model.appendRow(self._get_table_items(data))

                index = self.model.index(row, 1)
                self.model.setData(index, self._roi_icon if data.roi else self._data_icon, QtCore.Qt.DecorationRole)
                self._update_vis_icon(row, data)

            self.verticalScrollBar().setValue(scroll_pos)
        finally:
            self.blockSignals(False)

    def _update_vis_icons(self):
        for row, data in enumerate(sorted(self.ivm.data.values(), key=lambda x: -x.view.z_order)):
            self._update_vis_icon(row, data)

    def _update_vis_icon(self, row, qpdata):
        is_main = qpdata == self.ivm.main
        is_visible = qpdata.view.visible
        if is_main and is_visible:
            icon = self._main_vis_icon
        elif is_main:
            icon = self._main_icon
        elif is_visible:
            icon = self._vis_icon
        else:
            icon = None
        index = self.model.index(row, 0)
        self.model.setData(index, icon, QtCore.Qt.DecorationRole)

    def _selection(self, index):
        row, col = index.row(), index.column()
        name = self.model.item(row, 1).text()
        return row, col, self.ivm.data.get(name, None)

    def _clicked(self, index):
        row, col, qpdata = self._selection(index)
        self._selected = qpdata
        if qpdata.roi and qpdata != self.ivm.current_roi:
            self.ivm.set_current_roi(qpdata.name)
        elif not qpdata.roi and qpdata != self.ivm.current_data:
            self.ivm.set_current_data(qpdata.name)

        if col == 0:
            if qpdata.view.visible:
                qpdata.view.visible = Visible.INVISIBLE
            else:
                qpdata.view.visible = Visible.VISIBLE
            self._update_vis_icon(row, qpdata)
