# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2020-08-11
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Jossan
        email                : 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QColor
from qgis.PyQt.Qt import QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsFeature,
                       QgsDataSourceUri,
                       QgsProcessingOutputVectorLayer,
                       QgsProcessingParameterVectorLayer,
                       QgsWkbTypes,
                       QgsAction,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingUtils,
                       QgsSpatialIndex,
                       QgsGeometry,
                       QgsProcessingParameterField,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterExpression,
                       QgsProcessingException,
                       QgsProcessingParameterString,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterType,
                       QgsProcessingParameterCrs,
                       QgsCoordinateTransform,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsField,
                       QgsFields,
                       QgsProcessingOutputMultipleLayers,
                       QgsProcessingParameterString,
                       QgsConditionalStyle)
from operator import itemgetter
from collections import defaultdict
import json, os

class AssignDefaultFieldValueToLayersAlgorithm(QgsProcessingAlgorithm):

    INPUT_LAYERS = 'INPUT_LAYERS'
    FILE = 'FILE'
    TEXT = 'TEXT'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.INPUT_LAYERS,
                self.tr('Input Layers'),
                QgsProcessing.TypeVectorAnyGeometry
            )
        )

        self.addParameter(
            QgsProcessingParameterFile(
                self.FILE,
                self.tr('Input json file'),
                defaultValue = ".json"
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.TEXT,
                description =  self.tr('Input json text'),
                multiLine = True,
                defaultValue = '[]'
            )
        )

        self.addOutput(
            QgsProcessingOutputMultipleLayers(
                self.OUTPUT,
                self.tr('Original layers id with default field value')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.

        """
        inputLyrList = self.parameterAsLayerList(
            parameters,
            self.INPUT_LAYERS,
            context
        )
        inputJSONFile = self.parameterAsFile(
            parameters,
            self.FILE,
            context
        )
        inputJSONData = json.loads(
            self.parameterAsString(
                parameters,
                self.TEXT,
                context
            )
        )
        if os.path.exists(inputJSONFile):
            self.loadDefaultFieldValueFromJSONFile(inputJSONFile, inputLyrList, feedback)
        elif len(inputJSONData) > 0:
            self.loadDefaultFieldValueFromJSONData(inputJSONData, inputLyrList, feedback)
        else:
            return {self.OUTPUT: []}
        return {self.OUTPUT: [i.id() for i in inputLyrList]}

    def loadDefaultFieldValueFromJSONFile(self, inputJSONFile, inputLyrList, feedback):
        inputJSONData = json.load(inputJSONFile)
        self.loadDefaultFieldValueFromJSONData(inputJSONData, inputLyrList, feedback)
            
    def loadDefaultFieldValueFromJSONData(self, inputJSONData, inputLyrList, feedback):
        listSize = len(inputLyrList)
        progressStep = 100/listSize if listSize else 0
        layerNames = [ item['camadaNome'] for item in inputJSONData]
        for current, lyr in enumerate(inputLyrList):
            
            if feedback.isCanceled():
                break

            feedback.setProgress(current*progressStep)
            
            if not(lyr.dataProvider().uri().table() in layerNames):
                continue
            
            layerIdx = layerNames.index(lyr.dataProvider().uri().table())

            for field in inputJSONData[layerIdx]['atributos']:
                fieldIdx = lyr.fields().indexOf(field['nome'])
                if fieldIdx < 0 or not field['valor']:
                    continue
                configField = lyr.defaultValueDefinition(fieldIdx)
                configField.setExpression("'{0}'".format(field['valor']))
                lyr.setDefaultValueDefinition(fieldIdx, configField)

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'assigndefaultfieldvaluetolayersalgorithm'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Assign Default Field Value To Layers')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Layer Management Algorithms')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DSGTools: Layer Management Algorithms'

    def tr(self, string):
        return QCoreApplication.translate('AssignDefaultFieldValueToLayersAlgorithm', string)

    def createInstance(self):
        return AssignDefaultFieldValueToLayersAlgorithm()