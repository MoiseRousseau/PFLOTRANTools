#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author : Moise Rousseau (2020), email at moise.rousseau@polymtl.ca



import sys
import os
import importlib
#import plugin component
import common
import UI_Integral_flux
importlib.reload(UI_Integral_flux)

import salome
from salome.smesh import smeshBuilder
from qtsalome import QDialog, QMessageBox, QFileDialog
from PyQt5 import QtCore

import numpy as np
import SMESH




def exportSurfaceForIntegralFlux(meshToExport, dest, gridFormat, reverse = False, option = 0):
  fatherMesh = meshToExport.GetMesh()
  out = open(dest, 'w')
  elementList = meshToExport.GetIDs()
  if reverse: out.write("INVERT_DIRECTION\n")
  if option == 1:
    out.write("FLUXES_OPTION POSITIVE_FLUXES_ONLY\n")
  elif option == 2:
    out.write("FLUXES_OPTION ABSOLUTE_FLUXES\n")
  
  if gridFormat == 1: #COOR_AND_NORMAL
    out.write("COORDINATES_AND_DIRECTIONS\n")
    for elem in elementList:
      nodes = fatherMesh.GetElemNodes(elem)
      center = common.computeCenterFromNodeList(nodes, fatherMesh)
      normal = common.getNormalFromNodeList(nodes, fatherMesh)
      out.write("  ")
      center = [str(x) for x in center]
      out.write(" ".join(center) + " ")
      normal = [str(x) for x in normal]
      out.write(" ".join(normal) + '\n')
    
  elif gridFormat == 2: #VERTICES
    out.write("VERTICES\n")
    for elem in elementList:
      out.write("  ")
      nodes = [str(x) for x in fatherMesh.GetElemNodes(elem)]
      out.write(" ".join(nodes))
      out.write('\n')
      
  elif gridFormat == 3: #CELL_IDS
    #need to build correspondance between PFLOTRAN ID and Salome ID
    fatherElems = fatherMesh.GetElementsByType(SMESH.VOLUME)
    corresp = {fatherElems[i]:i+1 for i in range(len(fatherElems))}
    out.write("CELL_IDS\n")
    for elem in elementList:
      nodes = fatherMesh.GetElemNodes(elem)
      elems = fatherMesh.GetElementsByNodes(nodes, SMESH.VOLUME)
      normal = common.getNormalFromNodeList(nodes, fatherMesh)
      test = np.array(fatherMesh.BaryCenter(elems[1]))
      test -= fatherMesh.GetNodeXYZ(nodes[0])
      if np.dot(normal,test) < 0: elems.reverse()
      elems = [str(corresp[x]) for x in elems]
      out.write("  ")
      out.write(" ".join(elems))
      out.write('\n')
      
  out.write("/")
  out.close()
  return
  
  
  


def integralFluxExport(context):

  class ExportDialog(QDialog):
    
    def __init__(self):
      QDialog.__init__(self)
      # Set up the user interface from Designer.
      #self.ui = EDZ_permeability_dataset_GUI.Ui_Dialog()
      self.ui = UI_Integral_flux.Ui_Dialog()
      self.ui.setupUi(self)
      self.show()
      
      # Connect up the selectionChanged() event of the object browser.
      #sg.getObjectBrowser().selectionChanged.connect(self.select)
      self.selectMesh = False
      self.selectedMesh = None
      self.format = True #Coordinates and direction or false = vertices
      self.reverse = False
      
      # Connect up the buttons.
      self.ui.pb_origMeshFile.clicked.connect(self.setMeshInput)
      self.ui.pb_origOutputFile.clicked.connect(self.setOutputFile)
      self.ui.pb_okCancel.accepted.connect(self.checkValue)
      #self.select()
      
      return
      
      
    def select(self):
      #sg.getObjectBrowser().selectionChanged.disconnect(self.select)
      objIds = salome.sg.getAllSelected()
      if self.selectMesh:
        self._selectMeshInput(objIds)
      return
      
    def _selectMeshInput(self, objIds):
      self.selectedMeshes = [salome.IDToObject(x) for x in objIds]
      names = []
      for selectedMesh in self.selectedMeshes:
        name = salome.smesh.smeshBuilder.GetName(selectedMesh)
        if (isinstance(selectedMesh,SMESH._objref_SMESH_Group) or
      	    isinstance(selectedMesh,SMESH._objref_SMESH_GroupOnGeom) or
      	    isinstance(selectedMesh,SMESH._objref_SMESH_GroupOnFilter) ): 
      	    # or isinstance(selectedMesh,SMESH._objref_SMESH_subMesh) ) :
          if selectedMesh.GetType() == SMESH.FACE:
      	    names.append(name)
          else:
            print(f"Integral flux can not treat {name}: not a face group")
        else:
          print(f"Integral flux can not treat {name}: not a mesh group")
      
      to_print = "; ".join(names)
      if self.ui.le_origMeshFile.text() != to_print:
        self.ui.le_origMeshFile.setText(to_print)
        self.ui.le_origOutputFile.setText('')
      return
      
    def setMeshInput(self):
      if self.selectMesh == True:
        self.selectMesh = False
        context.sg.getObjectBrowser().selectionChanged.disconnect(self.select)
      else:
        self.selectMesh = True
        context.sg.getObjectBrowser().selectionChanged.connect(self.select)
        self.select()
      return
      
    def setOutputFile(self):
      selection = 'Integral Flux files (*.txt);;All Files (*)'
      ext = 'txt'
      fd = QFileDialog(self, "Select an output file", 
                       self.ui.le_origOutputFile.text(), selection)
      if len(self.selectedMeshes) > 1:
        fd.setFileMode(QFileDialog.Directory)
      else:
        fd.setFileMode(QFileDialog.AnyFile)
      if fd.exec_():
        if len(self.selectedMeshes) > 1:
          text = fd.directory().path()+'/'
        else:
          text = fd.selectedFiles()[0]
          if text.split('.')[-1] != ext: text = text + '.' + ext
        self.ui.le_origOutputFile.setText(text)
      return
      
    def printErrorMessage(self, text):
      #import qtsalome
      #msg = qtsalome.QMessageBox()
      msg = QMessageBox()
      #msg.setTitle('Error!')
      msg.setText(text)
      msg.setIcon(QMessageBox.Critical)
      msg.setStandardButtons(QMessageBox.Ok)
      msg.exec_()
      return
      
    def printInformationMessage(self, text):
      #import qtsalome
      msg = QMessageBox()
      #msg.setTitle('Error!')
      msg.setText(text)
      msg.setIcon(QMessageBox.Information)
      msg.setStandardButtons(QMessageBox.Ok)
      msg.exec_()
      return
      
    def printMessageYesNo(self, text):
      #import qtsalome
      msg = QMessageBox()
      #msg.setTitle('Error!')
      msg.setText(text)
      msg.setIcon(QMessageBox.Information)
      msg.setStandardButtons(QMessageBox.Yes| QMessageBox.No)
      reply = msg.exec_()
      if reply == QMessageBox.Yes: return True
      else: return False
      
    def checkValue(self):
      #check output file
      if not self.ui.le_origOutputFile.text():
        self.printErrorMessage('Please provide an output file')
        return
      if os.path.isfile(self.ui.le_origOutputFile.text()):
        res = self.printMessageYesNo('The output file you provided already exist and will be ecrased. Continue ?')
        if not res:
          return
      self.accept()
      return
  
  window = ExportDialog()
  window.exec_()
  result = window.result()
  
  if result:
    print ("\n\n\n")
    print ("##########################################\n")
    print (" Integral flux maker \n")
    print ("        By Moise Rousseau (2020)     \n")
    print ("     \n")
    print ("##########################################\n")
    
    #retrieve data from the GUI
    #mesh to export
    meshesToExport = window.selectedMeshes #Mesh object
    #destination file or folder
    dest = window.ui.le_origOutputFile.text()
    #grid format
    COOR_AND_DIR = 1 ; VERTICES = 2 ; CELL_IDS = 3
    if window.ui.rb_gridFormat[0].isChecked(): gridFormat = COOR_AND_DIR
    elif window.ui.rb_gridFormat[1].isChecked(): gridFormat = VERTICES
    else: gridFormat = CELL_IDS
    #Fluxes option
    SIGNED = 0 ; POSITIVE = 1 ; ABSOLUTE = 2
    if window.ui.comboBox_option.currentText() == 'Signed fluxes': option = SIGNED
    elif window.ui.comboBox_option.currentText() == 'Positive fluxes only': option = POSITIVE
    elif window.ui.comboBox_option.currentText() == 'Absolute fluxes': option = ABSOLUTE
    #reverse
    reverse = False
    if window.ui.cb_reverse.isChecked(): reverse= True
    
    #Export selected meshes
    if len(meshesToExport) > 1:
      for meshToExport in meshesToExport:
        name = meshToExport.GetName()
        print ("Create surface integral file: " + name)
        file_name = dest + name + ".txt"
        exportSurfaceForIntegralFlux(meshToExport, file_name, 
                                     gridFormat, reverse, option)
    else:
      print ("Create surface integral file: " + meshesToExport[0].GetName())
      exportSurfaceForIntegralFlux(meshesToExport[0], dest, gridFormat, reverse, option)
    
    print ("    END \n")
    print ("####################\n\n")

  return

