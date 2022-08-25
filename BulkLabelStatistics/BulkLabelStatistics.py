import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import glob
#
# BulkLabelStatistics
#

class BulkLabelStatistics(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "BulkLabelStatistics"
    self.parent.categories = ["Quantification"]
    self.parent.dependencies = ["SegmentStatistics"]
    self.parent.contributors = ["Rafael Palomar (Oslo University Hospital)"]
    self.parent.helpText = """
    This module can perform labelmap statistics in bulk. It requires a pool of volumes and a pool of segmentation.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
    This file was originally developed by Rafael Palomar (Oslo University Hospital) after Egidijus Pelanis (Oslo University Hospital) kindly requested it.
"""

#
# BulkLabelStatisticsWidget
#

class BulkLabelStatisticsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/BulkLabelStatistics.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = BulkLabelStatisticsLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    self.ui.segmentationsDirLabel.enabled = False;
    self.ui.outputFileLabel.enabled = False;
    self.ui.computeStatisticsPushButton.enabled = False;

    self.ui.segmentationsDirPushButton.connect('clicked(bool)', self.onSegmentationDirButtonPushed)
    self.ui.outputFilePushButton.connect('clicked(bool)', self.onOutputFileButtonPushed)
    self.ui.computeStatisticsPushButton.connect('clicked(bool)', self.onComputeStatisticsPushButton)

    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    self._parameterNode.EndModify(wasModified)

  def onSegmentationDirButtonPushed(self):
    """
    Action when segmentation directory push button is clicked
    """
    directory = qt.QFileDialog.getExistingDirectory(None,"Choose the Segmentation directory")
    if directory != '' :
      self.ui.segmentationsDirLabel.setText(directory)
      self.ui.segmentationsDirLabel.enabled = True
    else:
      self.ui.segmentationsDirLabel.setText('No segmentation directory specified')
      self.ui.segmentationsDirLabel.enabled = False

    self.enableComputeStatisticsPushButton()

  def onOutputFileButtonPushed(self):
    """
    Action when output file push button is clicked
    """
    outputFile = qt.QFileDialog.getSaveFileName(None,"Save results as...")
    if outputFile != '' :
      self.ui.outputFileLabel.setText(outputFile)
      self.ui.outputFileLabel.enabled = True
    else:
      self.ui.outputFileLabel.setText('No output file specified')
      self.ui.outputFileLabel.enabled = False

    self.enableComputeStatisticsPushButton()

  def enableComputeStatisticsPushButton(self):
    """
    Check whether directories have been privided and enables/disables the compute statistics button
    """
    if self.ui.segmentationsDirLabel.enabled and self.ui.outputFileLabel.enabled:
      self.ui.computeStatisticsPushButton.enabled = True
    else:
      self.ui.computeStatisticsPushButton.enabled = False

  def onComputeStatisticsPushButton(self):
    """
    Run processing when user clicks "Apply" button.
    """
    try:

      # Compute output
      # TODO: not very elegant getting a parameter from a text label, I know...
      self.logic.process(self.ui.segmentationsDirLabel.text,
                         self.ui.outputFileLabel.text,
                         self.ui.statusLabel,
                         self.ui.progressBar)

    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()

#
# BulkLabelStatisticsLogic
#

class BulkLabelStatisticsLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    pass

  def process(self, segmentationsDir, outputFile, statusLabel, progressBar):

    segmentations = glob.glob(segmentationsDir+ '/segmentation*')

    print(segmentations)

    from SegmentStatistics import SegmentStatisticsLogic

    progressBar.setRange(0,len(segmentations))
    progressBarValue = 0
    progressBar.setValue(progressBarValue)
    header = True

    with open(outputFile, 'w') as f:

      for segmentation in segmentations:

        slicer.mrmlScene.Clear()

        statusLabel.setText('Status: Loading ' + segmentation)
        segmentationNode = slicer.util.loadSegmentation(segmentation)

        statusLabel.setText('Stauts: Computing statistics for ' + segmentation)
        logic = SegmentStatisticsLogic()
        parameterNode = logic.getParameterNode();
        parameterNode.SetParameter("Segmentation", segmentationNode.GetID())
        newTable = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
        # parameterNode.SetParameter("MeasurementsTable", newTable.GetID())
        logic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.voxel_count.enabled",str(True))
        logic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.volume_cm3.enabled",str(True))
        logic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.surface_area_mm2.enabled",str(True))
        logic.computeStatistics()
        logic.exportToTable(newTable)
        logic.showTable(newTable)

        statusLabel.setText('Stauts: Exporting statistics for ' + segmentation)
        # Write the header for the first time
        if header:
          self.writeHeaderToCSV(newTable, f)
          header = False

        self.writeDataToCSV(segmentation, newTable, f)

        progressBarValue+=1
        progressBar.setValue(progressBarValue)

    f.close()

    statusLabel.setText('Status: Completed')
    print("Completed!")

  def writeHeaderToCSV(self, table, _file):
    """
    Writes the CSV header to file
    """
    _file.write('Dataset,')
    for j in range(table.GetNumberOfColumns()):
      if j < table.GetNumberOfColumns() -1:
        _file.write(table.GetColumnName(j) + ',')
      else:
        _file.write(table.GetColumnName(j) + '\n')

  def writeDataToCSV(self, dataset, table, _file):
    """
    Writes the statistics in CSV format (wihtout header)
    """
    for i in range(table.GetNumberOfRows()):
      for j in range(table.GetNumberOfColumns()+1):
        if j == 0:
          _file.write(dataset + ',')
        elif j>0 and j < table.GetNumberOfColumns():
          _file.write(table.GetCellText(i,j-1) + ',')
        else:
          _file.write(table.GetCellText(i,j-1) + '\n')






#
# BulkLabelStatisticsTest
#

class BulkLabelStatisticsTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_BulkLabelStatistics1()

  def test_BulkLabelStatistics1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    registerSampleData()
    inputVolume = SampleData.downloadSample('BulkLabelStatistics1')
    self.delayDisplay('Loaded test data set')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 695)

    outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
    threshold = 100

    # Test the module logic

    logic = BulkLabelStatisticsLogic()

