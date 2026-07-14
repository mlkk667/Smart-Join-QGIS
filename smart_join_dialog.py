# -*- coding: utf-8 -*-

import os
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# Charge le fichier .ui depuis le même dossier
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'smart_join_dialog_base.ui'))

class SmartJoinDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(SmartJoinDialog, self).__init__(parent)
        self.setupUi(self)
        
        # Connecte la liste des couches à la liste des champs
        self.mMapLayerComboBoxTarget.layerChanged.connect(self.mFieldComboBoxTarget.setLayer)
        self.mMapLayerComboBoxSource.layerChanged.connect(self.mFieldComboBoxSource.setLayer)
        
        self.mMapLayerComboBoxTarget.layerChanged.connect(self.mFieldComboBoxTargetSecondary.setLayer)
        self.mMapLayerComboBoxSource.layerChanged.connect(self.mFieldComboBoxSourceSecondary.setLayer)
        
        self.checkBoxSecondary.toggled.connect(self.mFieldComboBoxTargetSecondary.setEnabled)
        self.checkBoxSecondary.toggled.connect(self.mFieldComboBoxSourceSecondary.setEnabled)
