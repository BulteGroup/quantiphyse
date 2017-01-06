import os.path
import re
import numpy as np

from PySide import QtGui
import nibabel as nib

from pkview.analysis.t1_model import t10_map

class NumberInput(QtGui.QHBoxLayout):
    def __init__(self, text, initial_val):
        super(NumberInput, self).__init__()
        self.text = text
        self.val = initial_val

        label = QtGui.QLabel(self.text)
        self.addWidget(label)
        self.edit = QtGui.QLineEdit(str(self.val))
        self.addWidget(self.edit)
        self.edit.editingFinished.connect(self.changed)
        self.addStretch(1)

    def changed(self):
        try:
            self.val = float(self.edit.text())
            print(self.text, self.val)
        except:
            self.gen.setEnabled(False)
            QtGui.QMessageBox.warning(self, "Invalid value", "%s must be a number" % self.text, QtGui.QMessageBox.Close)

class SourceImageList(QtGui.QVBoxLayout):
    def __init__(self, header_text):
        super(SourceImageList, self).__init__()

        self.header_text = header_text
        self.dir = None
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setHorizontalHeaderLabels(["Filename", header_text])
        header = self.table.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.addWidget(self.table)

        bbox = QtGui.QHBoxLayout()
        b1 = QtGui.QPushButton('Add')
        b1.clicked.connect(self.add)
        bbox.addWidget(b1)
        b2 = QtGui.QPushButton('Remove')
        b2.clicked.connect(self.remove)
        bbox.addWidget(b2)
        self.addLayout(bbox)

    def check_file(self, filename):
        """
        Check that filename is a valid FA image. It must be
        3D (currently - 4D may be possible but must be handled differently)
        and must have shape consistent with the main volume
        """
        try:
            print(filename)
            f = nib.load(filename)
            data = f.get_data()
            print(data.shape)
            if len(data.shape) not in (3, 4):
                QtGui.QMessageBox.warning(None, "Invalid file", "File must be 3D or 4D volumes",
                                          QtGui.QMessageBox.Close)
                return []

            if data.shape[:3] != self.ivm.img_dims[:3]:
                QtGui.QMessageBox.warning(None, "Invalid file", "File dimensions must match the loaded volume",
                                          QtGui.QMessageBox.Close)
                return []
        except:
            QtGui.QMessageBox.warning(None, "Invalid file", "Files must be NIFTI volumes",
                                      QtGui.QMessageBox.Close)
            return []

        return data.shape

    def load_image(self, filename):
        # Try to guess the angle from the filename - if it ends in a number, go with that
        self.dir, name = os.path.split(filename)
        name = name.split(".")[0]
        print(name)
        m = re.search(r"(\d+).*$", name)
        if m is not None:
            guess = m.group(1)
        else:
            guess = ""
        print("Guess: ", guess)

        while 1:
            text, result = QtGui.QInputDialog.getText(None, "Enter value", "Enter %s" % self.header_text, text=guess)
            if result:
                try:
                    fa = float(text)
                    self.table.insertRow(0)
                    self.table.setItem(0, 0, QtGui.QTableWidgetItem(filename))
                    self.table.setItem(0, 1, QtGui.QTableWidgetItem(text))
                    break
                except:
                    QtGui.QMessageBox.warning(None, "Invalid value", "Must be a number", QtGui.QMessageBox.Close)
            else:
                break

    def load_multi_images(self, filename, n):
        guess=""
        while 1:
            text, result = QtGui.QInputDialog.getText(None, "Enter values",
                                                      "Enter %s as a series of %i comma-separated values" % (self.header_text, n),
                                                      text=guess)
            if result:
                try:
                    fas = [float(v) for v in text.split(",")]
                    if len(fas) != n:
                        QtGui.QMessageBox.warning(None, "Wrong number of values",
                                                  "Must enter %i values, you entered %i" % (n, len(fas)),
                                                  QtGui.QMessageBox.Close)
                        guess = text
                    else:
                        self.table.insertRow(0)
                        self.table.setItem(0, 0, QtGui.QTableWidgetItem(filename))
                        self.table.setItem(0, 1, QtGui.QTableWidgetItem(text))
                        break
                except:
                    QtGui.QMessageBox.warning(None, "Invalid value", "Must be a series of comma-separated numbers",
                                              QtGui.QMessageBox.Close)
            else:
                break

    def add(self):
        filename, junk = QtGui.QFileDialog.getOpenFileName(None, "Open image", dir=self.dir)
        if filename:
            dims = self.check_file(filename)
            if len(dims) == 3:
                self.load_image(filename)
            elif len(dims) == 4:
                self.load_multi_images(filename, dims[3])

    def remove(self):
        row = self.table.currentRow()
        print("Current row: ", row)
        self.table.removeRow(row)
        fa_angles = []
        print("TR=", self.trval)

    def get_images(self):
        vols = []
        vals = []
        for i in range(self.table.rowCount()):
            filename = self.table.item(i, 0).text()
            file_vals = [float(v) for v in self.table.item(i, 1).text().split(",")]
            print(filename, vals)
            img = nib.load(filename)
            vol = img.get_data()
            if len(file_vals) == 1:
                # FIXME need to check dimensions against volume?
                vols.append(vol)
                vals.append(file_vals[0])
            else:
                for i, val in enumerate(file_vals):
                    subvol=vol[...,i]
                    vols.append(subvol)
                    vals.append(val)
        return vols, vals

class T10Widget(QtGui.QWidget):
    """
    Run T10 analysis on 3 input volumes
    """
    def __init__(self):
        super(T10Widget, self).__init__()
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel("<font size=5>T10 map generation</font>"))

        fabox = QtGui.QGroupBox()
        fabox.setTitle("Flip angle images")
        self.fatable = SourceImageList("Flip angle")
        fabox.setLayout(self.fatable)
        self.trinp = NumberInput("TR", 4.108)
        self.fatable.addLayout(self.trinp)
        layout.addWidget(fabox)

        self.preclin = QtGui.QCheckBox("Use B0 correction (Preclinical)")
        self.preclin.stateChanged.connect(self.preclin_changed)
        self.preclin.setChecked(False)
        layout.addWidget(self.preclin)

        self.preclinGroup = QtGui.QGroupBox("")
        self.preclinGroup.setTitle("B0 correction")
        self.preclinGroup.setVisible(False)
        self.trtable = SourceImageList("TR (s)")
        self.preclinGroup.setLayout(self.trtable)
        self.fainp = NumberInput("Flip angle (AFI)", 64)
        self.trtable.addLayout(self.fainp)
        self.smooth = QtGui.QCheckBox("Smooth")
        self.trtable.addWidget(self.smooth)
        layout.addWidget(self.preclinGroup)

        hbox = QtGui.QHBoxLayout()
        self.clamp = QtGui.QCheckBox("Clamp T10 values between")
        self.clamp.stateChanged.connect(self.clamp_changed)
        self.clamp.setChecked(False)
        hbox.addWidget(self.clamp)
        self.clampMin = QtGui.QDoubleSpinBox()
        self.clampMin.setValue(0)
        hbox.addWidget(self.clampMin)
        hbox.addWidget(QtGui.QLabel("and"))
        self.clampMax = QtGui.QDoubleSpinBox()
        self.clampMax.setValue(5)
        hbox.addWidget(self.clampMax)
        self.clamp_changed()
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.gen = QtGui.QPushButton('Generate T1 map', self)
        self.gen.clicked.connect(self.generate)
        hbox.addWidget(self.gen)
        hbox.addStretch(1)
        layout.addLayout(hbox)

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management
        self.fatable.ivm = self.ivm
        self.trtable.ivm = self.ivm

    def preclin_changed(self):
        self.preclinGroup.setVisible(self.preclin.isChecked())

    def clamp_changed(self):
        self.clampMin.setEnabled(self.clamp.isChecked())
        self.clampMax.setEnabled(self.clamp.isChecked())

    def generate(self):
        if self.ivm.img_dims is None:
            QtGui.QMessageBox.warning(self, "No volume", "Load a volume before generating T10 map", QtGui.QMessageBox.Close)
            return

        fa_vols, fa_angles = self.fatable.get_images()
        # TR is expected in seconds but UI asks for it in ms
        tr = self.trinp.val / 1000
        print(tr, fa_angles)

        if self.preclin.isChecked():
            afi_vols, afi_trs = self.trtable.get_images()
            fa_afi = self.fainp.val
            print(fa_afi, afi_vols, afi_trs)
            T10 = t10_map(fa_vols, fa_angles, TR=tr,
                      afi_vols=afi_vols, fa_afi=fa_afi, TR_afi=afi_trs)
            if self.smooth.isChecked():
                print("Smoothing map")
                T10 = gaussian_filter(T10, sigma=0.5, truncate=3)
        else:
            T10 = t10_map(fa_vols, fa_angles, TR=tr)

        if self.clamp.isChecked():
            np.clip(T10, self.clampMin.value(), self.clampMax.value(), out=T10)

        self.ivm.set_overlay(name="T10", data=T10, force=True)
        self.ivm.set_current_overlay("T10")