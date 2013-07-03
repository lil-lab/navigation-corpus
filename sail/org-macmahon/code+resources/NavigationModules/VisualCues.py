# VisualCues.py
# $Revision: 1.1.1.1 $
# $Date: 2005/09/01 19:41:34 $


# This file includes:
#   class VisualCue to handle cues
#   class VisualCueList to hold a list of cues

import viz,math,random
from string import atof, upper

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.1.1.1 $')
	if m:
		return m.group(1)
	else:
		return None

class VisualCue:
	def __init__(self,x,y,z,theta,shape,texture,curtext,view_prob,time_mean,time_stdv):
		self.X = x      # x, y, z coordinates of cue
		self.Y = y
		self.Z = z
		self.InView = 1     #inView is 1 if cue is currently in view area, 0 otherwise
		if upper(texture) !='NONE':
			self.Texture = viz.addtexture(texture)             # texture of visible cue
		else:
			self.Texture = None
		if upper(curtext) != 'NONE':
			self.CurtainTexture = viz.addtexture(curtext)      # texture of non-visible cue
		else:
			self.CurtainTexture= None
		self.View_prob = view_prob                          # probability of cue being visible
		self.Time_mean = time_mean                          # mean time (in moves) to switch
		self.Time_stdv = time_stdv                          # standard deviation of time (in moves) to switch
		if(time_mean>0):
			self.Move_cnt = random.randint(0,self.Time_mean)    # number of moves since last switch (initialize with random)
		else: self.Move_cnt = 0
		self.IsCurtained = 0                                # object is currently "curtained"
		self.View_angle = 35.0      # view area is +/- 35 degrees from center
		self.Object = viz.addchild(shape)      # the cue's shape
		self.Object.disable(viz.LIGHTING)
		self.Object.curtain(viz.CLOSE)
		self.Object.rotate(0,1,0,theta)
		self.Object.translate(self.X,self.Y,self.Z)        
		r = random.random()
		if r < self.View_prob:      #initialize textures (for cues in view area)
			if self.Texture:
				self.Object.texture(self.Texture,'ROOT')    # 'ROOT' must be defined in .wrl file to be valid
			self.IsCurtained = 0
		else:
			if self.CurtainTexture:
				self.Object.texture(self.CurtainTexture,'ROOT')
			self.IsCurtained = 1
		self.Object.appearance(viz.MODULATE)
		self.setCurtain()   # update inView, and set texture accordingly

	def showCue(self,flag=1):
		if flag:
			self.Object.curtain(viz.OPEN)
		else:
			self.Object.curtain(viz.CLOSE)
			
	def curtainCue(self,flag=1):
		if flag:
			if self.CurtainTexture:
				self.Object.texture(self.CurtainTexture,'ROOT')
			self.IsCurtained = 1
		else:
			if self.Texture:
				self.Object.texture(self.Texture,'ROOT')
			self.IsCurtained = 0

	def setCurtain(self,_x=0,_z=0,_t=0):
		pos = [_x,0,_z] #viz.get(viz.HEAD_POS)
		ori = [_t]      #viz.get(viz.HEAD_ORI)

		self.Move_cnt = self.Move_cnt + 1		

		# check to see if cue is in view now...		
		angle = self.criticalAngle(pos)
		inViewRange = ((abs(ori[0] - angle) < self.View_angle)
				 or (ori[0]<0 and abs((ori[0]+360) - angle) < self.View_angle)
				 or (angle <0 and abs(ori[0] - (angle+360)) < self.View_angle))

		if self.Time_mean <= 0:	 #if curtain based on view_prob
			if inViewRange and not self.InView:  #if currently inView, but not inView before...
				#print "Coming into view..."+' ('+`self.X`+','+`self.Z`+')'
				self.InView = 1
			elif not inViewRange and self.InView:  #if not inView now, but was inView before...
				self.InView = 0
				r = random.random()
				#print "Leaving view... Random number:" , r,' ('+`self.X`+','+`self.Z`+')'
				if r < self.View_prob:
					if self.Texture:
						self.Object.texture(self.Texture,'ROOT')
					self.IsCurtained = 0
				else:
					if self.CurtainTexture:
						self.Object.texture(self.CurtainTexture,'ROOT')
					self.IsCurtained = 1
				self.Object.appearance(viz.MODULATE)

		elif not inViewRange:      #if curtain based on time (moves), and not inViewRange
			r = random.gauss(self.Time_mean,self.Time_stdv)
			if(self.Move_cnt >= r):
				self.Move_cnt = 0
				if self.IsCurtained:
					if self.Texture:
						self.Object.texture(self.Texture,'ROOT')
					self.IsCurtained = 0
				else:
					if self.CurtainTexture:
						self.Object.texture(self.CurtainTexture,'ROOT')
					self.IsCurtained = 1
				self.Object.appearance(viz.MODULATE)
				
				
	def criticalAngle(self,head_pos):
		#this method calculates what angle the viewer must be facing to see the cue
		
		# calculate view position relative to cue position
		x = head_pos[0]-self.X
		z = head_pos[2]-self.Z
		
		if (z == 0): theta = 90
		else: theta = abs(math.atan(x/z)*57.295779513082323)

		if(x>0):
			if(z>0): return -(180-theta)
			else:	return -theta
		elif(x<0):
			if(z>0): return 180-theta
			else:	return theta
		else:
			if(z>0): return 180
			else:	return 0

class VisualCueList:
	def __init__(self):
		self.CueList = []
	def updateCues(self):
		(x,y,z) = viz.get(viz.HEAD_POS)
		t = viz.get(viz.HEAD_ORI)[0]
		for cue in self.CueList:
			cue.setCurtain(x,z,t)
	def readInCues(self,filename):
		# input format: "x y z theta wrl texture curtext prob time_mean time_stdv" (all on one line, separated by spaces)
		#      -"x", "y", "z" are the x, y, and z coordinates of the object
		#      -"theta" is initial rotation around the y-axis of the object
		#      -"wrl" is .wrl file that describes object's shape
		#      -"texture" is texture of object when visible
		#      -"curtext" is texture when not visible
		#      -"prob" is probability of object being visible (if using time, then prob is only used to initialize cues)
		#      -"time_mean" is mean number of moves before object switches (set to -1 if using prob)
		#      -"time_stdv" is standard deviation of moves before switch
		
		file = open(filename,'r')
		lines = file.readlines()
		for l in lines:
			try:
				line = l.split('|')
				cue = VisualCue(atof(line[0]),atof(line[1]),atof(line[2]),atof(line[3]),line[4],line[5],line[6],atof(line[7]),atof(line[8]),atof(line[9]))
				self.CueList.append(cue)
			except:
				print "Error reading line:",l
		file.close()
		self.showAllCues(1)
	def showAllCues(self,show=1):
		if(show):
			for cue in self.CueList:
				cue.Object.curtain(viz.OPEN)
		else:
			for cue in self.CueList:
				cue.Object.curtain(viz.CLOSE)
	# get all cues in the rectangle formed by x1,z1,x2,z2 (all viz coordinates)
	def getCues(self,x1,z1,x2,z2):
		xmin = min([x1,x2])
		xmax = max([x1,x2])
		zmin = min([z1,z2])
		zmax = max([z1,z2])
		list = []
		for cue in self.CueList:
			if(cue.X > xmin and cue.X < xmax)and(cue.Z > zmin and cue.Z < zmax):
				list.append(cue)
		return list