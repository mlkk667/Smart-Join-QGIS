# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt import QtWidgets
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, 
    QgsField, QgsFields, QgsWkbTypes
)
import os
import difflib
import re

from .smart_join_dialog import SmartJoinDialog

def get_token_set_ratio(s1, s2):
    t1 = set(re.findall(r'\w+', str(s1).lower()))
    t2 = set(re.findall(r'\w+', str(s2).lower()))
    if not t1 or not t2: return 0
    intersection = t1.intersection(t2)
    rest1 = t1 - intersection
    rest2 = t2 - intersection
    str_inter = " ".join(sorted(intersection))
    str_rest1 = " ".join(sorted(rest1))
    str_rest2 = " ".join(sorted(rest2))
    
    s0 = str_inter
    s1_comb = (str_inter + " " + str_rest1).strip()
    s2_comb = (str_inter + " " + str_rest2).strip()
    
    r1 = difflib.SequenceMatcher(None, s0, s1_comb).ratio()
    r2 = difflib.SequenceMatcher(None, s0, s2_comb).ratio()
    r3 = difflib.SequenceMatcher(None, s1_comb, s2_comb).ratio()
    return max(r1, r2, r3) * 100

class SmartJoin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = u'&Smart Join'

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        # Utilise une icone générique de QGIS pour simplifier
        icon_path = ':/images/themes/default/mActionAddOgrLayer.svg'
        self.add_action(
            icon_path,
            text=u'Fuzzy Smart Join',
            callback=self.run,
            parent=self.iface.mainWindow()
        )

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(u'&Smart Join', action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        dlg = SmartJoinDialog()
        
        # Initialise les listes déroulantes de champs avec la première couche sélectionnée
        if dlg.mMapLayerComboBoxTarget.currentLayer():
            dlg.mFieldComboBoxTarget.setLayer(dlg.mMapLayerComboBoxTarget.currentLayer())
            dlg.mFieldComboBoxTargetSecondary.setLayer(dlg.mMapLayerComboBoxTarget.currentLayer())
        if dlg.mMapLayerComboBoxSource.currentLayer():
            dlg.mFieldComboBoxSource.setLayer(dlg.mMapLayerComboBoxSource.currentLayer())
            dlg.mFieldComboBoxSourceSecondary.setLayer(dlg.mMapLayerComboBoxSource.currentLayer())
            
        dlg.show()
        result = dlg.exec()
        
        if result:
            target_layer = dlg.mMapLayerComboBoxTarget.currentLayer()
            source_layer = dlg.mMapLayerComboBoxSource.currentLayer()
            target_field = dlg.mFieldComboBoxTarget.currentField()
            source_field = dlg.mFieldComboBoxSource.currentField()
            threshold = dlg.spinBoxThreshold.value()
            
            target_field_sec = None
            source_field_sec = None
            if dlg.checkBoxSecondary.isChecked():
                target_field_sec = dlg.mFieldComboBoxTargetSecondary.currentField()
                source_field_sec = dlg.mFieldComboBoxSourceSecondary.currentField()
                
            one_to_one = dlg.checkBoxOneToOne.isChecked()
            
            if not target_layer or not source_layer or not target_field or not source_field:
                QMessageBox.warning(self.iface.mainWindow(), "Erreur", "Veuillez sélectionner toutes les couches et champs principaux.")
                return
                
            self.perform_join(target_layer, source_layer, target_field, source_field, threshold, target_field_sec, source_field_sec, one_to_one)
            
    def perform_join(self, target_layer, source_layer, target_field, source_field, threshold, target_field_sec=None, source_field_sec=None, one_to_one=True):
        try:
            # Mettre en cache les entités sources pour ne pas ralentir le processus
            source_features = {}
            source_fields = source_layer.fields()
            
            for feat in source_layer.getFeatures():
                val = feat[source_field]
                val_sec = feat[source_field_sec] if source_field_sec else None
                if val is not None:
                    source_features[feat.id()] = {
                        'feat': feat,
                        'val': str(val),
                        'val_sec': str(val_sec) if val_sec is not None else ""
                    }

            # Préparer la nouvelle couche mémoire (Cible enrichie)
            crs = target_layer.crs().authid()
            geom_type = "Polygon" # Default fallback
            if target_layer.wkbType() == QgsWkbTypes.Type.Point: geom_type = "Point"
            elif target_layer.wkbType() == QgsWkbTypes.Type.LineString: geom_type = "LineString"
            elif target_layer.wkbType() == QgsWkbTypes.Type.Polygon: geom_type = "Polygon"
            elif target_layer.wkbType() == QgsWkbTypes.Type.MultiPoint: geom_type = "MultiPoint"
            elif target_layer.wkbType() == QgsWkbTypes.Type.MultiLineString: geom_type = "MultiLineString"
            elif target_layer.wkbType() == QgsWkbTypes.Type.MultiPolygon: geom_type = "MultiPolygon"
            
            uri = f"{geom_type}?crs={crs}"
            memory_layer = QgsVectorLayer(uri, f"{target_layer.name()}_joined", "memory")
            pr = memory_layer.dataProvider()
            
            # Fusionner les champs (Champs Cible + Champs Source)
            new_fields = QgsFields()
            for f in target_layer.fields():
                new_fields.append(f)
                
            # Éviter les doublons de noms de champs
            target_field_names = [f.name() for f in target_layer.fields()]
            
            source_field_mapping = {} # index source -> nouvel index
            for f in source_fields:
                if f.name() not in target_field_names:
                    new_fields.append(f)
                    source_field_mapping[f.name()] = new_fields.indexFromName(f.name())
                else:
                    # Ajoute un suffixe en cas de conflit
                    new_f = QgsField(f.name() + "_src", f.type())
                    new_fields.append(new_f)
                    source_field_mapping[f.name()] = new_fields.indexFromName(new_f.name())
                    
            pr.addAttributes(new_fields.toList())
            memory_layer.updateFields()
            
            target_features = list(target_layer.getFeatures())
            total = len(target_features)
            
            # Afficher une barre de progression
            progressMessageBar = self.iface.messageBar().createMessage("Smart Join", "Calcul de la jointure floue en cours...")
            progress = QtWidgets.QProgressBar()
            progress.setMaximum(total)
            progress.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(progressMessageBar)
            
            new_features = []
            matches = 0
            
            if one_to_one:
                # Etape 1: Calculer TOUS les scores
                progressMessageBar.layout().itemAt(0).widget().setText("Smart Join - Etape 1/2: Calcul des correspondances...")
                all_scores = []
                for i, t_feat in enumerate(target_features):
                    progress.setValue(i)
                    QCoreApplication.processEvents()
                    t_val = t_feat[target_field]
                    if t_val is None: continue
                    t_val_str = str(t_val)
                    t_val_sec_str = str(t_feat[target_field_sec]) if target_field_sec and t_feat[target_field_sec] is not None else ""
                    
                    for s_id, s_data in source_features.items():
                        s_val_str = s_data['val']
                        s_val_sec_str = s_data['val_sec']
                        
                        ratio_main = get_token_set_ratio(t_val_str, s_val_str)
                        if target_field_sec and source_field_sec:
                            ratio_sec = get_token_set_ratio(t_val_sec_str, s_val_sec_str)
                            ratio = (ratio_main + ratio_sec) / 2.0
                        else:
                            ratio = ratio_main
                            
                        if ratio >= threshold:
                            all_scores.append( (ratio, t_feat.id(), s_id) )
                
                # Etape 2: Mariage stable (Greedy)
                all_scores.sort(key=lambda x: x[0], reverse=True)
                assigned_targets = set()
                assigned_sources = set()
                match_dict = {} # target_id -> source_feat
                
                for ratio, t_id, s_id in all_scores:
                    if t_id not in assigned_targets and s_id not in assigned_sources:
                        assigned_targets.add(t_id)
                        assigned_sources.add(s_id)
                        match_dict[t_id] = source_features[s_id]['feat']
                        
                # Creation des entites
                progressMessageBar.layout().itemAt(0).widget().setText("Smart Join - Etape 2/2: Creation de la couche...")
                for i, t_feat in enumerate(target_features):
                    progress.setValue(i)
                    QCoreApplication.processEvents()
                    
                    new_f = QgsFeature(new_fields)
                    new_f.setGeometry(t_feat.geometry())
                    for idx in range(t_feat.fields().count()):
                        new_f.setAttribute(idx, t_feat.attribute(idx))
                        
                    best_match_feat = match_dict.get(t_feat.id())
                    if best_match_feat:
                        matches += 1
                        for s_field_name, new_idx in source_field_mapping.items():
                            new_f.setAttribute(new_idx, best_match_feat[s_field_name])
                    new_features.append(new_f)
                    
            else:
                # Mode Many-to-One classique
                for i, t_feat in enumerate(target_features):
                    progress.setValue(i)
                    QCoreApplication.processEvents()
                    
                    t_val = t_feat[target_field]
                    best_match_feat = None
                    
                    if t_val is not None:
                        t_val_str = str(t_val)
                        t_val_sec_str = str(t_feat[target_field_sec]) if target_field_sec and t_feat[target_field_sec] is not None else ""
                        best_ratio = 0
                        
                        for s_id, s_data in source_features.items():
                            s_val_str = s_data['val']
                            s_val_sec_str = s_data['val_sec']
                            s_feat = s_data['feat']
                            
                            ratio_main = get_token_set_ratio(t_val_str, s_val_str)
                            if target_field_sec and source_field_sec:
                                ratio_sec = get_token_set_ratio(t_val_sec_str, s_val_sec_str)
                                ratio = (ratio_main + ratio_sec) / 2.0
                            else:
                                ratio = ratio_main
                                
                            if ratio > best_ratio:
                                best_ratio = ratio
                                best_match_feat = s_feat
                                if best_ratio == 100:
                                    break
                        
                        if best_ratio < threshold:
                            best_match_feat = None
                    
                    # Créer la nouvelle entité
                    new_f = QgsFeature(new_fields)
                    new_f.setGeometry(t_feat.geometry())
                    for idx in range(t_feat.fields().count()):
                        new_f.setAttribute(idx, t_feat.attribute(idx))
                        
                    if best_match_feat:
                        matches += 1
                        for s_field_name, new_idx in source_field_mapping.items():
                            new_f.setAttribute(new_idx, best_match_feat[s_field_name])
                            
                    new_features.append(new_f)
                
            pr.addFeatures(new_features)
            memory_layer.updateExtents()
            QgsProject.instance().addMapLayer(memory_layer)
            
            self.iface.messageBar().clearWidgets()
            QMessageBox.information(self.iface.mainWindow(), "Terminé", f"Jointure terminée ! {matches} correspondances trouvées sur {total} entités cibles.")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            QMessageBox.critical(self.iface.mainWindow(), "Erreur Critique", f"Une erreur s'est produite : {str(e)}\n\nDétails:\n{error_msg}")
