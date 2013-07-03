# BeliefVector.py
# $Revision: 1.1.1.1 $
# $Date: 2005/09/01 19:41:34 $

import viz, Navigator


class __BeliefVectorMap:
	# filename is a text file showing the layout.
	def __init__(self,filename,width,height,length):
		self.viewmode = 0
		self.scale = width + length
		self.width = width
		self.height = height
		self.length = length

		#target location pointer
		self.targetpointer = viz.addchild('./Layouts/SharedMedia/Objects/bvmap_target_pointer.wrl')
		self.targetpointer.scale(self.scale*0.8,self.scale*0.8,self.scale*0.8)
		self.targetpointer.disable(viz.LIGHTING)
		self.targetpointer.curtain(viz.CLOSE)
		(_w,_h,_s) = Navigator.getPlatDim(filename)
		MyPlat = Navigator.PLAT(_w,_h,_s)
		MyPlat.ReadTextImage(filename)
		#MyPlat.DisplayTextImage()

		maxx = -1
		maxy = -1
		minx = -1
		miny = -1

		#belief vector pointers
		self.pointers = []		
		
		for y in range(MyPlat.y):
			for x in range(MyPlat.x):
				if (x,y) in MyPlat.ChosenList:
					if x > maxx or maxx == -1: maxx = x
					if x < minx or minx == -1: minx = x
					if y > maxy or maxy == -1: maxy = y
					if y < miny or miny == -1: miny = y

					pointer_0 = viz.addchild('./Layouts/SharedMedia/Objects/bvmap_pointer.wrl')
					pointer_0.scale(self.scale,self.scale,self.scale)
					pointer_0.disable(viz.LIGHTING)
					pointer_0.curtain(viz.CLOSE)
					pointer_90 = viz.addchild('./Layouts/SharedMedia/Objects/bvmap_pointer.wrl')
					pointer_90.scale(self.scale,self.scale,self.scale)
					pointer_90.disable(viz.LIGHTING)
					pointer_90.curtain(viz.CLOSE)
					pointer_180 = viz.addchild('./Layouts/SharedMedia/Objects/bvmap_pointer.wrl')
					pointer_180.scale(self.scale,self.scale,self.scale)
					pointer_180.disable(viz.LIGHTING)
					pointer_180.curtain(viz.CLOSE)
					pointer_270 = viz.addchild('./Layouts/SharedMedia/Objects/bvmap_pointer.wrl')
					pointer_270.scale(self.scale,self.scale,self.scale)
					pointer_270.disable(viz.LIGHTING)
					pointer_270.curtain(viz.CLOSE)

					pointer_0.translate(x*self.scale,self.height+self.scale*0.11,-y*self.scale+self.scale*0.125)
					pointer_90.translate(x*self.scale+self.scale*0.125,self.height+self.scale*0.11,-y*self.scale)
					pointer_180.translate(x*self.scale,self.height+self.scale*0.11,-y*self.scale-self.scale*0.125)
					pointer_270.translate(x*self.scale-self.scale*0.125,self.height+self.scale*0.11,-y*self.scale)
					pointer_0.rotate(180,90,180)
					pointer_90.rotate(180,90,90)
					pointer_180.rotate(180,90,0)
					pointer_270.rotate(180,90,270)
					
					self.pointers.append([(x,y,0),pointer_0])
					self.pointers.append([(x,y,90),pointer_90])
					self.pointers.append([(x,y,180),pointer_180])
					self.pointers.append([(x,y,270),pointer_270])
				
		# find center point (midx,midy)
		minx = minx*self.scale
		maxx = maxx*self.scale
		miny = -miny*self.scale
		maxy = -maxy*self.scale
		midx = (maxx+minx)/2
		midy = (maxy+miny)/2
		
		#find out how far away the farthest point from the center is.
		farthest = max([(midx-minx),(-midy+miny)])
		_yoffset = farthest + self.height + self.scale
		self.clipLevel = {
			"showMap" : (_yoffset - self.height - 1.5, _yoffset - self.height),
			"hideMap" : (_yoffset - self.height-1.6, _yoffset - self.height-1.5)
			}

		# Create a new window in the lower left corner
		self.window = viz.add(viz.WINDOW)
		self.window.position(0, 0.4)
		self.window.size(0.3, 0.4)
		self.window.fov(90,1)

		# Create a new viewpoint and attach it to the window 
		self.view = viz.add(viz.VIEWPOINT)
		self.window.viewpoint(self.view)
		self.view.translate(midx,_yoffset,midy)
		self.view.rotate(1,0,0,90)

		# Hide the window.
		self.window.clip( *self.clipLevel["hideMap"] )

	def updateBeliefVector(self,newVector):
		# newVector is expected to be a list of triples [(x,z,theta)]	
		for point in self.pointers:
			if point[0] in newVector and self.viewmode == "Map_Pointers":
				point[1].curtain(viz.OPEN)
			else:
				point[1].curtain(viz.CLOSE)

	# viewmode is either "NoMap_NoPointers", "Map_NoPointers", or "Map_Pointers",
	#   to select to display only a black square, only the map, or the map and
	#   the belief vector pointers, respectively.	
	def setViewmode(self,viewmode):
		# set the view mode of the map
		self.viewmode=viewmode
		if(self.viewmode == "NoMap_NoPointers"):
			self.window.clip( *self.clipLevel["hideMap"] )
		else:
			self.window.clip( *self.clipLevel["showMap"] )

	def enableWindow(self, enabled = True):
		if( enabled ):
			self.window.visible(viz.ON)
		else:
			self.window.visible(viz.OFF)

	def setTargetPosition(self,x,y,flag):
		self.targetpointer.translate(x*self.scale,self.height+self.scale*0.11,-y*self.scale)
		if (flag):
			self.targetpointer.curtain(viz.OPEN)
		else:
			self.targetpointer.curtain(viz.CLOSE)
			
	def showTargetPosition(self,flag):
		if (flag):
			self.targetpointer.curtain(viz.OPEN)
		else:
			self.targetpointer.curtain(viz.CLOSE)
			
class __UpdateBeliefVector:
	def __init__(self,filename,initialState):
		(_w,_h,_s) = Navigator.getPlatDim(filename)
		self.MyPlat= Navigator.PLAT(_w,_h,_s)
		self.MyPlat.ReadTextImage(filename)
		self.MyPlat.ComputeAllViews(100)
		self.PossiblePositions=[]
		#-------------------------------------------------
		# BJS 6/5/2002
		# Compute all of the possible positions in the environment.
		# Place all possible positions in the array PossiblePositions
		#-------------------------------------------------
		for position in self.MyPlat.ChosenList:
			for vCount in range(4):
				self.PossiblePositions.append((position[0],position[1],vCount))
		#-------------------------------------------------
		# Set the current state.
		# Convert from actual coordinates and angle.
		#-------------------------------------------------
		(x,y,t) = initialState
		if (t > -10 or t > 350) and t < 10: pos = (x,y,1)
		elif t > 80 and t < 100: pos = (x,y,2)
		elif t > 170 and t < 190: pos = (x,y,3)
		else: pos = (x,y,0)
		self.CurrState=pos
		#-------------------------------------------------
		# BJS 6/5/2002
		# Compute the view at the current state (CurrState)
		#-------------------------------------------------
		self.currView=self.MyPlat.Nodes[self.CurrState[0]][self.CurrState[1]].View[self.CurrState[2]]
		#-------------------------------------------------
		# BJS 6/5/2002
		# Find the states in the set of possible states that are
		# consistent with the current view.
		#-------------------------------------------------
		self.PossiblePositions=self.MyPlat.FindView(self.currView,self.PossiblePositions[:])
		#print 'CurrView=',self.currView
		#print 'PossiblePosition=%s' % self.PossiblePositions

	def updateBeliefVector(self,currResp):
		#-------------------------------------------------
		# BJS 6/5/2002
		# Convert the subject's keyboard response into
		# the movement response in the ANTIE program.
		#-------------------------------------------------
		if currResp==8:
			currResp=2
		elif currResp==4:
			currResp=0
		elif currResp==6:
			currResp=1
		else:
			print '***ERROR*** Invalid "currResp" in call to updateBeliefVector'
			
		#-------------------------------------------------
		# BJS 6/5/2002
		# Update the current state (CurrState) based upon
		# the subjects response.
		#-------------------------------------------------
		self.CurrState=self.MyPlat.MakeState(self.CurrState,currResp)
		#-------------------------------------------------
		# BJS 6/5/2002
		# Update the view (currView) based on the new current
		# state (CurrState)
		#-------------------------------------------------
		self.currView=self.MyPlat.Nodes[self.CurrState[0]][self.CurrState[1]].View[self.CurrState[2]]
		NewPossiblePos=[]
		#-------------------------------------------------
		# BJS 6/5/2002
		# Generate a new vector of possible positions (NewPossiblePos)
		# in which all of the states in the vector are updated based
		# on the subject's response.
		#-------------------------------------------------
		for otherPos in self.PossiblePositions:
			NewPossiblePos.append(self.MyPlat.MakeState([otherPos[0],otherPos[1],otherPos[2]],currResp))
		#-------------------------------------------------
		# BJS 6/5/2002
		# Set PossiblePositions to the NewPossible positions that
		# are consistent with the current view.
		#-------------------------------------------------	
		self.PossiblePositions=self.MyPlat.FindView(self.currView,NewPossiblePos[:])
		#print 'CurrView=',self.currView
		#print 'PossiblePosition=%s' % self.PossiblePositions

	# returns the belief vector in actual coordinates and angle		
	def getBeliefVector(self):
		beliefVec = []
		for (x,y,t) in self.PossiblePositions:
			if t == 0: angle = 270
			elif t==1: angle = 0
			elif t==2: angle = 90
			elif t==3: angle = 180
			beliefVec.append((x,y,angle))
		return beliefVec

#####################################################################################

__BELIEF_VECTOR_MAP = None
__BELIEF_VECTOR = None
__FILENAME = None

NO_MAP = "NoMap_NoPointers"
MAP_NO_POINTERS = "Map_NoPointers"
MAP_POINTERS = "Map_Pointers"
MOVE_FORWARD = 8
TURN_LEFT = 4
TURN_RIGHT = 6

# Display the map on the screen, and set the map's view (can be NO_MAP, MAP_NO_POINTERS, or MAP_POINTERS)
def Init(filename,viewmode=NO_MAP,width=1.0,height=1.0,length=3.0):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	__FILENAME = filename
	__BELIEF_VECTOR_MAP = __BeliefVectorMap(filename,width,height,length)
	__BELIEF_VECTOR_MAP.setViewmode(viewmode)
	__BELIEF_VECTOR = None

# if flag==1 display the target position on the map, else hide the target position
# x, y are PLAT coordinates
def SetTargetPosition(x,y,show=1):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None:
		raise "\n\nError in BeliefVector.SetTargetPosition:\n\tMust call BeliefVector.Init before using this function.\n"
	__BELIEF_VECTOR_MAP.setTargetPosition(x,y,show)

# if flag==1 display the target position on the map, else hide the target position
def ShowTargetPosition(show=1):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None:
		raise "\n\nError in BeliefVector.SetTargetPosition:\n\tMust call BeliefVector.Init before using this function.\n"
	__BELIEF_VECTOR_MAP.showTargetPosition(show)

# Set the subject's starting position (x, y are PLAT coordinates)
def SetState(x,y,angle):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None:
		raise "\n\nError in BeliefVector.SetState:\n\tMust call BeliefVector.Init before using this function.\n"
	__BELIEF_VECTOR = __UpdateBeliefVector(__FILENAME,(x,y,angle))
	__BELIEF_VECTOR_MAP.updateBeliefVector(__BELIEF_VECTOR.getBeliefVector())

# Update the belief vector based on action (can be MOVE_FORWARD, TURN_LEFT, or TURN_RIGHT)
def UpdateBeliefVector(action):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None or __BELIEF_VECTOR==None:
		raise "\n\nError in BeliefVector.UpdateBeliefVector:\n\tMust call BeliefVector.Init and BeliefVector.SetState before using this function.\n"
	__BELIEF_VECTOR.updateBeliefVector(action)
	__BELIEF_VECTOR_MAP.updateBeliefVector(__BELIEF_VECTOR.getBeliefVector())

# Return the belief vector
def GetBeliefVector():
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None or __BELIEF_VECTOR==None:
		raise "\n\nError in BeliefVector.GetBeliefVector:\n\tMust call BeliefVector.Init and BeliefVector.SetState before using this function.\n"
	return __BELIEF_VECTOR.getBeliefVector()
	
# Return the belief vector
def SetBeliefVector(states):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None or __BELIEF_VECTOR==None:
		raise "\n\nError in BeliefVector.SetBeliefVector:\n\tMust call BeliefVector.Init and BeliefVector.SetState before using this function.\n"
	__BELIEF_VECTOR.PossiblePositions=[]
	for (x,y,angle) in states:
		if angle==0: __BELIEF_VECTOR.PossiblePositions.append((x,y,1))
		elif angle==90: __BELIEF_VECTOR.PossiblePositions.append((x,y,2))
		elif angle==180: __BELIEF_VECTOR.PossiblePositions.append((x,y,3))
		else: __BELIEF_VECTOR.PossiblePositions.append((x,y,0))		
	__BELIEF_VECTOR_MAP.updateBeliefVector(__BELIEF_VECTOR.getBeliefVector())

# set the map's view (can be NO_MAP, MAP_NO_POINTERS, or MAP_POINTERS)
def SetViewMode(viewmode):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None or __BELIEF_VECTOR==None:
		raise "\n\nError in BeliefVector.SetViewMode:\n\tMust call BeliefVector.Init and BeliefVector.SetState before using this function.\n"
	__BELIEF_VECTOR_MAP.setViewmode(viewmode)
	__BELIEF_VECTOR_MAP.updateBeliefVector(__BELIEF_VECTOR.getBeliefVector())

# show/hide the window in which the map is displayed.
def enableWindow(enabled = True):
	global __BELIEF_VECTOR_MAP, __BELIEF_VECTOR, __FILENAME
	if __BELIEF_VECTOR_MAP==None or __BELIEF_VECTOR==None:
		raise "\n\nError in BeliefVector.SetViewMode:\n\tMust call BeliefVector.Init and BeliefVector.SetState before using this function.\n"
	__BELIEF_VECTOR_MAP.enableWindow(enabled)

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.1.1.1 $')
	if m:
		return m.group(1)
	else:
		return None    
