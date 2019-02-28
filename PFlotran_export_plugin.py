#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author : Moise Rousseau (2019)
#
# Convert Salome DAT file to Pflotran mesh input
# 
# Salome DAT ouput file description :
# line 1 : n_node n_element
# line 2 to n_node+1 : #node x y z
# line n+2 to n_node+n_element+1 : #element code list_of_node
# code = #dimension 0 #node_number, exemple : 203 for triangle, 304 for tetrahedron
#
# Pflotran input file description :
# line 1 : n_element n_node
# line 2 to n_element+1 : code(T,Q,P,W,H) list_of_node
# line n_element+2 to n_element+n_node+1 : x y z
#
# note : list of node in element line need to respect right hand rule
# for tetrahedron, the 4th need need to be in the direction of the right hand rule

# Tested only for tetrahedral meshes, until new update ...


#TODO
# add right hand rule for prism
# check pyramid
# Check HDF5 input
# add region
# dialog box for path / ascii / region
# 2D/3D automatic recognition



def Pflotran_export(context):
  """Convert Salome DAT mesh to Pflotran readable ASCII grid
  And region as HDF5 file
  Need to add Pflotran HDF5 mesh file
  Tested only for tetrahedral elements
  For other type support, need to update the check right hand rule function
  Export first from Salome to DAT file and convert to Pflotran after
  """
  
  print ("\n\n\n")
  print ("##################################\n")
  print (" Pflotran mesh converter for Salome 9.2.0 \n")
  print ("     By Moise Rousseau (2019)     \n")
  print ("  Export Salome meshes to Pflotran  \n")
  print ("    Add check for right hand rule \n")
  print ("Tested only with tetrahedral meshes\n")
  print ("and a little with Hex mesh\n")
  print ("###################################\n")
  
  def GetFolder(path):
    l = path.split('/')
    path = ''
    for i in range(0,len(l)-1):
      path = path + l[i] + '/'
    return path


  def meshSalomeToPFlotranAscii(salomeInput, PFlotranOutput, Mesh3D=True):
    
    #open salome and pflotran file
    src = open(salomeInput, 'r')
    out = open(PFlotranOutput, 'w')
    
    #read salome input first line
    line = src.readline().split(' ')
    n_node = int(line[0])
    n_element_tot = int(line[1])
    n_element_write = n_element_tot
    
    #save node coordinate for verifing right hand rule
    #initiate list
    X = [0.0]*n_node
    Y = [0.0]*n_node
    Z = [0.0]*n_node
    for i in range(0, n_node):
      line = src.readline().split(' ')
      X[i] = float(line[1])
      Y[i] = float(line[2])
      Z[i] = float(line[3])
   
    #initiate 2D/3D element type
    if Mesh3D:
      elementCode = {'304':'T', '305':'P', '306':'W', '308':'H'}
    else:
      elementCode = {'203':'T', '204':'Q'}
    #Go to 2D/3D element
    for i in range(0, n_element_tot):
      line = src.readline().split(' ')
      elementType = line[1]
      if not elementType in elementCode.keys():
        n_element_write -= 1
        continue
      break
      
    #pflotran line 1
    out.write(str(n_element_write) + ' ' + str(n_node) + '\n')
    
    #pflotran line 2 to n_element_2D/3D +1
    for i in range(0, n_element_write):
      out.write(elementCode[elementType] + ' ')
      elementNode = [int(x) for x in line[2:-1]]
      
      elementNode = checkRightHandRule(elementType, elementNode, X, Y, Z)
      
      for x in elementNode: #write
        out.write(str(x) + ' ')
      out.write('\n')
      line = src.readline().split(' ')
    
    #pflotran line n_element+1 to end
    #write node coordinates
    for i in range(0,len(X)):
      out.write(str(X[i]) + ' ' + str(Y[i]) + ' ' + str(Z[i]) + '\n')
    
    src.close()
    out.close()
    
    

  def meshSalomeToPFlotranHDF5(name, folder, PFlotranOutputName, i, Mesh3D=True):
    import h5py
    import gc
    
    #open salome and pflotran files
    src = open(folder+'DAT_raw_mesh/'+name+'.dat', 'r')
    out = h5py.File(PFlotranOutputName,mode='w')
    
    #read salome input first line
    line = src.readline().split(' ')
    n_node = int(line[0])
    n_element = int(line[1])
    
    #save node coordinate for verifing right hand rule
    #initiate list
    X = [0.0]*n_node
    Y = [0.0]*n_node
    Z = [0.0]*n_node
    for i in range(0, n_node):
      line = src.readline().split(' ')
      X[i] = float(line[1])
      Y[i] = float(line[2])
      Z[i] = float(line[3])
   
    #initiate 2D/3D element type
    if Mesh3D:
      elementCode = {'304':4, '305':5, '306':6, '308':8}
    else:
      elementCode = {'203':3, '204':4}
    
    #Go to 2D/3D element
    #TODO : Make 2D/3D recognition automatic
    while True:
      line = src.readline().split(' ')
      elementType = line[1]
      if not elementType in elementCode.keys():
        n_element -= 1
        continue
      break
      
    #initialise array
    elementsArray = [None]*n_element
    idCorrespondance = {key: int(0) for key in range(0,n_element)}
    
    #hdf5 element
    for i in range(0, n_element):
      elementArray = []
      idCorrespondance[i] = int(line[0])
      elementArray.append(elementCode[ilne[1]])
      elementNode = [int(x) for x in line[2:-1]]
      elementNode = checkRightHandRule(elementType, elementNode, X, Y, Z)
      for x in elementNode:
        elementArray.append(x)
      elementsArray[i] = elementArray
      line = src.readline().split(' ')
      
    out.create_dataset('Domain/Cells', data=elementsArray)
    del elementsArray, elementArray, elementNode, x, line #desallocate
    gc.collect()
    src.close()
    
    #hdf5 node coordinates
    vertexArray = [[float(0)]*3]*n_node
    for i in range(n_node):
      vextexArray[i][0] = X[i]
      vextexArray[i][1] = Y[i]
      vextexArray[i][2] = Z[i]
    out.create_dataset('Domain/Vertices', data=vertexArray)
    del vertexArray, X, Y, Z
    gc.collect()
    
    #Region id
    if i > 1:
    #TODO
      region_group = out.create_group("Regions")

    return



  def checkRightHandRule(elementType, elementNode, X, Y, Z):
    """
    right hand rule organize and check, only for tetrahedron and hex
    TODO for other type
    """
    
    def pointsToVec(A,B):
      """
      Create a vector AB by giving node number (A,B)
      """
      vec = (X[B-1]-X[A-1], Y[B-1]-Y[A-1], Z[B-1]-Z[A-1])
      return vec
      
    def computeProdVec(vecX,vecY):
      prodVec = (vecX[1]*vecY[2]-vecY[1]*vecX[2], vecX[2]*vecY[0]-vecY[2]*vecX[0], vecX[0]*vecY[1]-vecY[0]*vecX[1])
      return prodVec
      
    def computeDotVec(vecX,vecY):
      dot = vecX[0]*vecY[0]+vecX[1]*vecY[1]+vecX[2]*vecY[2]
      return dot
      
    def isPlan(A,B,C,D, tol = 1e-8):
      vecX = pointsToVec(A, B)
      vecY = pointsToVec(A, C)
      prodVecXY = computeProdVec(vecX, vecY)
      vecZ = pointsToVec(A, D)
      prodVecXYZ = [abs(x) for x in computeProdVec(prodVecXY, vecZ)]
      if sum(prodVecXYZ) < tol:
        return True
      else:
        return False
      
    def findFourth(elementNode):
      #1. first 3 point
      A = elementNode[0]
      B = elementNode[1]
      C = elementNode[2]
      elementNodeWork = [x for x in elementNode]
      elementNodeWork.remove(elementNode[0])
      elementNodeWork.remove(elementNode[1])
      elementNodeWork.remove(elementNode[2])
      #1. find fourth
      for x in elementNodeWork:
        if isPlan(A,B,C,x):
          elementNodeWork.remove(x)
          elementNode = [A,B,C,x]
          #anticipe 3.
          while not checkOrder(elementNode):
            continue
          while not checkOrder(elementNodeWork):
            continue
          elementNode.append(elementNodeWork)
          return True
      return False
      
    def checkOrder(elementList):
      #dont forget all 4 points in the plan
      #follow each point in the order
      #if in the right order, all vectoriel product need to be in the same direction
      vec1 = pointsToVec(elementList[0], elementList[1])
      vec2 = pointsToVec(elementList[1], elementList[2])
      prodVec12 = computeProdVec(vec1, vec2)
      vec3 = pointsToVec(elementList[2], elementList[3])
      prodVec23 = computeProdVec(vec2, vec3)
      if computeDotVec(prodVec12,prodVec23) < 0: #not in the same direction
        #here, mean that 3rd and 4th point are inversed
        #make the draw and you will see
        elementList = [elementList[0], elementList[1], elementList[3], elementList[2]]
        return False
      vec4 = pointsToVec(elementList[3], elementList[1])
      prodVec34 = computeProdVec(vec3, vec4)
      if computeDotVec(prodVec23,prodVec34) < 0:
        #here, mean that 1st and 2nd point are diagonal
        #make the draw and you will see, again
        elementList = [elementList[0], elementList[2], elementList[1], elementList[3]]
        return False
      return True
      
    
    if elementType == '304': #tetrahedron
      #method : compute normal and dot product
      #and if over the plane (>0) it's ok
      vecX = pointsToVec(elementNode[0], elementNode[1])
      vecY = pointsToVec(elementNode[0], elementNode[2])
      vecZ = pointsToVec(elementNode[0], elementNode[3])
      prodVecXY = computeProdVec(vecX, vecY)
      dotXZ = computeDotVec(prodVecXY,vecZ)

      if not dotXZ > 0: #right hand rule not respected !
        #inverse vertex 0 and 1 to turn in the right direction
        elementNode = [elementNode[1], elementNode[0], elementNode[2], elementNode[3]]
      
        
    elif elementType == '305': #Wedge
      print('Element type not supported yet...')
      #the fourth 4 nodes need to be in the same plane
      #and the 5th in the direction of the right hand rule
      #see rules for hexahedron for detail
      
      #1.
      while not findFourth(elementNode):
        elementToMove = elementNode.pop(-1)
        elementNode.insert(2, elementToMove)
      
      #4.
      normal = computeProdVec(pointsToVec(elementNode[0], elementNode[1]), pointsToVec(elementNode[1], elementNode[2])) #from 1 to 2, and from 2 to 3
      ref = computeDotVec(normal, pointsToVec(elementNode[0], elementNode[4]))
      if ref < 0:
        elementToMove = elementNode.pop(3)
        elementNode.insert(1, elementToMove)
        elementToMove = elementNode.pop(2)
        elementNode.insert(3, elementToMove)
      
      
    elif elementType == '306': #Prism
      print('Element type not supported yet...')
    
      
    elif elementType == '308': #hexahedron
      #algorithm rule :
      #1. take 3 first point and found 4th in the same plan
      #2. check if all the other point are on the same side of the plan
      #2bis. if not, take another point random point not selected and restart
      #3. Organise points to "turn" in the same direction
      #4. Check if normal point in the direction of other points
      #5. Make other turn for left hand rule x,y,z,a
      #6. 1x2y should be in the same plan
      #6bis. if not, turn xyza
            
      #1.
      while not findFourth(elementNode):
        elementToMove = elementNode.pop(-1)
        elementNode.insert(2, elementToMove)
      #2.
      normal = computeProdVec(pointsToVec(elementNode[0], elementNode[1]), pointsToVec(elementNode[1], elementNode[2])) #from 1 to 2, and from 2 to 3
      ref = computeDotVec(normal, pointsToVec(elementNode[0], elementNode[4]))
      for node in elementNode[5:]:
        if ref*computeDotVec(normal, pointsToVec(elementNode[0], node)) < 0:
          #2bis.
          elementToMove = elementNode.pop(4) #random, so the 5th
          elementNode.insert(2, elementToMove)
          #repeat 1.
          findFourth(elementNode)
      
      #3. already done in the findFourth function
      
      #4.
      if ref < 0:
        elementToMove = elementNode.pop(3)
        elementNode.insert(1, elementToMove)
        elementToMove = elementNode.pop(2)
        elementNode.insert(3, elementToMove)
      
      #5.
      #recall convention of #2
      normal = computeProdVec(pointsToVec(elementNode[0], elementNode[1]), pointsToVec(elementNode[1], elementNode[2])) #recalculate normal if change
      #point are normally in the right order from findFourth function
      normal2 = computeProdVec(pointsToVec(elementNode[4], elementNode[5]), pointsToVec(elementNode[5], elementNode[6]))
      if computeDotVec(normal, normal2) < 0: #turn in the wrong direction
        elementToMove = elementNode.pop(7)
        elementNode.insert(5, elementToMove)
        elementToMove = elementNode.pop(6)
        elementNode.insert(7, elementToMove)
      
      #6.
      A = elementNode[0]
      B = elementNode[4]
      C = elementNode[5]
      D = elementNode[1] 
      while isPlan(A,B,C,D):
        elementToMove = elementNode.pop(-1)
        elementNode.insert(4, elementToMove)
        A = elementNode[0]
        B = elementNode[4]
        C = elementNode[5]
        D = elementNode[1]
        
        
    elif elementType == '204': #Quad
      print('2D element type not supported yet...')
        
    else:
      print('Element type not supported by PFLOTRAN...')

    return elementNode


  # get context study, studyId, salomeGui
  #activeStudy = context.study
  activeStudy = salome.myStudy

  #create folder for exportation
  activeFolder = activeStudy._get_URL()
  activeFolder = GetFolder(activeFolder)
  print ("Mesh to be save in the folder " + activeFolder)
  if not os.path.exists(activeFolder+'DAT_raw_mesh/'):
    os.makedirs(activeFolder+'DAT_raw_mesh/')

  #retrieve selected meshes
  exportSubmeshFlag = True
  print ("Retrieve selected mesh")
  meshToExport = activeStudy.FindObjectID(salome.sg.getSelected(0)).GetObject()
  name = salome.smesh.smeshBuilder.GetName(meshToExport)
  i = 1 #material to export
  if not len(meshToExport.GetMeshOrder()) or not exportSubmeshFlag: #only one material
    print ("No submesh, only one material")
    #Export from Salome
    print ("Mesh export in progress...")
    meshToExport.ExportDAT(activeFolder+'DAT_raw_mesh/'+name+'.dat')
    zone_assign = open(activeFolder+name+'_zone.assignment', 'w')
    zone_assign.write('%s.dat 1\n' %(name))
    zone_assign.close()

  else:
    submeshToExport = meshToExport.GetMeshOrder()[0]
    print ("%s submeshes in the corresponding mesh" %len(submeshToExport)) 

    #Export from Salome
    print ("Mesh export in progress...")
    meshToExport.ExportDAT(activeFolder+'DAT_raw_mesh/'+name+'.dat')
    zone_assign = open(activeFolder+name+'_region.assignment', 'w')
    for mesh in submeshToExport:
      name2 = salome.smesh.smeshBuilder.GetName(mesh)
      meshToExport.ExportPartToDAT(mesh, activeFolder+'DAT_raw_mesh/'+name2+'.dat')
      zone_assign.write('%s.dat %s\n' %(name2,i))
      i = i+1
    zone_assign.close()


  #Convertion to Pflotran
  asciiOut = True
  hdf5Out = False
  if asciiOut:
    meshSalomeToPFlotranAscii(activeFolder+'DAT_raw_mesh/'+name+'.dat', activeFolder+name+'.mesh')
    if i > 1:
      print("Warning ! Ascii output not compatible with region assigning, please consider HDF5 output.\n")
  if hdf5Out:
    meshSalomeToPFlotranHDF5(activeFolder+'DAT_raw_mesh/'+name+'.dat', activeFolder+name+'.h5', i)
    

  #Delete temporary files
  delete_raw_meshes = True
  if delete_raw_meshes:
      for x in os.listdir(activeFolder+'DAT_raw_mesh'):
          os.remove(activeFolder+'DAT_raw_mesh/'+x)
      os.rmdir(activeFolder+'DAT_raw_mesh')

  print (" END \n")
  print ("####################\n\n")

  return
  
  
salome_pluginsmanager.AddFunction('Pflotran Tools/Export mesh to PFLOTRAN',
                                  'Export mesh and submesh to PFLOTRAN HDF5 format',
                                  Pflotran_export)
