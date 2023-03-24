# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DsgTools
                                 A QGIS plugin
 Brazilian Army Cartographic Production Tools
                              -------------------
        begin                : 2022-06-20
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Philipe Borba - Cartographic Engineer @ Brazilian Army
        email                : borba.philipe@eb.mil.br
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

from collections import defaultdict
from dataclasses import dataclass
from PyQt5.QtCore import QCoreApplication

from DsgTools.core.GeometricTools.layerHandler import LayerHandler
from qgis.core import (QgsDataSourceUri, QgsFeature, QgsFeatureSink, QgsProcessing,
    QgsProcessingAlgorithm, QgsProcessingException, QgsProcessingMultiStepFeedback,
    QgsProcessingOutputVectorLayer, QgsProcessingParameterBoolean, QgsProcessingParameterDistance,
    QgsProcessingParameterFeatureSink, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField, QgsProcessingParameterVectorLayer, QgsWkbTypes, QgsProcessingFeatureSourceDefinition,
    QgsFeatureRequest)

from ...algRunner import AlgRunner
from .validationAlgorithm import ValidationAlgorithm


class IdentifyGeometriesWithLargeVertexDensityAlgorithm(ValidationAlgorithm):
    FLAGS = 'FLAGS'
    INPUT = 'INPUT'
    SELECTED = 'SELECTED'
    SEARCH_RADIUS = 'SEARCH_RADIUS'

    def initAlgorithm(self, config):
        """
        Parameter setting.
        """
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr('Input layer'),
                [
                    QgsProcessing.TypeVectorLine,
                    QgsProcessing.TypeVectorPolygon
                ]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SELECTED,
                self.tr('Process only selected features')
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.SEARCH_RADIUS,
                self.tr('Search Radius'),
                defaultValue = 1.0
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.FLAGS,
                self.tr('{0} Flags').format(self.displayName())
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        algRunner = AlgRunner()
        inputLyr = self.parameterAsVectorLayer(
            parameters,
            self.INPUT,
            context
        )
        if inputLyr is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, self.INPUT)
            )
        onlySelected = self.parameterAsBool(
            parameters,
            self.SELECTED,
            context
        )
        searchRadius = self.parameterAsDouble(
            parameters,
            self.SEARCH_RADIUS,
            context
        )
        # output flag type is a polygon because the flag will be a circle with 
        # radius tol and center as the vertex
        self.prepareFlagSink(parameters, inputLyr, QgsWkbTypes.Point, context)
        # Compute the number of steps to display within the progress bar and
        # get features from source
        multiStepFeedback = QgsProcessingMultiStepFeedback(5, feedback)
        multiStepFeedback.setCurrentStep(0)
        multiStepFeedback.setProgressText(self.tr("Building aux structure..."))
        usedInput = inputLyr if not onlySelected else QgsProcessingFeatureSourceDefinition(
            inputLyr.id(), True)
        incrementedLayer = algRunner.runAddAutoIncrementalField(
            usedInput,
            context,
            feedback=multiStepFeedback
        )
        multiStepFeedback.setCurrentStep(1)
        multiStepFeedback.setProgressText(self.tr("Extracting vertexes..."))
        vertexLayer = algRunner.runExtractVertices(
            inputLyr=incrementedLayer,
            context=context,
            feedback=multiStepFeedback
        )
        multiStepFeedback.setCurrentStep(2)
        multiStepFeedback.setProgressText(self.tr("Building spatial index on extracted vertexes..."))
        algRunner.runCreateSpatialIndex(
            inputLyr=vertexLayer,
            context=context,
            feedback=multiStepFeedback
        )
        multiStepFeedback.setCurrentStep(3)
        multiStepFeedback.setProgressText(self.tr("Searching close vertexes..."))
        flagDict = self.getCloseVertexes(vertexLayer, searchRadius, feedback=multiStepFeedback)
        multiStepFeedback.setCurrentStep(4)
        multiStepFeedback.setProgressText(self.tr("Raising flags (if any)..."))
        self.raiseFlags(flagDict, feedback=multiStepFeedback)

        return {self.FLAGS: self.flag_id}

    def raiseFlags(self, flagDict, feedback=None):
        nFlags = len(flagDict)
        if nFlags == 0:
            return
        size = 100 / nFlags
        for current, (featId, flagGeomSet) in enumerate(flagDict.items()):
            if feedback is not None and feedback.isCanceled():
                break
            if len(flagGeomSet) < 2:
                feedback.setProgress(current * size)
                continue
            for flagGeom in flagGeomSet:
                self.flagFeature(
                    flagGeom=flagGeom,
                    fromWkb=True,
                    flagText=f"Vertex from feature {featId} is too close to another vertex.",
                )
            if feedback is not None:
                feedback.setProgress(current * size)

    def getCloseVertexes(self, vertexLayer, searchRadius, feedback=None):
        flagDict = defaultdict(set) # key: featid, value: set of vertexes
        featCount = vertexLayer.featureCount()
        if featCount == 0:
            return flagDict
        size = 100 / featCount
        for current, feat in enumerate(vertexLayer.getFeatures()):
            if feedback is not None and feedback.isCanceled():
                break
            geom = feat.geometry()
            buffer = geom.buffer(searchRadius, -1)
            bufferBB = buffer.boundingBox()
            request = QgsFeatureRequest().setFilterExpression(f"featid = {feat['featid']}").setFilterRect(bufferBB)
            for candidateFeat in vertexLayer.getFeatures(request):
                if candidateFeat.id() == feat.id() or candidateFeat.geometry() in flagDict[feat["featid"]]:
                    continue
                if candidateFeat.geometry().intersects(buffer):
                    flagDict[feat["featid"]].add(geom.asWkb())
            if feedback is not None:
                feedback.setProgress(size * current)
        return flagDict

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'identifygeometrieswithlargevertexdensityalgorithm'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Identify Geometries With Large Vertex Density')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Quality Assurance Tools (Identification Processes)')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'DSGTools: Quality Assurance Tools (Identification Processes)'

    def tr(self, string):
        return QCoreApplication.translate('IdentifyGeometriesWithLargeVertexDensityAlgorithm', string)

    def createInstance(self):
        return IdentifyGeometriesWithLargeVertexDensityAlgorithm()
