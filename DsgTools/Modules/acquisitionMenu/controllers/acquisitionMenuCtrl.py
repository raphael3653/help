from DsgTools.Modules.acquisitionMenu.factories.widgetFactory import WidgetFactory
from PyQt5 import QtCore, uic, QtWidgets, QtGui
from DsgTools.Modules.qgis.controllers.qgisCtrl import QgisCtrl
import json

class AcquisitionMenuCtrl:
    
    def __init__(
            self,
            qgis=QgisCtrl(),
            widgetFactory=WidgetFactory()
        ):
        self.qgis = qgis
        self.widgetFactory = widgetFactory
        self.menuDock = None
        self.menuEditor = None
        self.addMenuTab = None
        self.addMenuButton = None
        self.reclassifyDialog  = None
        self.ignoreSignal = False
        self.connectQgisSignals()

    def unloadPlugin(self):
        self.disconnectQgisSignals()

    def connectQgisSignals(self):
        self.qgis.connectSignal( 'StartAddFeature', self.deactiveMenu )
        self.qgis.connectSignal( 'ClickLayerTreeView', self.deactiveMenu )
        self.qgis.connectSignal( 'AddLayerTreeView', self.deactiveMenu )
        self.qgis.connectSignal( 'StartEditing', self.deactiveMenu )

    def disconnectQgisSignals(self):
        self.qgis.disconnectSignal( 'StartAddFeature', self.deactiveMenu )
        self.qgis.disconnectSignal( 'ClickLayerTreeView', self.deactiveMenu )
        self.qgis.disconnectSignal( 'AddLayerTreeView', self.deactiveMenu )
        self.qgis.disconnectSignal( 'StartEditing', self.deactiveMenu )

    def openMenuEditor(self):
        if not self.menuEditor:
            self.menuEditor  = self.widgetFactory.createWidget( 'MenuEditorDialog', self )
            self.menuEditor.setMenuWidget( self.getMenuWidget() )
            self.menuEditor.setTabEditorWidget( self.getTabEditorWidget() )
            self.menuEditor.setButtonEditorWidget( self.getButtonEditorWidget() )
        self.menuEditor.showTopLevel()

    def getMenuWidget(self):
        return self.widgetFactory.createWidget( 'MenuWidget', self )

    def getTabEditorWidget(self):
        return self.widgetFactory.createWidget( 'TabEditorWidget', self )

    def getButtonEditorWidget(self):
        return self.widgetFactory.createWidget( 'ButtonEditorWidget', self )

    def getAttributeTableWidget(self):
        return self.widgetFactory.createWidget( 'AttributeTableWidget', self )

    def getFilterComboBoxWidget(self):
        return self.widgetFactory.createWidget( 'FilterComboBox', self )
    
    def openAddTabDialog(self, callback):
        self.addMenuTab  = self.widgetFactory.createWidget( 'AddTabDialog', self )
        self.addMenuTab.showTopLevel()
        self.addMenuTab.setCallback( callback )

    def openEditTabDialog(self, tabData, callback):
        self.addMenuTab  = self.widgetFactory.createWidget( 'AddTabDialog', self )
        self.addMenuTab.setData( tabData )
        self.addMenuTab.showTopLevel()
        self.addMenuTab.setCallback( callback )

    def addTabMenuEditor(self, tabId, tabName):
        self.menuEditor.addPreviewTab( tabId, tabName )

    def updateTabMenuEditor(self, tabId, tabName):
        self.menuEditor.updatePreviewTab( tabId, tabName )
    
    def deleteTabMenuEditor(self, tabId):
        self.menuEditor.deletePreviewTab( tabId )

    def getTabNamesMenuEditor(self):
        return self.menuEditor.getPreviewTabNames()

    def openAddButtonDialog(self, callback):
        tabNames = self.getTabNamesMenuEditor()
        layerNames = self.getLoadedVectorLayerNames()
        if not tabNames:
            raise Exception( 'Adicione uma aba primeiro!' )
        if not layerNames:
            raise Exception( 'Adicione uma camada primeiro!' )
        self.addMenuButton  = self.widgetFactory.createWidget( 'AddButtonDialog', self )
        self.addMenuButton.setAttributeTableWidget( self.getAttributeTableWidget() )
        self.addMenuButton.setTabComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setToolComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setLayerComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setTabNames( tabNames )
        self.addMenuButton.setLayerNames( layerNames )
        self.addMenuButton.setToolNames( self.qgis.getAcquisitionToolNames() )
        self.addMenuButton.showTopLevel()
        self.addMenuButton.setCallback( callback )

    def openEditButtonDialog(self, buttonConfig, callback):
        tabNames = self.getTabNamesMenuEditor()
        layerNames = self.getLoadedVectorLayerNames()
        if not tabNames:
            raise Exception( 'Adicione uma aba primeiro!' )
        if not layerNames:
            raise Exception( 'Adicione uma camada primeiro!' )
        self.addMenuButton = self.widgetFactory.createWidget( 'AddButtonDialog', self )
        self.addMenuButton.setAttributeTableWidget( self.getAttributeTableWidget() )
        self.addMenuButton.setTabComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setToolComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setLayerComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setTabNames( tabNames )
        self.addMenuButton.setLayerNames( layerNames )
        self.addMenuButton.setToolNames( self.qgis.getAcquisitionToolNames() )
        self.addMenuButton.setData( buttonConfig )
        self.addMenuButton.showTopLevel()
        self.addMenuButton.setCallback( callback )

    def openCloneButtonDialog(self, buttonConfig, callback):
        tabNames = self.getTabNamesMenuEditor()
        layerNames = self.getLoadedVectorLayerNames()
        if not tabNames:
            raise Exception( 'Adicione uma aba primeiro!' )
        if not layerNames:
            raise Exception( 'Adicione uma camada primeiro!' )
        self.addMenuButton  = self.widgetFactory.createWidget( 'AddButtonDialog', self )
        self.addMenuButton.setAttributeTableWidget( self.getAttributeTableWidget() )
        self.addMenuButton.setTabComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setToolComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setLayerComboWidget( self.getFilterComboBoxWidget() )
        self.addMenuButton.setTabNames( tabNames )
        self.addMenuButton.setLayerNames( layerNames )
        self.addMenuButton.setToolNames( self.qgis.getAcquisitionToolNames() )
        buttonConfig['buttonId'] = None
        buttonConfig['buttonName'] = ''
        self.addMenuButton.setData( buttonConfig )
        self.addMenuButton.showTopLevel()
        self.addMenuButton.setCallback( callback )

    def addButtonMenuEditor(self, buttonConfig, callback):
        self.menuEditor.addButtonPreviewMenu( buttonConfig, callback )

    def updateButtonMenuEditor(self, newButtonConfig, oldButtonConfig, callback):
        self.menuEditor.updateButtonPreviewMenu( newButtonConfig, oldButtonConfig, callback)

    def deleteButtonMenuEditor(self, buttonConfig):
        self.menuEditor.deleteButtonPreviewMenu( buttonConfig )

    def getLoadedVectorLayerNames(self):
        return self.qgis.getLoadedVectorLayerNames()

    def getAttributesConfigByLayerName(self, layerName):
        return self.qgis.getAttributesConfigByLayerName( layerName )

    def createMenuDock(self, menuConfigs):
        self.removeMenuDock()
        self.menuDock = self.widgetFactory.createWidget( 'MenuDock', self )
        self.menuDock.setMenuWidget( self.getMenuWidget() )
        self.menuDock.loadMenus( menuConfigs )
        self.qgis.addDockWidget( self.menuDock )

    def removeMenuDock(self):
        self.qgis.removeDockWidget( self.menuDock ) if self.menuDock else ''

    def openReclassifyDialog(self, buttonConfig, callback):
        layers = self.qgis.getVectorLayersByName( buttonConfig['buttonLayer'] )
        if not layers:
            raise Exception('Camada não encontrada!')
        if len( layers ) > 1:
            raise Exception('Há camadas repetidas!')
        layer = layers[0]
        layerName = layer.dataProvider().uri().table()
        layersToReclassification = self.getLayersForReclassification( 
            layerName,
            layer.geometryType() 
        )
        if not layersToReclassification:
            return
        if self.reclassifyDialog:
            self.reclassifyDialog.close()
        self.reclassifyDialog  = self.widgetFactory.createWidget( 'ReclassifyDialog', self )
        self.reclassifyDialog.setAttributeTableWidget( self.getAttributeTableWidget() )
        self.reclassifyDialog.loadAttributes( self.getAttributesConfigByLayerName( buttonConfig['buttonLayer'] ) )
        self.reclassifyDialog.setAttributesValues( buttonConfig['buttonAttributes'] )
        self.reclassifyDialog.loadLayersStatus( layersToReclassification )
        self.reclassifyDialog.success.connect( callback )
        self.reclassifyDialog.showTopLevel()

    def reclassify(self, buttonConfig, reclassifyData):
        destinatonLayerName = buttonConfig['buttonLayer']
        destinatonLayer = self.qgis.getVectorLayerByName( destinatonLayerName )
        selectedLayers = reclassifyData['layers']
        attributes = reclassifyData['attributes']
        layerNames = self.qgis.getVectorLayerNames( selectedLayers )
        for layerName, layer in zip(layerNames, selectedLayers):
            if destinatonLayerName == layerName:
                self.qgis.attributeSelectedFeatures( layer, attributes )
            else:
                self.qgis.cutAndPasteSelectedFeatures( layer, destinatonLayer, attributes )
    
    def getLayersForReclassification(self, layerName, geometryType):
        layers = self.qgis.getLoadedVectorLayers()
        return [
            l
            for l in layers
            if l.geometryType() == geometryType and l.selectedFeatureCount() > 0
        ]

    def activeMenuButton(self, buttonConfig):
        self.disconnectQgisSignals()
        layers = self.qgis.getVectorLayersByName( buttonConfig['buttonLayer'] )
        if not layers:
            raise Exception('Camada não encontrada!')
        if len( layers ) > 1:
            raise Exception('Há camadas repetidas!')
        layer = layers[0]
        self.ignoreSignal = True
        self.qgis.setActiveLayer( layer )
        self.ignoreSignal = False
        attributesBackup = self.qgis.getLayerVariable( layer, 'attributesBackupV1' )
        if attributesBackup:
            attributesBackup = json.loads( attributesBackup )
        else:
            attributesBackup = self.qgis.getDefaultFields( layer )
        self.qgis.suppressLayerForm( layer, buttonConfig['buttonSuppressForm'] )
        self.qgis.setDefaultFields( layer, buttonConfig['buttonAttributes'] )
        self.qgis.setLayerVariable( layer, 'attributesBackupV1', json.dumps( attributesBackup ) )
        toolName = buttonConfig['buttonAcquisitionTool']
        self.startToolByName( buttonConfig['buttonAcquisitionTool'] ) if toolName else ''
        self.connectQgisSignals()

    def deactiveMenuButton(self, buttonConfig):
        layers = self.qgis.getVectorLayersByName( buttonConfig['buttonLayer'] )
        for layer in layers:
            self.qgis.suppressLayerForm( layer, False )
            attributesBackup = self.qgis.getLayerVariable( layer, 'attributesBackupV1' )
            if not attributesBackup:
                continue
            self.qgis.setDefaultFields( layer, json.loads( attributesBackup ), reset=True )

    def deactiveMenu(self):
        if not self.menuDock:
            return
        if self.ignoreSignal:
            return
        buttonConfig = self.menuDock.getCurrentButtonConfig()
        if not buttonConfig:
            return
        self.deactiveMenuButton( buttonConfig )

    def startToolByName(self, name):
        self.qgis.startToolByName( name )

    
