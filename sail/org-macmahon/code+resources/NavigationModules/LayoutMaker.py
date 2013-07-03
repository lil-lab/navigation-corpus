# LayoutMaker
# $Revision: 1.1.1.1 $
# $Date: 2005/09/01 19:41:34 $

from Tkinter import *
import tkFileDialog
import tkSimpleDialog
import tkMessageBox
from Navigator import *
import random,string,pickle, os, copy
from math import *

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.1.1.1 $')
	if m:
		return m.group(1)
	else:
		return None

class LayoutMaker:
	def __init__(self,master):
		# set up the dialog box
		master.title("Layout Generator")
		self.master = master

		# frame 1 contains filename, plat dimensions, and import/export options		
		f1 = Frame(master,bd=3, relief=GROOVE)
		f1.grid(row=0,column=0,padx=5,pady=5,sticky=W)
		Label(f1, text=" File Name").grid(row=0,sticky=W)
		Label(f1, text=" Plat Height").grid(row=1,sticky=W)
		Label(f1, text=" Plat Width").grid(row=2,sticky=W)
		Label(f1, text=" Plat Size").grid(row=3,sticky=W)
		# position the buttons
		Button(f1,text="Generate Layout",command = self.GenerateLayout).grid(row=4,column=0,padx=5,pady=3,sticky=W)
		Button(f1,text="Import Layout",command = self.BrowseFilenames).grid(row=4,column=1,padx=5,pady=3)
		Button(f1,text="Export Layout",command = self.ExportLayout).grid(row=4,column=2,padx=5,pady=3,sticky=E)
		Button(f1,text="Save",command = self.Save).grid(row=0,column=2,padx=5,pady=3,sticky=W)
		Button(f1,text="Load",command = self.Load).grid(row=0,column=2,padx=5,pady=3,sticky=E)
		self.e_filename = Entry(f1) # entry field for layout filename
		self.e_platheight = Entry(f1,width=5) # entry field for PLAT height
		self.e_platwidth =  Entry(f1,width=5) # entry field for PLAT width
		self.e_platsize  =  Entry(f1,width=5) # entry field for PLAT size
		self.e_filename.grid(row=0,column=0,columnspan=2,sticky=E) #position entry boxes on dialog
		self.e_platheight.grid(row=1, column=0,sticky=E)
		self.e_platwidth.grid(row=2, column=0,sticky=E)
		self.e_platsize.grid(row=3, column=0,sticky=E)
		self.e_filename.insert(0,"NewLayout") # set initial values in entry boxes
		self.e_platheight.insert(0,"25")
		self.e_platwidth.insert(0,"25")
		self.e_platsize.insert(0,"40")

		# frame 2 (inside frame 1) - scaling stuff
		f2 = Frame(f1, bd=3, relief=GROOVE)
		f2.grid(row=1,column=1,columnspan=3,rowspan=3,pady=2)
		Button(f2,text='Change Scale',command=self.ChangeScale).grid(row=1,column=1,columnspan=2,pady=2)
		self.l_scalewidth = Label(f2,text= 'width:  1.00'); self.l_scalewidth.grid(row=2,column=1,sticky=W,padx=3)
		self.l_scaleheight = Label(f2,text='height: 1.00'); self.l_scaleheight.grid(row=3,column=1,sticky=W,padx=3)
		self.l_scalelength = Label(f2,text='length: 3.00'); self.l_scalelength.grid(row=2,column=2,sticky=W,padx=3)
		self.l_scalethick = Label(f2,text= 'thick:  0.050');self.l_scalethick.grid(row=3,column=2,sticky=W,padx=3)		   

		# buttons and options outside of frame 1
		f4 = Frame(master); f4.grid(row=0,column=1,sticky=NW)
		self.delbutton = Button(f4,text="Delete",command = self.DeleteStructure,state=DISABLED)
		self.delbutton.grid(row=4,column=3,padx=5,pady=3,sticky=NW)
		self.checkbuttonvalue = IntVar() # variable that stores the value of the checkbutton state
		self.checkbutton = Checkbutton(f4,text="Show Visual Cues",var=self.checkbuttonvalue,command=self.ClickCheckbutton)
		self.checkbutton.grid(row=4,column=1,sticky=W)
		self.checkbutton.select()
		Button(f4,text="Distribute Cues",width=15,command = self.AddVisualCues).grid(row=2,column=1,padx=5,pady=3,sticky=SW)
		Button(f4,text="Remove All Cues",width=15,command = self.RemoveCues).grid(row=3,column=1,padx=5,pady=3,sticky=SW)
		Button(f4,text="Wall Textures",command = self.ChangeWallTextures).grid(row=0,column=1,padx=5,pady=3,sticky=NW)
		Label(f4).grid(row=1,column=1)
		self.coordlabel = Label(f4,text="x: 0, y: 0")
		self.coordlabel.grid(row=0,column=3,sticky=NE)
		self.cuetypes=[] # contains data about the kind of cues in the cue quick list
		self.cuelist=[] # list of cues distributed in the layout
		self.numcues=0 # number of cues distributed in the layout
		self.cueratios=[] # distribution ratios of different cues
		self.flooroffsets=[] # x,y,z,theta floor offsets for cue distribution
		self.halloffsets=[] # x,y,z,theta hall offsets for cue distribution
		self.walloffsets=[] # x,y,z,theta wall offsets for cue distribution

		# frame 3 - the canvas		  
		f3 = Frame(master, bd=3, relief=GROOVE)
		f3.grid(row=2,column=0,columnspan=3,padx=5,pady=5)
		self.canvas = Canvas(f3,width=600,height=600,background="Black")
		self.canvas.grid(row=0)
		self.canvas.bind("<Button-1>",self.CanvasClickCallback)		 # bind mouse events to the canvas
		self.canvas.bind("<Button-3>",self.CanvasRightClickCallback)
		self.canvas.bind("<Double-Button-1>",self.CanvasDblClickCallback)
		self.canvas.bind("<Motion>",self.CanvasMotionCallback)
		self.canvas.bind("<B1-Motion>",self.CanvasB1MotionCallback)
		self.canvas.bind("<ButtonRelease-1>",self.CanvasB1ReleaseCallback)
		self.master.bind("<Delete>",self.DeleteStructure)
		self.platObject = 0 # plat object storing the information about the layout structure
		self.makewallfrom = None # when drawing a new wall, points to canvas item where wall will start from
		self.makewallto = None   # points to item that new wall will be connected to.
		self.startpos = None # starting position
		self.PlatScale = 4.0 # distance of 1 plat unit == self.PlatScale vrut units == self.scalewidth + self.scalelength
		self.scaleheight = 1.0 # distance from ceiling to floor (meters)
		self.scalewidth = 1.0 # width of a node (meters)
		self.scalelength = 3.0 # length of a corridor (meters)
		self.scalethick = 0.05 # thickness of the walls (meter)
		# hallway, wall, floor, and ceiling textures:
		self.textures = ["./SharedMedia/Textures/cement1.jpg","./SharedMedia/Textures/cement1.jpg","./SharedMedia/Textures/burlap.jpg","./SharedMedia/Textures/cement1.jpg"]
		self.GenerateLayout() # generate initial layout

	# called when save button is pressed. Save layout information to a *.lyt file for later modifications		
	def Save(self):
		filename = tkFileDialog.asksaveasfilename(initialfile=self.e_filename.get()+'.lyt',filetypes=[("Layout",'*.lyt'),("All files",'*.*')])
		if filename: # filename will be None if browse was canceled
			# collect hotspot information
			hotspots = self.GetHotSpotList()
			file = open(filename,'w')
			# save essential layout information in object, then pickle object to a file
			# (make sure order of members in object are consistent with order in Load function (below)) 
			object = (self.platObject,self.cuelist,self.cuetypes,self.cueratios,self.flooroffsets,self.halloffsets,self.walloffsets,hotspots,self.startpos,self.scalewidth,self.scaleheight,self.scalelength,self.scalethick,self.textures)
			pickle.dump(object,file)
			file.close()
			fname = string.strip(filename)       # display saved filename in entry box
			if string.upper(fname[-4:])=='.LYT':
				fname = fname[:-4]
			self.e_filename.delete(0,END)
			self.e_filename.insert(0,fname)
			tkMessageBox.showinfo("Saved Layout File","Layout saved to:\n\n%s" % filename)
			
	# load layout from a .lyt file
	def Load(self):
		filename = tkFileDialog.askopenfilename(filetypes=[("Layout",'*.lyt'),("All files",'*.*')])
		if filename:
			try:
				file = open(filename,'r')
				# extract data from object
				object = pickle.load(file)
				self.platObject=object[0]
				self.cuelist=object[1]
				self.cuetypes=object[2]
				self.cueratios=object[3]
				self.flooroffsets=object[4]
				self.halloffsets=object[5]
				self.walloffsets=object[6]
				hotspots=object[7]
				if len(object) > 8:
					self.startpos = object[8]
				else:
					self.startpos = None
				if len(object)>12:
					self.scalewidth=object[9]
					self.scaleheight=object[10]
					self.scalelength=object[11]
					self.scalethick=object[12]
				else:
					self.scalewidth=1.0
					self.scaleheight=1.0
					self.scalelength=3.0
					self.scalethick=0.05
				if len(object)>13:
					self.textures=object[13]
				else:
					self.textures = ["./SharedMedia/Textures/cement1.jpg","./SharedMedia/Textures/cement1.jpg","./SharedMedia/Textures/burlap.jpg","./SharedMedia/Textures/cement1.jpg"]
				self.PlatScale = self.scalewidth + self.scalelength
				self.l_scaleheight.config(text='height: %.2f'%self.scaleheight)
				self.l_scalewidth.config(text= 'width:  %.2f'%self.scalewidth)
				self.l_scalelength.config(text='length: %.2f'%self.scalelength)
				self.l_scalethick.config(text= 'thick:  %.3f'%self.scalethick)
				
				file.close()
				# set filename and PLAT dimensions
				_w = self.platObject.x
				_h = self.platObject.y
				_s = self.platObject.Length
				fname = string.strip(filename)
				if string.upper(fname[-4:])=='.LYT':
					fname = fname[:-4]
				self.e_filename.delete(0,END)
				self.e_filename.insert(0,fname)
				self.e_platheight.delete(0,END)
				self.e_platheight.insert(0,_h)
				self.e_platwidth.delete(0,END)
				self.e_platwidth.insert(0,_w)
				self.e_platsize.delete(0,END)
				self.e_platsize.insert(0,_s)
				self.DisplayTextMap() # display the layout in the canvas
				# re-distribute the cues
				self.numcues = 0
				for (cue,x,y,z,t) in self.cuelist:
					_x=self.xoffset+(x/self.PlatScale)*self.scale # convert from VRUT to canvas coordinates
					_z=self.yoffset+(z/self.PlatScale)*self.scale
					_t = t*pi/180 # convert from degrees to radians
					size = self.scale/10.0 # size of cue markers is proportional to the size of the layout nodes
					x1 = _x+size*cos(_t)  # calculate the vertices for the cue marker
					y1 = _z+size*sin(_t)
					x2 = _x+size*cos(_t+(2*pi/3))
					y2 = _z+size*sin(_t+(2*pi/3))
					x3 = _x
					y3 = _z
					x4 = _x+size*cos(_t+(4*pi/3))
					y4 = _z+size*sin(_t+(4*pi/3))
					if len(cue)<8: cue.append("green") # default color of cue marker is green (for backwards compatibility)
					self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,x4,y4,fill=cue[7],outline=cue[7],tags=("cue",self.numcues)) # draw the cue on the canvas
					self.numcues = self.numcues+1
				for (num,coords,poswav,gotowav) in hotspots: # show all of the hotspots
					canvascoords = self.PlatToCanvas(coords[0],coords[1]) # convert to canvas coords
					self.canvas.create_text(canvascoords[0],canvascoords[1],text=num,fill="white",tags=(("hotspot"),("num",num),("poswav "+poswav),("gotowav "+gotowav),("coords",coords[0],coords[1]))) # display hotspot marker on canvas
				# display starting position
				if self.startpos:
					_x=self.xoffset+self.startpos[0]*self.scale  # get canvas coords
					_z=self.yoffset+self.startpos[1]*self.scale
					_t = (self.startpos[2]-90.0)*pi/180.0 # convert from degrees to radians
					size = self.width
					x1 = _x+size*cos(_t)   # calculate vertices for the cue marker
					y1 = _z+size*sin(_t)
					x2 = _x+size*cos(_t+(2.0*pi/3.0))
					y2 = _z+size*sin(_t+(2.0*pi/3.0))
					x3 = _x+size*cos(_t+(4.0*pi/3.0))
					y3 = _z+size*sin(_t+(4.0*pi/3.0))
					self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,fill='',width=2,outline='light green',tags="start_pos")			   
			except:
				# error occurred while loading file; restore defaults and show warning
				self.canvas.delete(ALL)
				self.platObject = 0
				self.cuelist=[]
				self.cuetypes=[]
				self.cueratios=[]
				self.flooroffsets=[]
				self.halloffsets=[]
				self.walloffsets=[]
				self.e_filename.delete(0,END)
				self.e_filename.insert(0,"NewLayout")				
				tkMessageBox.showwarning("Invalid Layout File","An error occurred while trying to load this layout file:\n\n%s" % filename)

	# export layout to various files used for VRUT experiments                
	def ExportLayout(self):
		if(self.platObject==0): return
		d=ExportDialog(self.master,self.e_filename.get()) # show dialog to select what to export
		if not d.result: return # return if cancelled
		filename   = d.filename
		self.e_filename.delete(0,END)           # display filename in entry box
		self.e_filename.insert(END,filename)
		if d.map.get(): # export text map
			FILEHANDLE = open(filename+'.txt','w')
			self.platObject.DisplayTextImage(FILEHANDLE)
			FILEHANDLE.close()
		if d.wrl.get(): # export .wrl file
			VRMLFILE=open(filename+'.wrl','w')
			self.platObject.DisplayVRMLLayout(VRMLFILE,self.scalewidth,self.scaleheight,self.scalelength,self.scalethick,self.textures[0],self.textures[1],self.textures[2],self.textures[3])
			VRMLFILE.close()
		if d.obj.get(): # export cue objects file
			OBJFILE=open(filename+'.obj','w')
			for item in self.cuelist:
				cue = item[0]
				OBJFILE.write("%f|%f|%f|%f|%s|%s|%s|%f|%f|%f\n"%(item[1],item[2],-item[3],item[4],cue[1],cue[2],cue[3],cue[4],cue[5],cue[6]))
			OBJFILE.close()
		if d.poi.get(): # export points of interest (hotspots)
			POIFILE=open(filename+'.poi','w')         
			hotspots = self.GetHotSpotList()
			for (num,coords,poswav,gotowav) in hotspots:
				POIFILE.write("%i|%i|%s|%s\n"%(coords[0],coords[1],poswav,gotowav))
			POIFILE.close()
		if d.run.get(): # output run file
			RUNFILE=open(filename+'.run','w')
			for (x,y) in self.platObject.ChosenList:
				for angle in [0,90,180,270]:
					RUNFILE.write("%i %i %i\n"%(x,y,angle))
			RUNFILE.close()
		if d.startpos.get(): # output run file
			POSFILE=open(filename+'.pos','w')
			if self.startpos:
				POSFILE.write("%i %i %i\n"%self.startpos)
			else:
				POSFILE.write("0 0 0\n")
			POSFILE.close()
		tkMessageBox.showinfo("Files Exported","Files exported to:\n\n%s" % filename)

	# randomly generate a new layout structure	
	def GenerateLayout(self):
		self.CanvasRightClickCallback(None)
		platheight = int(self.e_platheight.get()) # get PLAT dimensions from entry boxes
		platwidth  = int(self.e_platwidth.get())
		platsize   = int(self.e_platsize.get())
		self.startpos = None
		self.platObject=PLAT(platwidth,platheight,platsize)
		self.platObject.GenerateLayout() # generate a new PLAT
		self.DisplayTextMap()  # display new map in canvas
		self.DistributeCues()  # re-distribute cues

	# import a .txt text map file
	def BrowseFilenames(self):
		filename = tkFileDialog.askopenfilename(filetypes=[("Text Map",'*.txt'),("All files",'*.*')])
		if filename:
			try:
				_w,_h,_s = getPlatDim(filename) # get dimensions of the text map
				self.platObject=PLAT(_w,_h,_s)
				self.platObject.ReadTextImage(filename)
				self.DisplayTextMap() # display text map
				try:
					if string.upper(filename[-4:])==".TXT":
						filename = filename[:-4]
				except:
					pass
				self.e_filename.delete(0,END)
				self.e_filename.insert(0,filename) # display filename and dimensions
				self.e_platheight.delete(0,END)
				self.e_platheight.insert(0,_h)
				self.e_platwidth.delete(0,END)
				self.e_platwidth.insert(0,_w)
				self.e_platsize.delete(0,END)
				self.e_platsize.insert(0,_s)
			except: # error occurred while loading text map
				self.canvas.delete(ALL)
				self.platObject = 0
				self.e_filename.delete(0,END)
				self.e_filename.insert(0,"NewLayout")				
				tkMessageBox.showwarning("Invalid Layout File","An error occurred while trying to load this layout file:\n\n%s" % filename)

	# display the map in the canvas widgit				
	def DisplayTextMap(self):
		if(self.platObject==0): return				
		self.canvas.delete(ALL) # clear previous contents of canvas

		# get max and min PLAT coords of map, to center it in the canvas
		maxx = -1
		maxy = -1
		minx = -1
		miny = -1		
		for y in range(self.platObject.y):
			for x in range(self.platObject.x):
				if (x,y) in self.platObject.ChosenList:
					if x > maxx or maxx == -1: maxx = x
					if x < minx or minx == -1: minx = x
					if y > maxy or maxy == -1: maxy = y
					if y < miny or miny == -1: miny = y
		midx = (maxx+minx)/2.0 # PLAT midpoint
		midy = (maxy+miny)/2.0 # PLAT midpoint
		farthest = max([(midx-minx),(midy-miny)]) # max-radius of map
		self.scale = scale = 200/farthest # distance in pixels between center of two nodes
		self.width = width=scale/(self.PlatScale/self.scalewidth) #4 # size of a node in pixels
		xoffset = 300-midx*scale-width/2.0 # offset used to center the map
		yoffset = 300-midy*scale-width/2.0 # offset + PLAT coord * scale will give the upper left corner (in canvas coords) of the node at PLAT coord
		self.xoffset = xoffset+self.width/2 # these offsets are used to offset to the middle of the node,
		self.yoffset = yoffset+self.width/2 #    rather than to the upper left corner
		for y in range(self.platObject.y):
			for x in range(self.platObject.x):
				if (x,y) in self.platObject.ChosenList:
					# a floor
					self.canvas.create_rectangle(xoffset+x*scale,yoffset+y*scale,xoffset+x*scale+width,yoffset+y*scale+width,fill="black",outline="red",tags=("floor",('coords',x,y)))
					if (x+1,y) in self.platObject.Nodes[x][y].Linked or ((x+1<self.platObject.x) and (x,y) in self.platObject.Nodes[x+1][y].Linked):
						# a horizontal hallway
						self.canvas.create_rectangle(xoffset+x*scale+width+1,yoffset+y*scale,xoffset+(x+1)*scale-1,yoffset+y*scale+width,fill="red",outline="red",tags=("hallway_h",('coords',x,y,x+1,y)))
					if (x,y+1) in self.platObject.Nodes[x][y].Linked or ((y+1<self.platObject.y) and (x,y) in self.platObject.Nodes[x][y+1].Linked):
						# a vertical hallway
						self.canvas.create_rectangle(xoffset+x*scale,yoffset+y*scale+width+1,xoffset+x*scale+width,yoffset+(y+1)*scale-1,fill="red",outline="red",tags=("hallway_v",('coords',x,y,x,y+1)))
						
		self.canvas.tag_bind("floor","<Button-3>",self.FloorRightClkCallback) # bind events to the objects
		self.canvas.tag_bind("floor","<Button-1>",self.FloorCallback)
		self.canvas.tag_bind("hallway_h","<Button-3>",self.H_WallRightClkCallback)
		self.canvas.tag_bind("hallway_h","<Button-1>",self.H_WallCallback)
		self.canvas.tag_bind("hallway_v","<Button-3>",self.V_WallRightClkCallback)
		self.canvas.tag_bind("hallway_v","<Button-1>",self.V_WallCallback)
		if self.startpos: # draw the starting position marker if it exists
			_x=self.xoffset+self.startpos[0]*self.scale  # get canvas coords
			_z=self.yoffset+self.startpos[1]*self.scale
			_t = (self.startpos[2]-90.0)*pi/180.0 # convert from degrees to radians
			size = self.width
			x1 = _x+size*cos(_t)   # calculate vertices for the cue marker
			y1 = _z+size*sin(_t)
			x2 = _x+size*cos(_t+(2.0*pi/3.0))
			y2 = _z+size*sin(_t+(2.0*pi/3.0))
			x3 = _x+size*cos(_t+(4.0*pi/3.0))
			y3 = _z+size*sin(_t+(4.0*pi/3.0))
			self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,fill='',width=2,outline='light green',tags="start_pos")   

	# the 'Show visual cues' button was clicked		
	def ClickCheckbutton(self):
		if self.checkbuttonvalue.get():
			self.canvas.lift("cue") # draw cues above other objects
			self.canvas.tag_bind("cue","<Button-1>",self.CueCallBack) # bind cue callback
		else:
			self.canvas.lower("cue") # bring other objects above the cues
			self.canvas.tag_unbind("cue","<Button-1>") # unbind cue callback
			
	# get offsets and ratios to distribute cues
	def AddVisualCues(self):
		d = CueDistributionDialog(self.master,self.cuetypes,self.cueratios,self.flooroffsets,self.halloffsets,self.walloffsets,self.scalewidth,self.scalelength)
		if d.result: # get results from dialog
			self.cueratios=d.cueratios
			self.flooroffsets=d.flooroffs
			self.halloffsets=d.halloffs
			self.walloffsets=d.walloffs
			self.DistributeCues(d.removecues) # distribute the cues

	# remove the cues from the canvas			
	def RemoveCues(self):
		self.canvas.delete("cue")
		self.cuelist = []
		self.numcues = 0

	# randomly pick a cue type based on cue ratios
	def pickCue(self):
		r = random.random()*100.0
		total = 0
		for (res,ratio) in self.cueratios:
			total = total + ratio
			if total >= r:
				return res
		return None

	# display cue marker, and add cue to cuelist	
	def AddCue(self,cue,x,y,z,t):
		if cue==None: return
		self.cuelist.append([cue,x,y,z,t]) # append new cue to list of cues 
		_x=self.xoffset+(x/self.PlatScale)*self.scale  # get canvas coords
		_z=self.yoffset+(z/self.PlatScale)*self.scale
		_t = t*pi/180 # convert from degrees to radians
		size = self.scale/10.0 # cue marker is proportional to the scale of the layout
		x1 = _x+size*cos(_t) # calculate vertices for the cue marker
		y1 = _z+size*sin(_t)
		x2 = _x+size*cos(_t+(2*pi/3))
		y2 = _z+size*sin(_t+(2*pi/3))
		x3 = _x
		y3 = _z
		x4 = _x+size*cos(_t+(4*pi/3))
		y4 = _z+size*sin(_t+(4*pi/3))
		self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,x4,y4,fill=cue[7],outline=cue[7],tags=("cue",self.numcues)) # draw the marker on the canvas
		self.numcues = self.numcues+1

	# distribute cues based on cue ratios and offsets		
	def DistributeCues(self,removecues=1):
		if(self.platObject==0): return
		if removecues:
			self.RemoveCues()
		for y in range(self.platObject.y):
			for x in range(self.platObject.x):
				if (x,y) in self.platObject.ChosenList:
					# the floor
					for offset in self.flooroffsets: #output one cue with each offset in list
						cue = self.pickCue()
						self.AddCue(cue,x*self.PlatScale+offset[0],offset[1],y*self.PlatScale+offset[2],offset[3])
					if (x+1,y) in self.platObject.Nodes[x][y].Linked or ((x+1<self.platObject.x) and (x,y) in self.platObject.Nodes[x+1][y].Linked):
						# a horizontal hallway
						for offset in self.halloffsets: #output one cue with each offset in list
							cue = self.pickCue()
							self.AddCue(cue,x*self.PlatScale+self.PlatScale/2.0+offset[0],offset[1],y*self.PlatScale+offset[2],270+offset[3])
					if (x,y+1) in self.platObject.Nodes[x][y].Linked or ((y+1<self.platObject.y) and (x,y) in self.platObject.Nodes[x][y+1].Linked):
						# a vertical hallway
						for offset in self.halloffsets: #output one cue with each offset in list
							cue = self.pickCue()
							self.AddCue(cue,x*self.PlatScale-offset[2],offset[1],y*self.PlatScale+self.PlatScale/2.0+offset[0],offset[3])
					if (x-1<0) or ((x-1,y) not in self.platObject.Nodes[x][y].Linked and (x,y) not in self.platObject.Nodes[x-1][y].Linked):
						# left wall
						for offset in self.walloffsets: #output one cue with each offset in list
							cue = self.pickCue()
							self.AddCue(cue,x*self.PlatScale-self.scalewidth/2.0+offset[2],offset[1],y*self.PlatScale-offset[0],offset[3])
					if (x+1 >= self.platObject.x) or ((x+1,y) not in self.platObject.Nodes[x][y].Linked and (x,y) not in self.platObject.Nodes[x+1][y].Linked):
						# right wall
						for offset in self.walloffsets: #output one cue with each offset in list
							cue = self.pickCue()
							self.AddCue(cue,x*self.PlatScale+self.scalewidth/2.0-offset[2],offset[1],y*self.PlatScale+offset[0],180+offset[3])
					if (y+1>=self.platObject.y) or ((x,y+1) not in self.platObject.Nodes[x][y].Linked and (x,y) not in self.platObject.Nodes[x][y+1].Linked):
						# bottom wall
						for offset in self.walloffsets: #output one cue with each offset in list
							cue = self.pickCue()
							self.AddCue(cue,x*self.PlatScale-offset[0],offset[1],y*self.PlatScale+self.scalewidth/2.0-offset[2],270+offset[3])
					if (y-1<0) or ((x,y-1) not in self.platObject.Nodes[x][y].Linked and (x,y) not in self.platObject.Nodes[x][y-1].Linked):
						# top wall
						for offset in self.walloffsets: #output one cue with each offset in list
							cue = self.pickCue()
							self.AddCue(cue,x*self.PlatScale+offset[0],offset[1],y*self.PlatScale-self.scalewidth/2.0+offset[2],90+offset[3])
		self.canvas.tag_bind("cue","<Button-1>",self.CueCallBack) # bind callbacks to cues
		self.ClickCheckbutton() # raise or lower cues depending on state of checkbutton

	# delete highlighted halls and floors
	def DeleteStructure(self,event=None):
		if(self.platObject==0): return
		for item in self.canvas.find_withtag('highlight'): # go through each high-lighted item
			tags = self.canvas.gettags(item)
			if "hallway_h" in tags or "hallway_v" in tags: # if item is a hallway
				pts = None
				for tag in tags:
					if string.find(tag,'coords') != -1:
						pts = map(int,tag.split()[1:]) # get the coordinates of the hallway
						break
				if pts:
					# remove links in the PLAT object to remove the hallway
					if (pts[2],pts[3]) in self.platObject.Nodes[pts[0]][pts[1]].Linked:
						self.platObject.Nodes[pts[0]][pts[1]].Linked.remove((pts[2],pts[3]))
					if (pts[0],pts[1]) in self.platObject.Nodes[pts[2]][pts[3]].Linked:
						self.platObject.Nodes[pts[2]][pts[3]].Linked.remove((pts[0],pts[1]))
				self.canvas.delete(item) # delete the hall from the canvas
		for item in self.canvas.find_withtag('floor'):
			# now that links have been removed from the PLAT object,
			#   remove any floors (nodes) that aren't linked to anything.
			#   (By doing the deletion in two steps like this, you make sure that no nodes are an island,
			#    and that no nodes are deleted if they are still linked with other nodes)
			x,y = self.getItemPlatCoords(item)
			if len(self.platObject.Nodes[x][y].Linked) == 0 and (x==0 or (x,y) not in self.platObject.Nodes[x-1][y].Linked) and (y==0 or (x,y) not in self.platObject.Nodes[x][y-1].Linked) and (x==self.platObject.x-1 or (x,y) not in self.platObject.Nodes[x+1][y].Linked) and (y==self.platObject.y-1 or (x,y) not in self.platObject.Nodes[x][y+1].Linked):
				self.platObject.Nodes[x][y].active=0 
				self.platObject.ChosenList.remove((x,y)) # remove node from PLAT chosen list
				self.currentitem = item # remove hotspots in the node
				self.RemoveHotspot()
				self.currentitem = None
				self.canvas.delete(item) # delete the floor from the canvas		 
				
		self.UnHighlight()
		self.delbutton.config(state=DISABLED) # disable the delete button

	# connect self.makewallfrom to self.makewallto with hallways		
	def MakeWall(self):
		if(self.platObject==0): return
		px1,py1 = self.getItemPlatCoords(self.makewallfrom)
		px2,py2 = self.getItemPlatCoords(self.makewallto)
		
		if px1==px2 and py1==py2:	 # just a single point, cancel draw	
			self.CanvasRightClickCallback(None)
			return
		
		xoffset = self.xoffset-self.width/2
		yoffset = self.yoffset-self.width/2
		xlow = min(px1,px2)
		xhi = max(px1,px2)
		ylow = min(py1,py2)
		yhi = max(py1,py2)

		if (xlow,ylow) not in self.platObject.ChosenList: # add points to chosen list if they aren't there already
			self.platObject.ChosenList.append((xlow,ylow))
			self.platObject.Nodes[xlow][ylow].active = 1
		if (xhi,yhi) not in self.platObject.ChosenList:
			self.platObject.ChosenList.append((xhi,yhi))
			self.platObject.Nodes[xhi][yhi].active = 1

		if px1==px2: # draw hallways vertically
			x = px1
			for y in range(ylow,yhi):
				if (x,y) not in self.platObject.ChosenList: # add nodes to chosenlist
					self.platObject.ChosenList.append((x,y))
					self.platObject.Nodes[x][y].active = 1
					self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
				if not ((x,y+1) in self.platObject.Nodes[x][y].Linked or ((y+1<self.platObject.y) and (x,y) in self.platObject.Nodes[x][y+1].Linked)):
					self.platObject.Nodes[x][y].Linked.append((x,y+1)) # add link to nodes
					self.platObject.Nodes[x][y+1].Linked.append((x,y))
					self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale+self.width+1,xoffset+x*self.scale+self.width,yoffset+(y+1)*self.scale-1,fill="red",outline="red",tags=("hallway_v",('coords',x,y,x,y+1)))
		elif py1==py2: # horizontal
			y = py1
			for x in range(xlow,xhi):
				if (x,y) not in self.platObject.ChosenList: # add nodes to chosenlist
					self.platObject.ChosenList.append((x,y))
					self.platObject.Nodes[x][y].active = 1
					self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
				if not ((x+1,y) in self.platObject.Nodes[x][y].Linked or ((x+1<self.platObject.x) and (x,y) in self.platObject.Nodes[x+1][y].Linked)):
					self.platObject.Nodes[x][y].Linked.append((x+1,y)) # add link to nodes
					self.platObject.Nodes[x+1][y].Linked.append((x,y))
					self.canvas.create_rectangle(xoffset+x*self.scale+self.width+1,yoffset+y*self.scale,xoffset+(x+1)*self.scale-1,yoffset+y*self.scale+self.width,fill="red",outline="red",tags=("hallway_h",('coords',x,y,x+1,y)))

	# convert from PLAT coords to canvas coords		
	def PlatToCanvas(self,x,y):
		return ((self.xoffset+x*self.scale),(self.yoffset+y*self.scale))
	
	# convert from canvas coords to PLAT coords
	def canvasToPlat(self,x,y):
		return (int(round((x-self.xoffset)/self.scale)),int(round((y-self.yoffset)/self.scale)))
	
	# return PLAT coords of a canvas item
	def getItemPlatCoords(self,item):
		for tag in self.canvas.gettags(item):
			if string.find(tag,'coords') != -1:
				t = tag.split()
				return (int(t[1]),int(t[2]))
			
	# left mouse button was held down while moved across the canvas
	#   - update select box
	def CanvasB1MotionCallback(self,event):
		items=self.canvas.find_withtag("select-box")
		if len(items) == 0: # create select-box if it doesn't exist yet
			self.UnHighlight()
			self.delbutton.config(state=DISABLED)
			item = self.canvas.create_rectangle(event.x,event.y,event.x,event.y,outline="yellow",tags=("select-box",("coords",event.x,event.y)))
		else: item = items[0]
		
		for tag in self.canvas.gettags(item): # get base coords of the select-box
			if string.find(tag,'coords') != -1:
				break
		t = tag.split()
		x = t[1]
		y = t[2]
		xlow = min(x,event.x)
		xhi = max(x,event.x)
		ylow = min(y,event.y)
		yhi = max(y,event.y)
		self.canvas.coords(item,xlow,ylow,xhi,yhi) # update the select-box

	# left mouse button was released, highlight items in the select-box		
	def CanvasB1ReleaseCallback(self,event):
		items=self.canvas.find_withtag("select-box")
		if len(items)!=0: # if select-box exists
			item = items[0]
			(x1,y1,x2,y2) = self.canvas.coords(item)
			items = self.canvas.find_enclosed(x1, y1, x2, y2) # get all objects enclosed by box
			if len(items)>0:
				self.delbutton.config(state=NORMAL)
				for i in items:
					tags = self.canvas.gettags(i)
					if "floor" in tags or "hallway_h" in tags or "hallway_v" in tags: # highlight enclosed items
						newtags = tags + ('highlight',)
						self.canvas.itemconfig(i,outline="yellow",tags = newtags)
			self.canvas.delete("select-box")

	# cursor moved over canvas, update line if making hallway
	def CanvasMotionCallback(self,event):
		x,y = self.canvasToPlat(event.x,event.y)
		self.coordlabel.config(text="x: %i, y: %i"%(x,y))
		if self.makewallfrom:
			px1,py1 = self.getItemPlatCoords(self.makewallfrom)			
			px2,py2 = self.canvasToPlat(event.x,event.y)
			if px1==px2 or py1==py2:
				line = self.canvas.find_withtag('line')[0]
				x1,y1 = self.PlatToCanvas(px1,py1)
				x2,y2 = self.PlatToCanvas(px2,py2)
				if x2 > 0 and x2 < 600 and y2 > 0 and y2 < 600:
					self.canvas.coords(line,x1,y1,x2,y2)

	# canvas was clicked with the left mouse button, draw hallway if making hallway					
	def CanvasClickCallback(self,event):
		if(self.platObject==0): return
		if self.makewallfrom:
			line = self.canvas.find_withtag('line')[0]
			(x0,y0,x1,y1) = self.canvas.coords(line)
			x,y = self.canvasToPlat(x1,y1)
			
			####### temporary fix ##########
			# make sure wall won't be drawn out of PLAT bounds
			if x<0 or y<0 or x>=self.platObject.x or y>= self.platObject.y:
				tkMessageBox.showwarning("ERROR","Out of Range",parent=self.master)
				self.CanvasRightClickCallback(None)
				return
			################################
			
			self.canvas.delete('line')
			xoffset = self.xoffset-self.width/2
			yoffset = self.yoffset-self.width/2
			for item in self.canvas.find_withtag(('coords',x,y)): # connect hallway to existing node
				if "floor" in self.canvas.gettags(item):
					self.makewallto = item
					break
			if not self.makewallto: # create new node to connect hallway.
				self.makewallto = self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
			self.MakeWall() # draw in the hallway
			self.makewallfrom=None
			self.makewallto=None

	# right click on canvas,
	#   - cancel making wall
	#   - unhighlight items
	#   - hotspot menu
	def CanvasRightClickCallback(self,event):
		if(self.platObject==0): return
		if self.makewallfrom:
			(x,y) = self.getItemPlatCoords(self.makewallfrom) # cancel making wall
			if (x,y) not in self.platObject.ChosenList:
				self.canvas.delete(self.makewallfrom)				
			self.makewallfrom=None
			self.makewallto=None
			self.canvas.delete('line')
		if len(self.canvas.find_withtag(CURRENT))==0:
			self.UnHighlight() # unhighlight items
		elif "hotspot" in self.canvas.gettags(CURRENT) or "start_pos" in self.canvas.gettags(CURRENT):
			self.FloorRightClkCallback(event) # call floor callback to display hotspot menu

	# canvas double clicked, start drawing hallway			
	def CanvasDblClickCallback(self,event):
		if(self.platObject==0): return
		self.canvas.delete('line')
		x,y = self.canvasToPlat(event.x,event.y)

		####### temporary fix ##########
		# don't draw wall out of bounds
		if x<0 or y<0 or x>=self.platObject.x or y>= self.platObject.y:
			tkMessageBox.showwarning("ERROR","Out of Range",parent=self.master)
			return
		################################
		
		xoffset = self.xoffset-self.width/2
		yoffset = self.yoffset-self.width/2
		for item in self.canvas.find_withtag(('coords',x,y)): # start wall from existing node
			if "floor" in self.canvas.gettags(item):
				self.makewallfrom = item
				(x0,y0,x1,y1)=self.canvas.coords(item)
				self.Highlight(self.makewallfrom)
				self.canvas.create_line((x0+x1)/2,(y0+y1)/2,(x0+x1)/2,(y0+y1)/2,fill="yellow",tags=('line'))
				return
		# no node exists to draw wall from, so must create a new one
		item = self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
		self.makewallfrom = item
		self.Highlight(self.makewallfrom)
		(x0,y0,x1,y1)=self.canvas.coords(item)
		self.canvas.create_line((x0+x1)/2,(y0+y1)/2,(x0+x1)/2,(y0+y1)/2,fill="yellow",tags=('line'))

	# cue left clicked, display edit cue dialog		
	def CueCallBack(self,event):
		(c,n,cur)=self.canvas.gettags(CURRENT)
		num = int(n)
		cue = self.cuelist[num][0] # get cue info from list
		self.canvas.itemconfig(CURRENT,fill="white",outline="white") #highlight cue as white
		d=AddCueDialog(self.master,cue,"Edit Cue Dialog",self.cuetypes) # display edit cue dialog
		if d.result:
			self.cuelist[num][0] = d.result # modify cue info
		self.canvas.itemconfig(CURRENT,fill=self.cuelist[num][0][7],outline=self.cuelist[num][0][7]) # return cue color to normal

	# floor was right clicked, display hotspot menu		
	def FloorRightClkCallback(self,event):
		hashotspot = 0
		self.currentitem = None
		x,y = self.canvasToPlat(event.x,event.y)
		for item in self.canvas.find_withtag(('coords',x,y)):
			if "floor" in self.canvas.gettags(item):
				self.currentitem = item
			elif "hotspot" in self.canvas.gettags(item):
				hashotspot = 1  # floor has a hotspot already
		if not self.currentitem:
			return
		self.Highlight(self.currentitem) # highlight floor
		menu = Menu(root, tearoff=0)
		menu.add_command(label="Add/Move Cues",command=lambda self=self,x=x,y=y,st=0: self.Add_Move_Cues(x,y,st))
		menu.add_command(label="Set Starting Position",command=self.SetStartPos)
		if not hashotspot: # floor doesn't have a hotspot, so show add hotspot menu
			menu.add_command(label="Add Hotspot", command=self.AddHotspot)
		else: # floor has a hotspot, so show the remove hotspot menu
			menu.add_command(label="Edit Hotspot",command=self.EditHotspot)
			menu.add_command(label="Remove Hotspot", command=self.RemoveHotspot)
		menu.post(event.x_root, event.y_root) # display the menu at the cursur

	# a horizontal hallway was right clicked
	def H_WallRightClkCallback(self,event):
		self.Highlight() # highlight
		x,y = None,None
		for tag in self.canvas.gettags(CURRENT):
			if tag[0:6]=='coords':
				fields = tag.split()
				x,y = int(fields[1]),int(fields[2])
				break
		if x==None or y==None:
			return
		menu = Menu(root, tearoff=0)
		menu.add_command(label="Add/Move Cues",command=lambda self=self,x=x,y=y,st=1: self.Add_Move_Cues(x,y,st))
		menu.post(event.x_root, event.y_root) # display the menu at the cursur
		
	# a vertical hallway was right clicked
	def V_WallRightClkCallback(self,event):
		self.Highlight() # highlight
		for tag in self.canvas.gettags(CURRENT):
			if tag[0:6]=='coords':
				fields = tag.split()
				x,y = int(fields[1]),int(fields[2])
				break
		if x==None or y==None:
			return
		menu = Menu(root, tearoff=0)
		menu.add_command(label="Add/Move Cues",command=lambda self=self,x=x,y=y,st=2: self.Add_Move_Cues(x,y,st))
		menu.post(event.x_root, event.y_root) # display the menu at the cursur

	# floor was left clicked, highlight it		
	def FloorCallback(self,event):
		self.Highlight()

	# a horizontal hallway was clicked, highlight it		
	def H_WallCallback(self,event):
		self.Highlight()

	# a vertical hallway was clicked, highlight it		
	def V_WallCallback(self,event):
		self.Highlight()

	# add and move cues to structure at x,y
	# structuretype:
	#  0: floor, x and y are PLAT coordinates
	#  1: horizontal hallway, x and y are PLAT for node left of hallway
	#  2: vertical hallway, x and y are PLAT for node above hallway
	def Add_Move_Cues(self,x,y,structuretype):
		d = AddMoveCueDialog(self.master,x,y,structuretype,self.cuelist,self.cuetypes,self.scalewidth,self.scalelength)
		if d.result:
			self.cuelist = d.cuelist
			self.canvas.delete('cue')
			self.numcues = 0
			for (cue,x,y,z,t) in self.cuelist:
				_x=self.xoffset+(x/self.PlatScale)*self.scale # convert from VRUT to canvas coordinates
				_z=self.yoffset+(z/self.PlatScale)*self.scale
				_t = t*pi/180 # convert from degrees to radians
				size = self.scale/10.0 # size of cue markers is proportional to the size of the layout nodes
				x1 = _x+size*cos(_t)  # calculate the vertices for the cue marker
				y1 = _z+size*sin(_t)
				x2 = _x+size*cos(_t+(2*pi/3))
				y2 = _z+size*sin(_t+(2*pi/3))
				x3 = _x
				y3 = _z
				x4 = _x+size*cos(_t+(4*pi/3))
				y4 = _z+size*sin(_t+(4*pi/3))
				if len(cue)<8: cue.append("green") # default color of cue marker is green (for backwards compatibility)
				self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,x4,y4,fill=cue[7],outline=cue[7],tags=("cue",self.numcues)) # draw the cue on the canvas
				self.numcues = self.numcues+1

	# unhighlight all items		
	def UnHighlight(self):
		for item in self.canvas.find_withtag("highlight"):
			self.canvas.dtag(item,"highlight")
			self.canvas.itemconfig(item,outline="red") # change color back to normal
		self.delbutton.config(state=DISABLED)

	# highlight CURRENT or h_item		
	def Highlight(self,h_item=None):
		if h_item==None:
			h_item = self.canvas.find_withtag(CURRENT)[0]
		self.UnHighlight() # unhighlight other items
		newtags = self.canvas.gettags(h_item) + ('highlight',)
		self.canvas.itemconfig(h_item,outline="yellow",tags = newtags) # highlight as yellow
		self.delbutton.config(state=NORMAL)

	def SetStartPos(self):
		x,y = self.getItemPlatCoords(self.currentitem)
		d = StartPosDialog(self.master)
		if d.result != None:
			self.canvas.delete("start_pos")
			self.startpos = (x, y, int(d.result))
			_x=self.xoffset+float(x)*self.scale  # get canvas coords
			_z=self.yoffset+float(y)*self.scale
			_t = (d.result-90.0)*pi/180.0 # convert from degrees to radians
			size = self.width
			x1 = _x+size*cos(_t)   # calculate vertices for the cue marker
			y1 = _z+size*sin(_t)
			x2 = _x+size*cos(_t+(2.0*pi/3.0))
			y2 = _z+size*sin(_t+(2.0*pi/3.0))
			x3 = _x+size*cos(_t+(4.0*pi/3.0))
			y3 = _z+size*sin(_t+(4.0*pi/3.0))
			self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,fill='',width=2,outline='light green',tags="start_pos")
			
	# remove hotspot from self.currentitem		
	def RemoveHotspot(self):
		x,y = self.getItemPlatCoords(self.currentitem)
		for item in self.canvas.find_withtag(("coords",x,y)):
			tags = self.canvas.gettags(item)
			if ("hotspot") in tags:
				self.canvas.delete(item)

	# edit information for an existing hotspot	
	def EditHotspot(self):
		x,y = self.getItemPlatCoords(self.currentitem)
		for item in self.canvas.find_withtag(("coords",x,y)):
			tags = self.canvas.gettags(item)
			if ("hotspot") in tags:
				num = 0
				poswav = None
				gotowav = None
				coords = [0,0]
				tags = self.canvas.gettags(item) # get tags associated with hs
				for tag in tags: # get necessary hotspot information from the tags
					if tag[0:3]=="num":
						num = int(tag[4:])
					elif tag[0:6]=="poswav":
						poswav = tag[7:]
					elif tag[0:7]=="gotowav":
						gotowav = tag[8:]
					elif tag[0:6]=="coords":
						splittag = tag.split()
						coords = [int(splittag[1]),int(splittag[2])]
				d = AddHotspotDialog(self.master,num,"Edit Hotspot",poswav,gotowav) # post edit hotspot dialog
				if d.result:
					while d.result and (d.result[0]!=num and len(self.canvas.find_withtag(("num",d.result[0])))!=0): # duplicate hotspot number
						tkMessageBox.showwarning("Invalid Hotspot number","That hotspot number has already been used",parent=self.master)
						d = AddHotspotDialog(self.master,num,"Edit Hotspot",poswav,gotowav) # re-display add hotspot dialog
					if not d.result: return # cancel if result is None (user pressed cancel)
					i = self.currentitem
					platcoords = self.getItemPlatCoords(i)
					# reconfig the hotspot
					self.canvas.itemconfig(item,text=d.result[0],tags=(("hotspot"),("num",d.result[0]),("poswav "+d.result[1]),("gotowav "+d.result[2]),("coords",platcoords[0],platcoords[1])))
						
	# add a hotspot to self.currentitem				
	def AddHotspot(self):
		nexthotspot=1
		while len(self.canvas.find_withtag(("num",nexthotspot)))!=0: # find next available hotspot number
			nexthotspot = nexthotspot+1
		d = AddHotspotDialog(self.master,nexthotspot) # display the add hotspot dialog
		if d.result:
			while d.result and len(self.canvas.find_withtag(("num",d.result[0])))!=0: # duplicate hotspot number
				tkMessageBox.showwarning("Invalid Hotspot number","That hotspot number has already been used",parent=self.master)
				d = AddHotspotDialog(self.master,nexthotspot) # re-display add hotspot dialog
			if not d.result: return # cancel if result is None (user pressed cancel)

			# display the hotspot on the canvas			
			item = self.currentitem
			platcoords = self.getItemPlatCoords(item)
			canvascoords = self.PlatToCanvas(platcoords[0],platcoords[1])
			item = self.canvas.create_text(canvascoords[0],canvascoords[1],text=d.result[0],fill="white",tags=(("hotspot"),("num",d.result[0]),("poswav "+d.result[1]),("gotowav "+d.result[2]),("coords",platcoords[0],platcoords[1])))

	# return sorted list of hotspot info of form: [(num,coords,poswav,gotowav)]
	def GetHotSpotList(self):
		hotspots = []
		for hs in self.canvas.find_withtag("hotspot"): # get each item in canvas with the tag "hotspot"
			num = 0
			poswav = None
			gotowav = None
			coords = [0,0]
			tags = self.canvas.gettags(hs) # get tags associated with hs
			for tag in tags: # get necessary hotspot information from the tags
				if tag[0:3]=="num":
					num = int(tag[4:])
				elif tag[0:6]=="poswav":
					poswav = tag[7:]
				elif tag[0:7]=="gotowav":
					gotowav = tag[8:]
				elif tag[0:6]=="coords":
					splittag = tag.split()
					coords = [int(splittag[1]),int(splittag[2])]
			hotspots.append((num,coords,poswav,gotowav))
		hotspots.sort()
		return hotspots

	# Change the textures of the walls
	def ChangeWallTextures(self):
		d = ChangeTextureDialog(self.master,self.textures)
		if d.result:
			self.textures = d.result

	# modify layout scale
	def ChangeScale(self):
		d = ChangeScaleDialog(self.master,self.scaleheight,self.scalewidth,self.scalelength,self.scalethick)
		if d.result:
			if tkMessageBox.askokcancel('Continue?','Changing the scale will remove all existing cues.\nContinue?'):
				self.RemoveCues()
				self.scaleheight = d.height
				self.scalewidth = d.width
				self.scalelength = d.length
				self.scalethick = d.thick
				self.PlatScale = self.scalewidth + self.scalelength
				self.l_scaleheight.config(text='height: %.2f'%self.scaleheight)
				self.l_scalewidth.config(text= 'width:  %.2f'%self.scalewidth)
				self.l_scalelength.config(text='length: %.2f'%self.scalelength)
				self.l_scalethick.config(text= 'thick:  %.3f'%self.scalethick)
				hotspots = self.GetHotSpotList()
				self.DisplayTextMap()
				for (num,coords,poswav,gotowav) in hotspots: # redisplay all of the hotspots
					canvascoords = self.PlatToCanvas(coords[0],coords[1]) # convert to canvas coords
					self.canvas.create_text(canvascoords[0],canvascoords[1],text=num,fill="white",tags=(("hotspot"),("num",num),("poswav "+poswav),("gotowav "+gotowav),("coords",coords[0],coords[1]))) # display hotspot marker on canvas

# dialog to read in the new textures for walls
class ChangeTextureDialog(tkSimpleDialog.Dialog):
	def __init__(self,parent,textures):
		self.textures = textures
		tkSimpleDialog.Dialog.__init__(self,parent,'Change Textures')
	def body(self,master):
		cnt = 0
		self.entries = []
		for s in ['Hallways','Walls','Floor','Ceiling']:
			Label(master,text=s).grid(row=cnt,column=0)
			e = Entry(master,width=40); e.grid(row=cnt,column=1)
			e.insert(0,self.textures[cnt])
			self.entries.append(e)
			Button(master,text='Browse',command=lambda self=self,cnt=cnt:self.Browse(cnt)).grid(row=cnt,column=2,padx=2,pady=1)
			cnt += 1
	def Browse(self,num):
		filename = tkFileDialog.askopenfilename(filetypes=[("All files",'*.*')])
		if filename:
			self.entries[num].delete(0,END)
			self.entries[num].insert(0,filename)
	def validate(self):
		try: # make sure entries are all valid 
			self.result = []
			for e in self.entries:
				if len(e.get())<=0:
					raise 'empty'
				else:
					self.result.append(e.get())
		except:
			tkMessageBox.showwarning("Invalid Entry","Please enter a filename for each entry.")
			return 0
		return 1
			
# dialog to read in the new scale of the layout
class ChangeScaleDialog(tkSimpleDialog.Dialog):
	def __init__(self,parent,height,width,length,thick):
		self.height = height
		self.width = width
		self.length = length
		self.thick = thick
		tkSimpleDialog.Dialog.__init__(self,parent,'Change Structure Scale')
	def body(self,master):
		Label(master,text='* All units are in meters *').grid(row=0,column=0,columnspan=2)
		Label(master,text='Width of node:').grid(row=1,column=0)
		self.e_width = Entry(master,width=10); self.e_width.grid(row=1,column=1)
		Label(master,text='Height (ceiling to floor):').grid(row=2,column=0)
		self.e_height = Entry(master,width=10); self.e_height.grid(row=2,column=1)
		Label(master,text='Length of corridor:').grid(row=3,column=0)
		self.e_length = Entry(master,width=10); self.e_length.grid(row=3,column=1)
		Label(master,text='Wall thickness:').grid(row=4,column=0)
		self.e_thick=Entry(master,width=10); self.e_thick.grid(row=4,column=1)
		self.e_width.insert(0,self.width)
		self.e_height.insert(0,self.height)
		self.e_length.insert(0,self.length)
		self.e_thick.insert(0,self.thick)
	def validate(self):
		try: # make sure entries are all valid floats >= 0
			self.height = float(self.e_height.get())
			self.width = float(self.e_width.get())
			self.length = float(self.e_length.get())
			self.thick = float(self.e_thick.get())
			if self.height < 0 or self.width < 0 or self.length < 0 or self.thick < 0:
				raise 'less than zero'
		except:
			tkMessageBox.showwarning("Invalid Number","All values must be numbers greater than zero")
			return 0
		self.result = 1
		return 1

# Dialog used to move or add cues to a specific structure
# structuretype:
#  0: floor, x and y are PLAT coordinates
#  1: horizontal hallway, x and y are PLAT for node left of hallway
#  2: vertical hallway, x and y are PLAT for node above hallway
class AddMoveCueDialog(tkSimpleDialog.Dialog):
	def __init__(self,parent,x,y,structuretype,cuelist,cuetypes,width,length):
		self.struct=structuretype
		self.cuelist = copy.deepcopy(cuelist)
		self.cuetypes = cuetypes
		self.scalewidth=width
		self.scalelength=length
		self.PlatScale = width+length
		self.x=x*self.PlatScale # center of node (in meters)
		self.y=y*self.PlatScale
		tkSimpleDialog.Dialog.__init__(self,parent,'Add or Move Cues')
	def apply(self):
		self.result = 1
		while None in self.cuelist:
			self.cuelist.remove(None)
		self.numcues = len(self.cuelist)
	def body(self,master):
		if self.struct==0:
			self.canvas=Canvas(master,bg='black',width=500,height=500)
			self.canvas.grid(row=0,column=0,columnspan=10)
			self.canvas.create_rectangle(50,50,450,450,outline='red',fill='black',width=3)
			self.xoffset = 250
			self.yoffset = 250
			self.scale = self.scalewidth/400 # ratio of meters to pixels
			minx = self.x - self.scalewidth
			miny = self.y - self.scalewidth
			maxx = self.x + self.scalewidth
			maxy = self.y + self.scalewidth
		else:
			if self.struct==1: # horizontal hallway
				self.x = self.x+0.5*self.PlatScale
				minx = self.x - self.scalelength
				miny = self.y - self.scalewidth
				maxx = self.x + self.scalelength
				maxy = self.y + self.scalewidth
				recwidth = self.scalelength # width of rectangle
				recheight = self.scalewidth # heigth of rectangle
			else: # vertical hallway
				self.y = self.y+0.5*self.PlatScale
				minx = self.x - self.scalewidth
				miny = self.y - self.scalelength
				maxx = self.x + self.scalewidth
				maxy = self.y + self.scalelength
				recwidth = self.scalewidth # width of rectangle
				recheight = self.scalelength # heigth of rectangle
			if recheight/recwidth < 0.5: # horizontal rectangle
				width = 600; height=400 # canvas dimensions
				self.scale = recwidth/500
				coords = [50,200-recheight*0.5/self.scale,550,200+recheight*0.5/self.scale]
			elif recheight/recwidth > 2.0: # vertical rectangle
				width = 400; height=600  # canvas dimensions
				self.scale = recheight/500
				coords = [200-recwidth*0.5/self.scale,50,200+recwidth*0.5/self.scale,550]
			elif recheight>recwidth: # squarish vertical rectangle
				width = 500; height=500  # canvas dimensions
				self.scale = recheight/400
				coords = [250-recwidth*0.5/self.scale,50,250+recwidth*0.5/self.scale,450]
			else: # square or squarish horizontal rectangle
				width = 500; height=500 # canvas dimensions
				self.scale = recwidth/400
				coords = [50,250-recheight*0.5/self.scale,450,250+recheight*0.5/self.scale]
			self.canvas=Canvas(master,bg='black',width=width,height=height)
			self.canvas.grid(row=0,column=0,columnspan=10)
			self.canvas.create_rectangle(coords,outline='red',fill='black',width=3)
			self.xoffset = width/2.0
			self.yoffset = height/2.0
		self.numcues=0
		for (cue,x,y,z,t) in self.cuelist:
			if x>=minx and x<=maxx and z>=miny and z<=maxy:
				if len(cue)<8: cue.append("green") # default color of cue marker is green (for backwards compatibility)
				self.canvas.create_polygon(self.CalcCueCanvasCoords(x,z,t),fill=cue[7],outline='black',tags=("cue",self.numcues)) # draw the cue on the canvas
			self.numcues = self.numcues+1
		self.canvas.tag_bind("cue","<Button-3>",self.CueCallBack) # bind callbacks to cues
		f = Frame(master)
		f.grid(row=1,column=0)
		f2 = Frame(master)
		f2.grid(row=1,column=1)
		self.l_cursorcoords=Label(f,text='Cursor Position (VRUT): ')
		self.l_cursorcoords.grid(row=0,column=0,columnspan=4,sticky=NW)
		Label(f,text='Cue X').grid(row=1,column=0,sticky=NW)
		Label(f,text='Cue Y').grid(row=2,column=0,sticky=NW)
		Label(f,text='Cue Z').grid(row=3,column=0,sticky=NW)
		Label(f,text='Cue T').grid(row=4,column=0,sticky=NW)
		self.e_cuex = Entry(f,width=10); self.e_cuex.grid(row=1,column=1,sticky=NW)
		self.e_cuey = Entry(f,width=10); self.e_cuey.grid(row=2,column=1,sticky=NW)
		self.e_cuez = Entry(f,width=10); self.e_cuez.grid(row=3,column=1,sticky=NW)
		self.e_cuet = Entry(f,width=10); self.e_cuet.grid(row=4,column=1,sticky=NW)
		self.b_delete = Button(f2,text='Delete Cue',state=DISABLED,width=10,command=self.DeleteCue)
		self.b_delete.grid(row=0,column=0,sticky=NW,pady=3)
		Button(f2,text='Add Cue',width=10,command=self.AddCue).grid(row=1,column=0,sticky=NW,pady=3)
		self.e_cuex.bind('<Key>',self.EntryChange)
		self.e_cuey.bind('<Key>',self.EntryChange)
		self.e_cuez.bind('<Key>',self.EntryChange)
		self.e_cuet.bind('<Key>',self.EntryChange)
		self.canvas.bind('<Button-3>',self.CanvasRightClick)
		self.canvas.tag_bind('cue','<Button-1>',self.CueLeftClick)
		self.canvas.tag_bind('cue','<B1-Motion>',self.CueLeftClickMove)
		self.currentcue = None
		self.canvas.bind('<Motion>',self.CursorMotion)
		
	# cue right clicked, display edit cue dialog		
	def CueCallBack(self,event):
		self.HighlightCue(CURRENT)
		num=int(self.canvas.gettags(CURRENT)[1])
		cue = self.cuelist[num][0] # get cue info from list
		d=AddCueDialog(self.master,cue,"Edit Cue Dialog",self.cuetypes) # display edit cue dialog
		if d.result:
			self.cuelist[num][0] = d.result # modify cue info
		self.canvas.itemconfig(CURRENT,fill=self.cuelist[num][0][7],outline='black') # return cue color to normal
		self.UnHighlightCues()
	def CursorMotion(self,event):
		self.l_cursorcoords.config(text='Cursor Position (VRUT): %.4f, -%.4f'%self.CANVAStoVRUT(event.x,event.y))
	def VRUTtoCANVAS(self,x,z):
		return (((x-self.x)/self.scale+self.xoffset),((z-self.y)/self.scale+self.yoffset))
	def CANVAStoVRUT(self,x,y):
		return (((x-self.xoffset)*self.scale+self.x),((y-self.yoffset)*self.scale+self.y))
	# Calculate the canvas coordinates for the vertices of the cue marker given x,z (vrut coords)
	def CalcCueCanvasCoords(self,x,z,t):
		_x,_z = self.VRUTtoCANVAS(x,z)
		_t = t*pi/180 # convert from degrees to radians
		size = 20 # size of cue markers is proportional to the size of the layout nodes
		x1 = _x+size*cos(_t)  # calculate the vertices for the cue marker
		y1 = _z+size*sin(_t)
		x2 = _x+size*cos(_t+(2*pi/3))
		y2 = _z+size*sin(_t+(2*pi/3))
		x3 = _x
		y3 = _z
		x4 = _x+size*cos(_t+(4*pi/3))
		y4 = _z+size*sin(_t+(4*pi/3))
		return [x1,y1,x2,y2,x3,y3,x4,y4]
	def HighlightCue(self,cue):
		if self.UnHighlightCues(): return
		tags = self.canvas.gettags(cue)
		n = tags[1]
		tags+=('highlight',)
		self.currentcue = int(n)
		(_,x,y,z,t) = self.cuelist[self.currentcue]
		self.e_cuex.delete(0,END); self.e_cuex.insert(0,x)
		self.e_cuey.delete(0,END); self.e_cuey.insert(0,y)
		self.e_cuez.delete(0,END); self.e_cuez.insert(0,-z)
		self.e_cuet.delete(0,END); self.e_cuet.insert(0,t)
		self.canvas.itemconfig(cue,outline='white',width=2,tags=tags)
		self.b_delete.config(state=NORMAL)
	def validate(self):
		if self.currentcue!=None:
			try:
				self.cuelist[self.currentcue][1]=string.atof(self.e_cuex.get())
				self.cuelist[self.currentcue][2]=string.atof(self.e_cuey.get())
				self.cuelist[self.currentcue][3]=-string.atof(self.e_cuez.get())
				self.cuelist[self.currentcue][4]=string.atof(self.e_cuet.get())
			except:
				tkMessageBox.showwarning("Invalid Parameters","One or more of the cue coordinates are invalid")
				return 0
		return 1
	def UnHighlightCues(self):
		cues = self.canvas.find_withtag('highlight')
		for cue in cues:
			if not self.validate(): return 1
			self.canvas.dtag(cue,'highlight')
			self.canvas.itemconfig(cue,outline='black',width=0)
		self.currentcue = None
		self.e_cuex.delete(0,END)
		self.e_cuey.delete(0,END)
		self.e_cuez.delete(0,END)
		self.e_cuet.delete(0,END)
		self.b_delete.config(state=DISABLED)
		return 0
	def AddCue(self):
		d = VisualCueQuickList(self.master,self.cuetypes,1)
		if d.result:
			x,z = self.CANVAStoVRUT(self.xoffset,self.yoffset)
			y,t = 0,0
			self.cuelist.append([d.result,x,y,z,t])
			cue = self.canvas.create_polygon(self.CalcCueCanvasCoords(x,z,t),fill=d.result[7],outline='black',tags=("cue",self.numcues)) # draw the cue on the canvas
			self.canvas.tag_bind("cue","<Button-3>",self.CueCallBack) # bind callbacks to cues
			self.numcues+=1
			self.HighlightCue(cue)
		else:
			print 'none'
	def DeleteCue(self):
		cues = self.canvas.find_withtag('highlight')
		for cue in cues:
			tags = self.canvas.gettags(cue)
			self.cuelist[string.atoi(tags[1])]=None
			self.canvas.delete(cue)			
		self.currentcue = None
		self.e_cuex.delete(0,END)
		self.e_cuey.delete(0,END)
		self.e_cuez.delete(0,END)
		self.e_cuet.delete(0,END)
		self.b_delete.config(state=DISABLED)
	def CanvasRightClick(self,event):
		self.UnHighlightCues()
	def CueLeftClick(self,event):
		self.HighlightCue(CURRENT)
	def CueLeftClickMove(self,event):
		x,z = self.CANVAStoVRUT(event.x,event.y)
		self.cuelist[self.currentcue][1]=x
		self.cuelist[self.currentcue][3]=z
		coords = self.CalcCueCanvasCoords(x,z,self.cuelist[self.currentcue][4])
		self.canvas.coords(CURRENT,coords[0],coords[1],coords[2],coords[3],coords[4],coords[5],coords[6],coords[7])
		(c,x,y,z,t) = self.cuelist[self.currentcue]
		self.e_cuex.delete(0,END); self.e_cuex.insert(0,x)
		self.e_cuey.delete(0,END); self.e_cuey.insert(0,y)
		self.e_cuez.delete(0,END); self.e_cuez.insert(0,-z)
		self.e_cuet.delete(0,END); self.e_cuet.insert(0,t)
	def EntryChange(self,event=None):
		if self.currentcue==None: return
		try:
			event.widget.selection_clear()
			event.widget.icursor(END)			
			vals=[]
			for widget in [self.e_cuex,self.e_cuey,self.e_cuez,self.e_cuet]:
				v = widget.get() # get the content of all of the fields
				if event.widget == widget:
					# this callback function is called before the contents of the
					# entry field are modified, so you need to take the original
					# contents of the field and update them based on which key was pressed
					if event.char=='\b': v = v[:-1] # backspace was pressed
					else: v = v+event.char # append key to original contents
				if len(v)==0: v = '0.0'
				if widget==self.e_cuez:
					vals.append(-float(v))
				else:
					vals.append(float(v))
			self.cuelist[self.currentcue][1:]=vals
			coords = self.CalcCueCanvasCoords(vals[0],vals[2],vals[3])			
			self.canvas.coords('highlight',coords[0],coords[1],coords[2],coords[3],coords[4],coords[5],coords[6],coords[7])
		except Exception,e:
			return
		

# Add Hotspot Dialog used to get the hotspot number and necessary .wav files when adding a hotspot
class AddHotspotDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent, hotspotnum=0, title="Add Hotspot",wavfile="None",gotofile="None"):
		self.hotspotnum = hotspotnum # set initial values
		if title == "Add Hotspot":
			wavfile = './Layouts/SharedMedia/Sounds/Position%d.wav'%hotspotnum
			gotofile = './Layouts/SharedMedia/Sounds/GotoPos%d.wav'%hotspotnum
		self.wavfilename = wavfile
		self.gotowavfilename = gotofile
		tkSimpleDialog.Dialog.__init__(self,parent,title)
	def body(self,master):
		# define layout for dialog
		Label(master,text='Hotspot #',anchor=W).grid(row=0,column=0,sticky=W)
		Label(master,text='Sound',anchor=W).grid(row=1,column=0,sticky=W)
		Label(master,text='Goto Sound',anchor=W).grid(row=2,column=0,sticky=W)
		self.e_num = Entry(master,width=5) # hotspot number entry box
		self.e_num.grid(row=0,column=1,sticky=W)
		self.e_num.insert(END,self.hotspotnum)
		self.e_sound = Entry(master) # hotspot sound file entry box
		self.e_sound.grid(row=1,column=1,sticky=W)
		self.e_sound.insert(END,self.wavfilename)
		Button(master,text='Browse',command=self.Browse).grid(row=1,column=2) #browse for file button
		self.e_gotosound = Entry(master) # hotspot goto-sound file entry box
		self.e_gotosound.grid(row=2,column=1,sticky=W)
		self.e_gotosound.insert(END,self.gotowavfilename)
		Button(master,text='Browse',command=self.GotoBrowse).grid(row=2,column=2) #browse for file button
		return self.e_num
	def validate(self):
		self.wavfilename=self.e_sound.get()
		self.gotowavfilename=self.e_gotosound.get()
		try: # make sure hotspot number is valid
			self.hotspotnum = int(self.e_num.get())
		except:
			tkMessageBox.showwarning("Input a Hotspot number","Please input a valid hotspot number.",parent=self)
			return 0
		self.result = (self.hotspotnum,self.wavfilename,self.gotowavfilename)
		return 1
	def Browse(self): #browse for hotspot sound file
		filename = tkFileDialog.askopenfilename(parent=self)
		if filename:
			self.e_sound.delete(0,END)
			self.e_sound.insert(END,filename)
	def GotoBrowse(self): #browse for hotspot goto-sound file
		filename = tkFileDialog.askopenfilename(parent=self)
		if filename:
			self.e_gotosound.delete(0,END)
			self.e_gotosound.insert(END,filename)

# Starting position dialog
class StartPosDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent):
		tkSimpleDialog.Dialog.__init__(self,parent,"Starting Position")
	def body(self,master):
		# define layout for dialog
		self.start_angle = IntVar()
		self.start_angle.set(0)
		Radiobutton(master,text='Up',variable=self.start_angle,value=0).grid(row=0,column=1,sticky=W)
		Radiobutton(master,text='Down',variable=self.start_angle,value=180).grid(row=2,column=1,sticky=W)
		Radiobutton(master,text='Left',variable=self.start_angle,value=270).grid(row=1,column=0,sticky=W)
		Radiobutton(master,text='Right',variable=self.start_angle,value=90).grid(row=1,column=2,sticky=W)
	def apply(self):
		self.result = self.start_angle.get()

# Export dialog used to choose filename and which files to export
class ExportDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent, filename, title="Export Files"):
		# set default filename
		if len(os.path.basename(filename))==0:
			filename='NewLayout'
		if len(os.path.dirname(filename)) == 0 or not os.path.isdir(os.path.dirname(filename)):
			filename = os.path.join(os.getcwd(),os.path.basename(filename))
		self.initfilename=filename
		tkSimpleDialog.Dialog.__init__(self,parent,title)
	def apply(self):
		self.result = 'OK'
	def validate(self):
		# make sure filename is okay
		if not self.filename:
			tkMessageBox.showwarning("Choose a Filename","Please choose a file name to save as.",parent=self)
			return 0
		f,x = os.path.splitext(self.filename)
		if len(x) != 0:
			tkMessageBox.showwarning("Do not include extension","Please do not add an extension to the filename.",parent=self)
			return 0
		return 1
	def button(self):
		# browse for a filename to save as
		filename = tkFileDialog.asksaveasfilename(parent=self,initialfile=self.initfilename)
		if filename:
			self.filename=filename
			self.label.config(text=filename)
	def body(self,master):
		# define dialog layout
		self.filename=None
		Button(master,text='File Name',command=self.button).grid(row=1,column=0,padx=5,pady=5,sticky=W) # browse filenames button
		self.label = Label(master,text=self.initfilename,anchor=W)
		self.label.grid(row=1,column=1,sticky=W)
		self.filename = self.initfilename
		
		self.map = IntVar() # stores the state of the text map checkbutton
		c = Checkbutton(master,text='Text map  (".txt")',variable=self.map)
		c.grid(row=2,column=0,columnspan=2,sticky=NW)
		c.select()
		
		self.wrl = IntVar() # stores the state of the wrl checkbutton
		c = Checkbutton(master,text='Layout WRL File  (".wrl")',variable=self.wrl)
		c.grid(row=3,column=0,columnspan=2,sticky=NW)
		c.select()
		
		self.obj = IntVar() # stores the state of the cue checkbutton
		c = Checkbutton(master,text='Visual Cue File  (".obj")',variable=self.obj)
		c.grid(row=4,column=0,columnspan=2,sticky=NW)
		c.select()

		self.poi = IntVar() # stores the state of the hotspot checkbutton
		c = Checkbutton(master,text='Hotspots  (".poi")',variable=self.poi)
		c.grid(row=5,column=0,columnspan=2,sticky=NW)
		c.select()
		
		self.run = IntVar() # stores the state of the run file checkbutton
		c = Checkbutton(master,text='Run File  (".run")',variable=self.run)
		c.grid(row=6,column=0,columnspan=2,sticky=NW)
		c.select()

		self.startpos = IntVar() # stores the state of the run file checkbutton
		c = Checkbutton(master,text='Start File  (".pos")',variable=self.startpos)
		c.grid(row=7,column=0,columnspan=2,sticky=NW)
		c.select()		

# create a new type of visual cue
class AddCueDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent, cuedata=None, title="Add Cue Type",cuetypes=None):
		self.cuedata = cuedata # initial cue settings (if editting a cue type)
		self.cuetypes= cuetypes # data for other cue types
		tkSimpleDialog.Dialog.__init__(self,parent,title)
	def buttonbox(self):
		pass	
	def body(self,master):
		Label(master,text="Name:",anchor=W).grid(row=0,column=0,sticky=W)
		Label(master,text="WRL File:",anchor=W).grid(row=1,column=0,sticky=W)
		Label(master,text="Marker Color:",anchor=W).grid(row=2,column=0,sticky=W)
		self.name = Entry(master); self.name.grid(row=0,column=1,pady=3) # cue type name
		self.wrl  = Entry(master); self.wrl.grid(row=1,column=1,pady=3) # wrl file describing cue's shape
		if self.cuetypes!=None: # allow user to select an existing cue type
			Button(master,text="Types",command=self.clicktypes).grid(row=0,column=2,pady=2,sticky=W)
		Button(master,text="Browse",command=self.BrowseWRL).grid(row=1,column=2,pady=2,sticky=W)

		frame = Frame(master)
		frame.grid(row=2,column=1,padx=5,sticky=N)
		scrollbar = Scrollbar(frame, orient=VERTICAL)
		self.listbox = Listbox(frame, bg="white",height=4,exportselection=0,yscrollcommand=scrollbar.set)
		scrollbar.config(command=self.listbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.listbox.pack(side=LEFT, fill=BOTH, expand=1)
		if self.cuedata: # if editting a cue, set the color
			color = self.cuedata[7]
		else: # otherwise set default color
			color = "green"
		cnt = 0
		# insert available colors in listbox
		for item in ["green","blue","yellow","magenta","cyan","orange","purple","brown","pink"]:
			self.listbox.insert(END,item)
			if item==string.lower(color): # highlight the selected color
				self.listbox.select_set(cnt)
				self.listbox.see(cnt)
			cnt+=1

		self.addTexture = IntVar() # variable stores the state of the add texture checkbutton
		frame1 = Frame(master,bd=3,relief=GROOVE) # frame containing texture options
		frame1.grid(row=3,column=0,columnspan=3,pady=3)
		self.addtxt_checkbutton = Checkbutton(frame1, text="Add Texture (to ROOT Node)",variable=self.addTexture,command=self.clickTexture)
		self.addtxt_checkbutton.grid(row=1,column=0,columnspan=2,sticky=W)
		self.l_gentext=Label(frame1,text="General Texture:",anchor=W,state=DISABLED); self.l_gentext.grid(row=2,column=0,sticky=W)
		self.l_curtext=Label(frame1,text="Curtain Texture:",anchor=W,state=DISABLED); self.l_curtext.grid(row=3,column=0,sticky=W)
		self.l_viewprob=Label(frame1,text="View Probability (%):",anchor=W,state=DISABLED); self.l_viewprob.grid(row=4,column=0,sticky=W)
		self.regtext = Entry(frame1,bg="Gray"); self.regtext.grid(row=2,column=1,pady=3)
		self.regtext.insert(0,'None'); self.regtext.config(state=DISABLED)
		self.b_regtext=Button(frame1,text="Browse",command=self.BrowseRegText,state=DISABLED); self.b_regtext.grid(row=2,column=2,pady=2,padx=2)
		self.curtext = Entry(frame1,bg="Gray"); self.curtext.grid(row=3,column=1,pady=3)
		self.curtext.insert(0,'None'); self.curtext.config(state=DISABLED)
		self.b_curtext=Button(frame1,text="Browse",command=self.BrowseCurText,state=DISABLED); self.b_curtext.grid(row=3,column=2,pady=2,padx=2)
		self.viewprob = Entry(frame1,width=7,text='100',state=NORMAL,bg="Gray"); self.viewprob.grid(row=4,column=1,pady=3,sticky=W)
		self.viewprob.delete(0,END)
		self.viewprob.insert(0,'100')
		self.viewprob.config(state=DISABLED)
		self.time_texture = IntVar() # variable stores the state of the 'texture based on time' checkbutton
		
		frame2 = Frame(frame1,bd=3,relief=GROOVE) # frame containing time-based options
		frame2.grid(row=5,column=0,columnspan=2,pady=3)
		self.chk_alttime = Checkbutton(frame2, text="Alternate texture based on # moves",variable=self.time_texture,command=self.click,state=DISABLED)
		self.chk_alttime.grid(row=0,column=0,columnspan=2)
		self.l_meantime = Label(frame2,text="Mean # Moves:",state=DISABLED); self.l_meantime.grid(row=1,column=0,sticky=E)
		self.l_standardev = Label(frame2,text="Standard Deviation:",state=DISABLED); self.l_standardev.grid(row=2,column=0,sticky=E)		
		self.meantime = Entry(frame2,width=7,state=DISABLED,bg="Gray"); self.meantime.grid(row=1,column=1,pady=2)
		self.stddev = Entry(frame2,width=7,state=DISABLED,bg="Gray"); self.stddev.grid(row=2,column=1,pady=2)
		
		b = Button(master, text="OK", width=15, command=self.ok, default=ACTIVE)
		b.grid(row=10,column=0,padx=5,pady=3,sticky=W)
		b = Button(master, text="Cancel", width=15, command=self.cancel)
		b.grid(row=10,column=1,padx=5,pady=3,sticky=W)
		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)

		if self.cuedata: #insert values if editting a cue
			self.name.insert(END,self.cuedata[0])
			self.wrl.insert(END,self.cuedata[1])			
			if string.upper(self.cuedata[2])!='NONE' or string.upper(self.cuedata[3])!='NONE':
				# textures are specified, so initialize those fields
				self.addtxt_checkbutton.select() # select the add texture checkbutton
				self.clickTexture() # enable fields
				self.regtext.delete(0,END)
				self.curtext.delete(0,END)
				self.regtext.insert(END,self.cuedata[2])
				self.curtext.insert(END,self.cuedata[3])
				self.viewprob.delete(0,END)
				self.viewprob.insert(END,self.cuedata[4]*100)
				if(self.cuedata[5]>=0):
					# time-based options are specified, so initialize those fields
					self.chk_alttime.select() # select the time-based checkbutton
					self.click() # enable fields
					self.meantime.insert(END,self.cuedata[5])
					self.stddev.insert(END,self.cuedata[6])		
		return self.name

	# initialize field values	
	def initvalues(self,cuedata):
		self.name.delete(0,END)
		self.name.insert(END,cuedata[0]) # set name field
		self.wrl.delete(0,END)
		self.wrl.insert(END,cuedata[1]) # set wrl field
		list = self.listbox.get(0,END)
		self.listbox.select_clear(0,END)
		for i in range(len(list)): # select the cue marker's color
			if cuedata[7]==list[i]:
				self.listbox.select_set(i)
				self.listbox.see(i)
				break
		if string.upper(cuedata[2])!='NONE' or string.upper(cuedata[3])!='NONE':
			# set texture fields
			self.addtxt_checkbutton.select()
			self.clickTexture()
			self.regtext.delete(0,END)
			self.regtext.insert(END,cuedata[2])
			self.curtext.delete(0,END)
			self.curtext.insert(END,cuedata[3])
			self.viewprob.delete(0,END)
			self.viewprob.insert(END,cuedata[4]*100)
			if(cuedata[5]>=0):
				# set time-based option fields
				self.chk_alttime.select()
				self.click()
				self.meantime.delete(0,END)
				self.meantime.insert(END,cuedata[5])
				self.stddev.delete(0,END)
				self.stddev.insert(END,cuedata[6])
			else:
				# time-based options not used, so clear the fields
				self.meantime.config(state=NORMAL)
				self.meantime.delete(0,END)
				self.stddev.config(state=NORMAL)
				self.stddev.delete(0,END)
				self.chk_alttime.deselect()
				self.click()
		else:
			# texture options not used, so clear the fields
			self.regtext.config(state=NORMAL)
			self.curtext.config(state=NORMAL)
			self.viewprob.config(state=NORMAL)
			self.regtext.delete(0,END)
			self.curtext.delete(0,END)
			self.viewprob.delete(0,END)
			self.viewprob.insert(0,'100')
			self.meantime.config(state=NORMAL)
			self.meantime.delete(0,END)
			self.stddev.config(state=NORMAL)
			self.stddev.delete(0,END)
			self.chk_alttime.deselect()
			self.click()
			self.addtxt_checkbutton.deselect()
			self.clickTexture()

	# display a list of the cue types to select from			
	def clicktypes(self):
		d=VisualCueQuickList(self,self.cuetypes,1)
		if d.result:
			self.initvalues(d.result) # set fields based on selected type

	# make sure all fields are okay before closing			
	def validate(self):
		try:
			name = self.name.get()
			wrl = self.wrl.get()
			regtext = self.regtext.get()
			curtext = self.curtext.get()
			viewprob = 1
			if len(name)==0 or len(wrl)==0: # make sure names are specified
				raise Exception()
			if self.addTexture.get(): # make sure textures are specified, and viewprob is ok
				viewprob = float(self.viewprob.get())/100.0
				if len(regtext)==0 or len(curtext)==0 or viewprob < 0 or viewprob > 1:
					raise Exception()
				if self.time_texture.get(): # make sure time-based options are okay
					meantime = float(self.meantime.get())
					stddev = float(self.stddev.get())
					if meantime <= 0.0 or stddev < 0.0:
						raise Exception()
				else:
					# time-based options not used, so set defaults
					meantime = -1
					stddev = 0
			else:
				# textures not used, so set defaults
				regtext = "None"
				curtext = "None"
				viewprob = 1
				meantime = -1
				stddev = 0
			items = self.listbox.curselection()
			try: items = map(int, items)
			except ValueError: pass
			color = self.listbox.get(items[0]) # get selected color
			self.result = [name,wrl,regtext,curtext,viewprob,meantime,stddev,color] # save all field values
		except:
			tkMessageBox.showwarning("Invalid Entry",
				"One or more of the entries are invalid.",
				parent=self)
			return 0
		return 1

	# The Add Texture checkbutton was clicked	
	def clickTexture(self):
		if(self.addTexture.get()): # if checkbutton is selected, enable fields
			self.regtext.config(state=NORMAL,bg="White")
			self.curtext.config(state=NORMAL,bg="White")
			self.viewprob.config(state=NORMAL,bg="White")
			self.l_gentext.config(state=NORMAL)
			self.l_curtext.config(state=NORMAL)
			self.l_viewprob.config(state=NORMAL)
			self.b_regtext.config(state=NORMAL)
			self.b_curtext.config(state=NORMAL)
			self.chk_alttime.config(state=NORMAL)
			self.click()
		else: # if checkbutton is not selected, disable fields
			self.regtext.config(state=DISABLED,bg="Gray")
			self.curtext.config(state=DISABLED,bg="Gray")
			self.viewprob.config(state=DISABLED,bg="Gray")
			self.l_gentext.config(state=DISABLED)
			self.l_curtext.config(state=DISABLED)
			self.l_viewprob.config(state=DISABLED)
			self.b_regtext.config(state=DISABLED)
			self.b_curtext.config(state=DISABLED)
			self.chk_alttime.config(state=DISABLED)
			self.click(1)

	# The time-based options checkbutton was clicked			
	def click(self,flag=None):
		if(self.time_texture.get() and not flag): # enable fields
			self.l_meantime.config(state=NORMAL)
			self.l_standardev.config(state=NORMAL)
			self.meantime.config(state=NORMAL,bg="White")
			self.stddev.config(state=NORMAL,bg="White")
		else: # disable fields
			self.l_meantime.config(state=DISABLED)
			self.l_standardev.config(state=DISABLED)
			self.meantime.config(state=DISABLED,bg="Gray")
			self.stddev.config(state=DISABLED,bg="Gray")

	# browse WRL file names			
	def BrowseWRL(self):
		filename = tkFileDialog.askopenfilename()
		if(filename):
			self.wrl.delete(0,END)
			self.wrl.insert(END,filename)

	# browse for texture file names			
	def BrowseRegText(self):
		filename = tkFileDialog.askopenfilename()
		if(filename):
			self.regtext.delete(0,END)
			self.regtext.insert(END,filename)
			
	# browse for curtain texture file names
	def BrowseCurText(self):
		filename = tkFileDialog.askopenfilename()
		if(filename):
			self.curtext.delete(0,END)
			self.curtext.insert(END,filename)

# Shows a list of cue types to select from			
class VisualCueQuickList(tkSimpleDialog.Dialog):
	def __init__(self, parent, cuetypes, flag=0,ratio=None):
		# flag: 0=view/edit, 1=select cue type, 2=select cue type with ratio
		self.flag = flag
		self.ratio = ratio
		self.cuetypes = cuetypes
		if self.flag == 0: title = "Visual Cue Quick List"
		else: title = "Select a Visual Cue Type"
		tkSimpleDialog.Dialog.__init__(self,parent,title)
		
	def buttonbox(self):
		pass

	def body(self, master):
		# set up dialog layout
		b = Button(master, text="Add Type", width=15, command=self.AddType)
		b.grid(row=0,column=0,padx=5,pady=3,sticky=W)
		b = Button(master, text="Remove Type", width=15, command=self.RemoveType)
		b.grid(row=1,column=0,padx=5,pady=3,sticky=W)
		b = Button(master, text="Edit Type", width=15, command=self.EditType)
		b.grid(row=2,column=0,padx=5,pady=3,sticky=W)
		frame = Frame(master)
		frame.grid(row=3,column=0,padx=5,pady=3,sticky=NW)
		
		if self.flag == 2: # select a ratio with the cue (used when distributing cues)
			Label(frame, text="Ratio:",height=3,anchor=NW).grid(row=0,column=0,padx=5,pady=3,sticky=NW)
			self.entry = Entry(frame,width=3)
			if self.ratio: self.entry.config(text=itoa(ratio))
			self.entry.grid(row=0,column=1,sticky=NW)
			Label(frame,text="%",anchor=NW).grid(row=0,column=2,sticky=NW)
		else:
			# not using ratio, but add a dummy field to keep layout consistant
			Label(frame,text="",height=3).grid(row=0,column=0,sticky=NW)
			self.entry = None
		if self.flag != 0:
			# selecting a cue type
			b = Button(master, text="OK", width=15, command=self.ok, default=ACTIVE)
			b.grid(row=4,column=0,padx=5,pady=3,sticky=W)
			b = Button(master, text="Cancel", width=15, command=self.cancel)
			b.grid(row=5,column=0,padx=5,pady=3,sticky=W)
		else:
			# editing cue list
			b = Button(master, text="Close", width=15, command=self.cancel)
			b.grid(row=5,column=0,padx=5,pady=3,sticky=W)

		# set up listbox containing cue types		
		frame = Frame(master)
		frame.grid(row=0,column=2,rowspan=10,padx=5,sticky=N)
		scrollbar = Scrollbar(frame, orient=VERTICAL)
		self.listbox = Listbox(frame, bg="white",height=13,exportselection=0,yscrollcommand=scrollbar.set)
		scrollbar.config(command=self.listbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.listbox.pack(side=LEFT, fill=BOTH, expand=1)
		self.listbox.bind('<Double-Button-1>',self.ListBoxDoubleClick)
		for item in self.cuetypes:
			self.listbox.insert(END,item[0])
		
		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)		
		
		return self.entry # initial focus

	# make sure values are okay before closing	
	def validate(self):
		if self.flag==2:
			try:
				# make sure inputted ratio value is okay
				self.ratio = float(self.entry.get())
				if self.ratio < 0 or self.ratio > 100:
					raise ValueError
			except ValueError:
				tkMessageBox.showwarning("Invalid Ratio Entry",
					"Please input a ratio between 0 and 100%.",
					parent=self)
				return 0
		if self.flag!=0:
			# make sure a cue type was selected
			items = self.listbox.curselection()
			try: items = map(int, items)
			except ValueError: pass

			if(len(items) == 0):
				tkMessageBox.showwarning("Invalid Selection",
					"Please select a cue type.",parent=self)
				return 0
			self.result = self.cuetypes[items[0]]
		return 1
		
	def apply(self):
		pass

	# add a type to the list	
	def AddType(self):
		d = AddCueDialog(self)
		if d.result:
			self.cuetypes.append(d.result)
			self.listbox.insert(END,d.result[0])
		return 0

	# remove a type from the list	
	def RemoveType(self):
		item = self.listbox.curselection() # get selected cue type
		try: item = map(int, item)
		except ValueError: pass
		if len(item)==0:
			tkMessageBox.showwarning("Invalid Selection",
					"Please select a cue type.",parent=self)
		else:
			self.listbox.delete(item[0]) # remove from listbox
			self.cuetypes.pop(item[0])   # remove from list of cue types
		return 0

	# edit a cue type	
	def EditType(self):
		item = self.listbox.curselection() # get selected cue type
		try: item = map(int, item)
		except ValueError: pass
		if len(item)==0:
			tkMessageBox.showwarning("Invalid Selection",
					"Please select a cue type.",parent=self)
		else:
			d = AddCueDialog(self,self.cuetypes[item[0]],"Edit Cue Dialog")
			if d.result:
				self.cuetypes[item[0]]=d.result
				self.listbox.delete(item[0])
				self.listbox.insert(item[0],d.result[0])
		return 0

	# edit a cue type if listbox was double clicked	
	def ListBoxDoubleClick(self,event):
		self.EditType()

# Get the cue offsets for cue distribution
class OffsetQueryDialog(tkSimpleDialog.Dialog):
	def __init__(self,parent,title,type,cueoffsets,width,length):
		self.cueoffsets=cueoffsets
		self.scalewidth = width
		self.scalelength = length
		self.PlatScale = width+length
		self.type = type #0= floor offsets, 1=hallway offsets 2=wall offsets
		tkSimpleDialog.Dialog.__init__(self,parent,title)
	def body(self,master):
		# set up dialog layout
		Label(master,text="X offset:").grid(row=0,column=0)
		self.Xentry = Entry(master,width=10)
		self.Xentry.grid(row=0,column=1)
		self.Xentry.insert(END,self.cueoffsets[0])
		Label(master,text="Y offset:").grid(row=1,column=0)
		self.Yentry = Entry(master,width=10)
		self.Yentry.grid(row=1,column=1)
		self.Yentry.insert(END,self.cueoffsets[1])
		Label(master,text="Z offset:").grid(row=2,column=0)
		self.Zentry = Entry(master,width=10)
		self.Zentry.grid(row=2,column=1)
		self.Zentry.insert(END,self.cueoffsets[2])
		Label(master,text="Theta offset:").grid(row=3,column=0)
		self.Tentry = Entry(master,width=10)
		self.Tentry.grid(row=3,column=1)
		self.Tentry.insert(END,self.cueoffsets[3])

		# call self.keypressed if content of fields are modified		
		self.Xentry.bind('<Key>',self.keypressed)
		self.Yentry.bind('<Key>',self.keypressed)
		self.Zentry.bind('<Key>',self.keypressed)
		self.Tentry.bind('<Key>',self.keypressed)

		# set up canvas to preview offsets		
		self.canvas = Canvas(master,width=220,height=220,background="Black")
		self.canvas.grid(row=4,columnspan=3)
		self.scale = 100 # length of hallways
		self.width = self.scale/(self.PlatScale/self.scalewidth)#25  # width of hallways
		self.offset = (220 - (self.scale+self.width)) /2.0 # used to center the hallways
		for x in range(2):
			for y in range(2):
				# draw a node
				self.canvas.create_rectangle(self.offset+x*self.scale,self.offset+y*self.scale,self.offset+x*self.scale+self.width,self.offset+y*self.scale+self.width,fill="black",outline="red")
				if x==0: # draw a horizontal hallway
					self.canvas.create_rectangle(self.offset+x*self.scale+self.width+1,self.offset+y*self.scale,self.offset+(x+1)*self.scale-1,self.offset+y*self.scale+self.width,fill="red",outline="red")
				if y==0: # draw a vertical hallway
					self.canvas.create_rectangle(self.offset+x*self.scale,self.offset+y*self.scale+self.width+1,self.offset+x*self.scale+self.width,self.offset+(y+1)*self.scale-1,fill="red",outline="red")
		self.offset+=self.width/2
		self.DistributeCues(self.cueoffsets)
		return self.Xentry

	# update the preview display if offset fields were changed	
	def keypressed(self,event=None):
		try:
			event.widget.selection_clear()
			event.widget.icursor(END)
			vals=[]
			for widget in [self.Xentry,self.Yentry,self.Zentry,self.Tentry]:
				v = widget.get() # get the content of all of the fields
				if event.widget == widget:
					# this callback function is called before the contents of the
					# entry field are modified, so you need to take the original
					# contents of the field and update them based on which key was pressed
					if event.char=='\b': v = v[:-1] # backspace was pressed
					else: v = v+event.char # append key to original contents
				if len(v)==0: v = '0.0'
				vals.append(float(v))
			self.DistributeCues(vals)
		except:
			self.DistributeCues([0.0,0.0,0.0,0.0])

	# distribute the cues in the preview window			
	def DistributeCues(self,offset):
		self.canvas.delete("cue")
		for y in range(2):
			for x in range(2):
				if self.type==0: # floors
					self.AddCue(x*self.PlatScale+offset[0],offset[1],y*self.PlatScale+offset[2],offset[3])
				elif self.type==1: #hallways
					if x==0: # horizontal
						self.AddCue(x*self.PlatScale+self.PlatScale/2.0+offset[0],offset[1],y*self.PlatScale+offset[2],270+offset[3])
					if y==0: # vertical
						self.AddCue(x*self.PlatScale-offset[2],offset[1],y*self.PlatScale+self.PlatScale/2.0+offset[0],offset[3])
				elif self.type==2: #walls
					if x==0: #left wall
						self.AddCue(x*self.PlatScale-self.scalewidth/2.0+offset[2],offset[1],y*self.PlatScale-offset[0],offset[3])
					else: # right wall
						self.AddCue(x*self.PlatScale+self.scalewidth/2.0-offset[2],offset[1],y*self.PlatScale+offset[0],180+offset[3])
					if y==0: #top wall
						self.AddCue(x*self.PlatScale+offset[0],offset[1],y*self.PlatScale-self.scalewidth/2.0+offset[2],90+offset[3])
					else: #bottom wall
						self.AddCue(x*self.PlatScale-offset[0],offset[1],y*self.PlatScale+self.scalewidth/2.0-offset[2],270+offset[3])

	# add a cue to the preview window						
	def AddCue(self,x,y,z,t):
		# calculate the vertices of the cue marker
		_x=self.offset+(x/self.PlatScale)*self.scale
		_z=self.offset+(z/self.PlatScale)*self.scale
		_t = t*pi/180
		x1 = _x+5*cos(_t)
		y1 = _z+5*sin(_t)
		x2 = _x+5*cos(_t+(2*pi/3))
		y2 = _z+5*sin(_t+(2*pi/3))
		x3 = _x
		y3 = _z
		x4 = _x+5*cos(_t+(4*pi/3))
		y4 = _z+5*sin(_t+(4*pi/3))		
		self.canvas.create_polygon(x1,y1,x2,y2,x3,y3,x4,y4,fill="green",outline="green",tags=("cue"))

	# make sure values are okay before closing		
	def validate(self):
		try:
			xoff = float(self.Xentry.get())
			yoff = float(self.Yentry.get())
			zoff = float(self.Zentry.get())
			toff = float(self.Tentry.get())
			self.result=[xoff,yoff,zoff,toff]
			return 1
		except ValueError:
			tkMessageBox.showwarning("Invalid Entry",
				"Please input a valid number.",
				parent=self)
			return 0

# Dialog used when distributing cues in the layout
class CueDistributionDialog(tkSimpleDialog.Dialog):
	def __init__(self, parent, cue_types,cue_ratios,floor_offsets,hall_offsets,wall_offsets,width,length):
		self.cuetypes=cue_types # a POINTER to the data of all the cue types
		self.cueratios=cue_ratios[:] # a COPY of the cue ratios
		self.flooroffs=floor_offsets[:] # a COPY of the floor offsets
		self.halloffs=hall_offsets[:] # a COPY of the hallway offsets
		self.walloffs=wall_offsets[:] # a COPY of the wall offsets
		self.removecues=1
		self.scalewidth = width
		self.scalelength = length
		title = "Visual Cue Distribution"
		tkSimpleDialog.Dialog.__init__(self,parent,title)
		
	def buttonbox(self):
		pass

	# define the dialog layout
	def body(self, master):
		b = Button(master, text="OK", width=15, command=self.ok, default=ACTIVE)
		b.grid(row=0,column=0,padx=5,pady=5,sticky=S)
		b = Button(master, text="Cancel", width=15, command=self.cancel)
		b.grid(row=1,column=0,padx=5,pady=5,sticky=N)
		self.removecuesvar = IntVar(); self.removecuesvar.set(1)
		Checkbutton(master,text='Remove existing cues',var=self.removecuesvar).grid(row=2,column=0)

		# cue list box
		Label(master,text="Cue Types and Ratios").grid(row=0,column=1,padx=5,sticky=S)
		frame = Frame(master)
		frame.grid(row=1,column=1,rowspan=10,padx=5,sticky=N)
		scrollbar = Scrollbar(frame, orient=VERTICAL)
		self.cuelistbox = Listbox(frame, bg="white",height=13,yscrollcommand=scrollbar.set)
		scrollbar.config(command=self.cuelistbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.cuelistbox.pack(side=LEFT, fill=BOTH, expand=1)
		b = Button(master, text="Add", width=8, command=self.AddCue)
		b.grid(row=5,column=1,padx=10,pady=3,sticky=SW)
		b = Button(master, text="Remove", width=8, command=self.RemoveCue)
		b.grid(row=5,column=1,padx=10,pady=3,sticky=SE)
		for (res,ratio) in self.cueratios:
			self.cuelistbox.insert(END,"%d%% - \"%s\""%(ratio,res[0]))

		# hall offsets
		Label(master,text="Hallway Offsets").grid(row=0,column=2,padx=5,sticky=S)
		frame = Frame(master)
		frame.grid(row=1,column=2,padx=5,sticky=N)
		scrollbar = Scrollbar(frame, orient=VERTICAL)
		self.halloffsetlistbox = Listbox(frame, bg="white",height=4,width=35,yscrollcommand=scrollbar.set)
		self.halloffsetlistbox.bind('<Double-Button-1>',self.halloffsetdblclk)
		scrollbar.config(command=self.halloffsetlistbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.halloffsetlistbox.pack(side=LEFT, fill=BOTH, expand=1)
		b = Button(master, text="Add", width=8, command=self.AddHallOffset)
		b.grid(row=1,column=3,padx=3,pady=3,sticky=N)
		b = Button(master, text="Remove", width=8, command=self.RemoveHallOffset)
		b.grid(row=1,column=3,padx=3,pady=3,sticky=S)
		for item in self.halloffs:
			self.halloffsetlistbox.insert(END,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(item[0],item[1],item[2],item[3]))

		# wall offsets
		Label(master,text="Wall Offsets").grid(row=2,column=2,padx=5,sticky=S)
		frame = Frame(master)
		frame.grid(row=3,column=2,padx=5,sticky=N)
		scrollbar = Scrollbar(frame, orient=VERTICAL)
		self.walloffsetlistbox = Listbox(frame, bg="white",height=4,width=35,yscrollcommand=scrollbar.set)
		self.walloffsetlistbox.bind('<Double-Button-1>',self.walloffsetdblclk)
		scrollbar.config(command=self.walloffsetlistbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.walloffsetlistbox.pack(side=LEFT, fill=BOTH, expand=1)
		b = Button(master, text="Add", width=8, command=self.AddWallOffset)
		b.grid(row=3,column=3,padx=3,pady=3,sticky=N)
		b = Button(master, text="Remove", width=8, command=self.RemoveWallOffset)
		b.grid(row=3,column=3,padx=3,pady=3,sticky=S)
		for item in self.walloffs:
			self.walloffsetlistbox.insert(END,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(item[0],item[1],item[2],item[3]))

		# floor offsets
		Label(master,text="Floor Offsets").grid(row=4,column=2,padx=5,sticky=S)
		frame = Frame(master)
		frame.grid(row=5,column=2,padx=5,sticky=N)
		scrollbar = Scrollbar(frame, orient=VERTICAL)
		self.flooroffsetlistbox = Listbox(frame, bg="white",height=4,width=35,yscrollcommand=scrollbar.set)
		self.flooroffsetlistbox.bind('<Double-Button-1>',self.flooroffsetdblclk)
		scrollbar.config(command=self.flooroffsetlistbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.flooroffsetlistbox.pack(side=LEFT, fill=BOTH, expand=1)
		b = Button(master, text="Add", width=8, command=self.AddFloorOffset)
		b.grid(row=5,column=3,padx=3,pady=3,sticky=N)
		b = Button(master, text="Remove", width=8, command=self.RemoveFloorOffset)
		b.grid(row=5,column=3,padx=3,pady=3,sticky=S)
		for item in self.flooroffs:
			self.flooroffsetlistbox.insert(END,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(item[0],item[1],item[2],item[3]))
				
		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)		
		
		return self # initial focus

	# hall offset listbox was double clicked, so edit that field	
	def halloffsetdblclk(self,event):
		item = self.halloffsetlistbox.curselection() # get selected item 
		try: item = map(int, item)
		except ValueError: pass
		if len(item)!=0:
			index = item[0]
			d = OffsetQueryDialog(self,"Hallway Offset",1,self.halloffs[index],self.scalewidth,self.scalelength)
			if d.result:
				# display new value in list box
				self.halloffs[index]=d.result
				self.halloffsetlistbox.delete(index)
				self.halloffsetlistbox.insert(index,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(d.result[0],d.result[1],d.result[2],d.result[3]))

	# wall offset listbox was double clicked, so edit the field				
	def walloffsetdblclk(self,event):
		item = self.walloffsetlistbox.curselection() # get selected item 
		try: item = map(int, item)
		except ValueError: pass
		if len(item)!=0:
			index = item[0]
			d = OffsetQueryDialog(self,"Wall Offset",2,self.walloffs[index],self.scalewidth,self.scalelength)
			if d.result:
				# display new value in list box
				self.walloffs[index]=d.result
				self.walloffsetlistbox.delete(index)
				self.walloffsetlistbox.insert(index,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(d.result[0],d.result[1],d.result[2],d.result[3]))

	# floor offset listbox was double clicked, so edit the field				
	def flooroffsetdblclk(self,event):
		item = self.flooroffsetlistbox.curselection() # get selected item
		try: item = map(int, item)
		except ValueError: pass
		if len(item)!=0:
			index = item[0]
			d = OffsetQueryDialog(self,"Floor Offset",0,self.flooroffs[index],self.scalewidth,self.scalelength)
			if d.result:
				# display new value in list box
				self.flooroffs[index]=d.result
				self.flooroffsetlistbox.delete(index)
				self.flooroffsetlistbox.insert(index,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(d.result[0],d.result[1],d.result[2],d.result[3]))

	# make sure values are okay before closing				
	def validate(self):
		total=0
		for (res,ratio) in self.cueratios:
			total = total + ratio
		if total > 100: # make sure ratios do not exceed 100
			tkMessageBox.showwarning("Invalid Ratios",
					"Ratios must add up to 100% or less.",parent=self)
			return 0	 
		return 1

	# return OK		
	def apply(self):
		self.removecues = self.removecuesvar.get()
		self.result='OK'

	# select a cue from the QuickList to add to the list of cues to be distributed		 
	def AddCue(self):
		d=VisualCueQuickList(self,self.cuetypes,2)
		if(d.result):
			self.cuelistbox.insert(END,"%.1f%% - \"%s\""%(d.ratio,d.result[0]))
			self.cueratios.append((d.result,d.ratio))

	# remove a cue from the distribution list			
	def RemoveCue(self):
		item = self.cuelistbox.curselection()
		try: item = map(int, item)
		except ValueError: pass
		if len(item)==0:
			tkMessageBox.showwarning("Invalid Selection",
					"Please select a cue type.",parent=self)
		else:
			self.cuelistbox.delete(item[0])
			self.cueratios.pop(item[0])

	# add a hallway offset			
	def AddHallOffset(self):
		d = OffsetQueryDialog(self,"Hallway Offset",1,[0.0,0.0,0.0,0.0],self.scalewidth,self.scalelength)
		if(d.result):
			self.halloffsetlistbox.insert(END,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(d.result[0],d.result[1],d.result[2],d.result[3]))
			self.halloffs.append(d.result)

	# remove a hallway offset			
	def RemoveHallOffset(self):
		item = self.halloffsetlistbox.curselection()
		try: item = map(int, item)
		except ValueError: pass
		if len(item)==0:
			tkMessageBox.showwarning("Invalid Selection",
					"Please select an offset.",parent=self)
		else:
			self.halloffsetlistbox.delete(item[0])
			self.halloffs.pop(item[0])

	# add a wall offset			
	def AddWallOffset(self):
		d = OffsetQueryDialog(self,"Wall Offset",2,[0.0,0.0,0.0,0.0],self.scalewidth,self.scalelength)
		if(d.result):
			self.walloffsetlistbox.insert(END,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(d.result[0],d.result[1],d.result[2],d.result[3]))
			self.walloffs.append(d.result)

	# remove a wall offset			
	def RemoveWallOffset(self):
		item = self.walloffsetlistbox.curselection()
		try: item = map(int, item)
		except ValueError: pass
		if len(item)==0:
			tkMessageBox.showwarning("Invalid Selection",
					"Please select an offset.",parent=self)
		else:
			self.walloffsetlistbox.delete(item[0])
			self.walloffs.pop(item[0])

	# add a floor offset			
	def AddFloorOffset(self):
		d = OffsetQueryDialog(self,"Floor Offset",0,[0.0,0.0,0.0,0.0],self.scalewidth,self.scalelength)
		if(d.result):
			self.flooroffsetlistbox.insert(END,"x: %.1f,  y: %.1f,  z: %.1f,  t: %.1f"%(d.result[0],d.result[1],d.result[2],d.result[3]))
			self.flooroffs.append(d.result)

	# remove a floor offset			
	def RemoveFloorOffset(self):
		item = self.flooroffsetlistbox.curselection()
		try: item = map(int, item)
		except ValueError: pass
		if len(item)==0:
			tkMessageBox.showwarning("Invalid Selection",
					"Please select an offset.",parent=self)
		else:
			self.flooroffsetlistbox.delete(item[0])
			self.flooroffs.pop(item[0])		

if __name__=='__main__':
	import sys
	try:
		sys.argv[0]
	except:
		sys.argv=['LayoutMaker.py']
	root = Tk()
	LM = LayoutMaker(root)
	root.mainloop()