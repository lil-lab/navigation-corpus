# DrawMap.py
# $Revision: 1.1.1.1 $
# $Date: 2005/09/01 19:41:34 $

from Tkinter import *
import tkFileDialog,tkSimpleDialog,tkMessageBox
import random,string,sys,time,re,os
from math import *
from Navigator import *

# 1 if plat1 == plat2, 0 otherwise
def PlatEq(plat1,plat2):
	for y in range(max([plat1.y,plat2.y])):
		for x in range(max([plat1.x,plat2.x])):
			isChosen1 = (x,y) in plat1.ChosenList
			isChosen2 = (x,y) in plat2.ChosenList
			if isChosen1 ^ isChosen2: return 0 #(x,y) is in one chosen list, but not the other
			elif isChosen1 and isChosen2:
				# (x,y) is in both chosen lists, so make sure they have the same set of links
				for link in plat1.Nodes[x][y].Linked:
					if link not in plat2.Nodes[x][y].Linked: return 0
				for link in plat2.Nodes[x][y].Linked:
					if link not in plat1.Nodes[x][y].Linked: return 0
	return 1

class DrawMap:
	def __init__(self,master,layoutfile=None,outfile=None):
		master.title("Draw Map")
		self.master = master

		# display the buttons and text for the layout and output file name fields
		f1 = Frame(master,bd=3, relief=GROOVE)
		f1.grid(row=0,column=0,padx=5,pady=5,sticky=W)
		# the 'Open Layout' button to select the layout file name
		layoutbutton = Button(f1,text="Open Layout",command = self.SetLayoutFilenames,width=12)
		layoutbutton.grid(row=0,column=0,padx=5,pady=3)
		# self.l_filename is the label that displays the layout file name
		self.l_filename = Label(f1,width=68,text="Please select a layout",anchor=W)
		self.l_filename.grid(row=0,column=1,padx=5,pady=3)
		# the 'Out File' button to select the output file name
		outbutton = Button(f1,text="Out File",command = self.SetOutputFilenames,width=12)
		outbutton.grid(row=1,column=0,padx=5,pady=3)
		# self.o_filename is the label that displays the output file name
		self.o_filename = Label(f1,width=68,text="Please select an output file",anchor=W)
		self.o_filename.grid(row=1,column=1,padx=5,pady=3)

		# some brief instructions for using the program:
		f2 = Frame(master, bd=3, relief=GROOVE)
		f2.grid(row=1,column=0,padx=5,pady=5,sticky=W)        
		Label(f2,text='* Double left-click to draw a wall * Left-click and drag to select walls *\n* Right-click to add/remove hot-spots * Press the "Delete" key to delete walls *\n* Press the "Enter" key or the "Save Data" button to save the drawing *').grid(row=0,column=0)

		# the 'Save Data' button        
		self.savebutton = Button(master,text="Save Data",command = self.ExportLayout,state=DISABLED,width=12)
		self.savebutton.grid(row=1,column=0,padx=5,pady=3,sticky=E)
		
		# set up the canvas, and bind events
		f3 = Frame(master, bd=3, relief=GROOVE)
		f3.grid(row=2,column=0,columnspan=3,padx=5,pady=5)
		self.canvas = Canvas(f3,width=600,height=600,background="Black")
		self.canvas.grid(row=0)
		self.canvas.bind("<Button-1>",self.CanvasClickCallback) # left click on the canvas
		self.canvas.bind("<Button-3>",self.CanvasRightClickCallback) # right click on the canvas
		self.canvas.bind("<Double-Button-1>",self.CanvasDblClickCallback) # double left click
		self.canvas.bind("<Motion>",self.CanvasMotionCallback) # mouse moves over canvas
		self.canvas.bind("<B1-Motion>",self.CanvasB1MotionCallback) # mouse moved while holding left button
		self.canvas.bind("<ButtonRelease-1>",self.CanvasB1ReleaseCallback) # left button released
		self.master.bind("<Delete>",self.DeleteStructure) # delete key pressed 
		self.master.bind("<Return>",self.ExportLayout) # enter key pressed 
		
		self.platObject = 0 # PLAT object of the drawing
		self.makewallfrom = None # starting location of walls to be drawn
		self.makewallto = None # ending location of walls to be drawn
		self.outfilename = None # outfile where drawn map is written
		self.layoutfilename = None # name of text map file
		self.targetmaphotspots = [] # list of hotspots in layout
		self.success = None

		# check to see if default layout and output file names
		# were provided as arguments to the program	   
		if layoutfile:
			self.SetLayoutFilenames(layoutfile)
		if outfile:
			self.SetOutputFilenames(outfile)
			

	# Export Layout is called when the 'Save Data' button or the 'Enter' key is pressed 
	def ExportLayout(self,event=None):
		# don't try saving data if there's no platObject, etc.
		if(self.platObject==0 or self.layoutfilename==None or self.outfilename==None): return
		try:
			filename = self.outfilename
			
			# collect hotspots marked in drawing
			hotspots = []
			for hs in self.canvas.find_withtag("hotspot"):
				num = 0
				coords = [0,0]
				tags = self.canvas.gettags(hs)
				for tag in tags:
					if tag[0:3]=="num":
						num = int(tag[4:])  # hotspot id #
					elif tag[0:6]=="coords":
						splittag = tag.split()
						coords = (int(splittag[1]),int(splittag[2])) # location of hotspot
				hotspots.append((num,coords))
			hotspots.sort() # sort hotspots according to id #
			hotspotsokay = (map(lambda (a,b):b,hotspots) == self.targetmaphotspots) # compare subject's hotspots with correct hotspots list
			
			width,height,size = getPlatDim(self.layoutfilename)
			platObj=PLAT(width,height,size)
			platObj.ReadTextImage(self.layoutfilename) # platObj contains the correct layout design
			FILEHANDLE = open(filename,'a')
			FILEHANDLE.write('\n/--------------------------------------------\n')
			FILEHANDLE.write("| %s\n" % time.strftime("Date:%x Time:%X",time.localtime(time.time())))
			if hotspotsokay and PlatEq(self.platObject,platObj):  # success iff layout and hotspots are both correct
				FILEHANDLE.write('| Score: SUCCESS\n')
				success = 1
			else:
				FILEHANDLE.write('| Score: FAILURE\n')
				success = 0
			FILEHANDLE.write('| Original Hotspots: ')
			num = 1
			for (xpos,ypos) in self.targetmaphotspots:
				FILEHANDLE.write('%d: %d,%d; '%(num,xpos,ypos))
				num += 1
			FILEHANDLE.write('\n| Marked Hotspots: ')
			for (num,(xpos,ypos)) in hotspots:
				FILEHANDLE.write('%d: %d,%d; '%(num,xpos,ypos))
			FILEHANDLE.write('\n| Original Layout (%s):\n'%self.layoutfilename)
			platObj.DisplayTextImage(FILEHANDLE)
			FILEHANDLE.write("\n| Map Drawn:\n")			
			self.platObject.DisplayTextImage(FILEHANDLE)
			FILEHANDLE.write('\n\\--------------------------------------------\n')
			FILEHANDLE.close()
			if success:
				tkMessageBox.showinfo("Correct","Map drawn successfully!")
				self.success = 1
			else:
				tkMessageBox.showerror("Incorrect","Map drawn INCORRECTLY!")
				self.success = 0
			self.master.destroy()
		except Exception, e:
			print e
			tkMessageBox.showerror("Export Error","Error when trying to export:\n%s" % (filename))

	# This function is called when the 'Open Layout' button is pressed, or
	# when a layout filename is provided as an argument to the program.
	# Draws the reduced starting map specified by '<filename>.start'
	# Also reads in the hotspots associated with the layout (.poi file)
	def SetLayoutFilenames(self,filename=None):
		if filename==None: # open a browse-filenames dialog to get 'filename' if necessary
			filename = tkFileDialog.askopenfilename(filetypes=[("Text Map",'*.txt'),("All files",'*.*')])
		if filename: # Make sure user didn't press cancel in browse dialog
			try:
				width,height,size = getPlatDim(filename)
				self.platObject=PLAT(width,height,size) # create PLAT object large enough for layout
				self.platObject.ReadTextImage(filename)
				self.layoutfilename = filename	
				self.DisplayTextMap() #draw the starting layout
				try: # try to read in layout's hotspots
					self.targetmaphotspots = []
					# the following regex removes the extension from filename (usually '.txt')
					# and then appends the '.poi' extension to look for the hotspots file.
					HSFILE = open(re.match("(.*)\..*",filename).group(1)+'.poi','r')
					for line in HSFILE.readlines():
						# get the x,y coordinates of each hotspot
						splitline = string.split(line,'|')
						self.targetmaphotspots.append((int(float(splitline[0])),int(float(splitline[1]))))
					HSFILE.close()
				except:
					# failed somewhere, so just keep the hotspots list empty
					self.targetmaphotspots = []

				# the following code truncates a path if it is too long to fit in the display field
				#  for example: 'C:/.../Layout/Layout.txt'
				if len(filename) >= 64:
					f = filename.split('/')
					if len(f)>2:
						while len(f)>2 and len(string.join(f,'/'))>64: f.pop(1)
						if len(f)>=2:
							filename = f[0]+'/.../'+string.join(f[1:],'/')
				# display the truncated filename
				self.l_filename.config(text=filename)
				if self.outfilename!=None:
					# activate the 'Save Data' button only if the layout and output files have both been specified
					self.savebutton.config(state=ACTIVE)
				return 1
			except Exception, e:
				# an error occurred somewhere; re-initialize variables just to be safe
				print 'DrawMap Error:',e
				self.canvas.delete(ALL)
				self.platObject=0
				self.targetmaphotspots = []
				self.layoutfilename = None
				self.savebutton.config(state=DISABLED)
				self.l_filename.config(text="Please select a layout")
				tkMessageBox.showwarning("Invalid Layout File","An error occurred while trying to load this layout file:\n\n%s\n\n(Make sure that \"%s.start\" is valid)" % (filename,filename))
				return 0

	# This function is called when the 'Out File' button is pressed, or
	# when an output filename is provided as an argument to the program.
	# (Doesn't do much more than display the filename)
	def SetOutputFilenames(self,filename=None):
		if filename==None: # open a browse-filenames dialog to get 'filename' if necessary
			filename = tkFileDialog.asksaveasfilename(filetypes=[("All files",'*.*')])
		if filename:
			try:
				self.outfilename = filename
				# the following code truncates a path if it is too long to fit in the display field
				#  for example: 'C:/.../Layout/Layout.out'
				if len(filename) >= 64:
					f = filename.split('/')
					if len(f)>2:
						while len(f)>2 and len(string.join(f,'/'))>64: f.pop(1)
						if len(f)>=2:
							filename = f[0]+'/.../'+string.join(f[1:],'/')
				self.o_filename.config(text=filename)
				if self.layoutfilename!=None:
					# activate the 'Save Data' button only if the layout and output files have both been specified
					self.savebutton.config(state=ACTIVE)
				return 1
			except Exception, e:
				# error occurred; re-init variables
				print "DrawMap Error:",e
				self.outfilename = None
				self.savebutton.config(state=DISABLED)
				self.o_filename.config(text="Please select an output file")
				tkMessageBox.showwarning("Invalid Output File","An error occurred while trying to access this file:\n\n%s" % filename)
				return 0

	# display the map in the canvas		
	def DisplayTextMap(self):
		if(self.platObject==0): return				
		self.canvas.delete(ALL)

		# find dimensions of map to zoom in
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
		midx = (maxx+minx)/2.0 # center points
		midy = (maxy+miny)/2.0
		farthest = max([(midx-minx),(midy-miny)]) # radius from center
		self.scale = scale = 200/farthest # distance in canvas coords from one node to another
		xoffset = 300-midx*scale # x,y offsets to keep image centered,
		yoffset = 300-midy*scale #  e.g. offset+(PLAT-coord)*scale = upper left corner of node square (in canvas coords)
		self.width = width = scale/4 # width of a node in canvas coords
		self.xoffset = xoffset+self.width/2 # offset to get center of node (rather than upper left corner)
		self.yoffset = yoffset+self.width/2

		#don't want to draw the actual .txt map, so now read in the .txt.start map
		fname = self.layoutfilename+'.start'		
		w,h,s = getPlatDim(fname)
		self.platObject=PLAT(w,h,s)
		self.platObject.ReadTextImage(fname)

		# draw the .txt.start map
		for y in range(self.platObject.y):
			for x in range(self.platObject.x):
				if (x,y) in self.platObject.ChosenList:
					# a floor
					self.canvas.create_rectangle(xoffset+x*scale,yoffset+y*scale,xoffset+x*scale+width,yoffset+y*scale+width,fill="black",outline="red",tags=("floor",('coords',x,y)))
					if (x+1,y) in self.platObject.Nodes[x][y].Linked or ((x+1<self.platObject.x) and (x,y) in self.platObject.Nodes[x+1][y].Linked):
						# a horizontal hallway
						self.canvas.create_rectangle(xoffset+x*scale+width+1,yoffset+y*scale,xoffset+(x+1)*scale-1,yoffset+y*scale+width,fill="red",outline="red",tags=("hallway",('coords',x,y,x+1,y)))
					if (x,y+1) in self.platObject.Nodes[x][y].Linked or ((y+1<self.platObject.y) and (x,y) in self.platObject.Nodes[x][y+1].Linked):
						# a vertical hallway
						self.canvas.create_rectangle(xoffset+x*scale,yoffset+y*scale+width+1,xoffset+x*scale+width,yoffset+(y+1)*scale-1,fill="red",outline="red",tags=("hallway",('coords',x,y,x,y+1)))

		# starting state (x,y,theta) line marked by '@'
		regex = re.compile("^\s*@[ \t]*(\d+)[ \t]+(\d+)[ \t]+(\d+)",re.MULTILINE)
		FILE = open(fname,'r')
		m = re.search(regex,FILE.read())
		FILE.close()
		if m != None:
			# if starting state given, then draw a gray triangle marking the location
			params = map(string.atoi,[m.group(1),m.group(2),m.group(3)]) #m.group 1,2 and 3 are the three integers (in parentheses) specified in the regex above
			# calculate the three points for the triangle
			# lambda expressions don't have access to the local variables in a function,
			#  so you must pass default variable values (i.e. p0,p1,and w) to the lambda expression
			tricoords = map(lambda t,p0=xoffset+params[0]*scale+width/2,p1=yoffset+params[1]*scale+width/2,w=width: (w/2*cos(t*pi/180)+p0,w/2*sin(t*pi/180)+p1),[-90+params[2],50+params[2],130+params[2]])
			self.canvas.create_polygon(tricoords,fill="gray",outline="gray",tags=("start"))
		
		# bind events to various objects in the canvas
		self.canvas.tag_bind("floor","<Button-1>",self.FloorCallback)
		self.canvas.tag_bind("floor","<Button-3>",self.FloorRightClkCallback)
		self.canvas.tag_bind("start","<Button-3>",self.FloorRightClkCallback)
		self.canvas.tag_bind("hallway_h","<Button-1>",self.H_WallCallback)
		self.canvas.tag_bind("hallway_v","<Button-1>",self.V_WallCallback)

	# delete a highlighted structure		
	def DeleteStructure(self,event=None):
		if(self.platObject==0): return
		for item in self.canvas.find_withtag('highlight'): # go through each high-lighted item
			tags = self.canvas.gettags(item)
			if "hallway_h" in tags or "hallway_v" in tags: # if item is a hallway
				pts = None
				for tag in tags:
					if string.find(tag,'coords') != -1:
						pts = map(int,tag.split()[1:])  # get the coordinates of the hallway
						break
				if pts:
					# remove links in the PLAT object to remove the wall
					if (pts[2],pts[3]) in self.platObject.Nodes[pts[0]][pts[1]].Linked:
						self.platObject.Nodes[pts[0]][pts[1]].Linked.remove((pts[2],pts[3]))
					if (pts[0],pts[1]) in self.platObject.Nodes[pts[2]][pts[3]].Linked:
						self.platObject.Nodes[pts[2]][pts[3]].Linked.remove((pts[0],pts[1]))
				self.canvas.delete(item) #delete the hall from the canvas
			elif "floor" in tags:
				# if the item is a node, remove any hotspots from it, but don't delete the node yet!
				x,y = self.getItemPlatCoords(item)
				for i in self.canvas.find_withtag(("coords",x,y)):
					tags = self.canvas.gettags(i)
					if ("hotspot") in tags:
						self.canvas.delete(i)
		for item in self.canvas.find_withtag('floor'):
			# now that links have been removed from the PLAT object,
			#   remove any floors (nodes) that aren't linked to anything.
			#   (By doing the deletion in two steps like this, you make sure that no nodes are an island,
			#    and that no nodes are deleted if they are still linked with other nodes)
			x,y = self.getItemPlatCoords(item)
			if len(self.platObject.Nodes[x][y].Linked) == 0 and (x==0 or (x,y) not in self.platObject.Nodes[x-1][y].Linked) and (y==0 or (x,y) not in self.platObject.Nodes[x][y-1].Linked) and (x==self.platObject.x-1 or (x,y) not in self.platObject.Nodes[x+1][y].Linked) and (y==self.platObject.y-1 or (x,y) not in self.platObject.Nodes[x][y+1].Linked):
				self.platObject.Nodes[x][y].active=0
				self.platObject.ChosenList.remove((x,y))
				self.currentitem = None
				self.canvas.delete(item)
				for i in self.canvas.find_withtag(("coords",x,y)):
					tags = self.canvas.gettags(i)
					if ("hotspot") in tags:
						self.canvas.delete(i)
		self.UnHighlight()
		
	# draw a hallway from self.makewallfrom to self.makewallto  
	def MakeWall(self):
		if(self.platObject==0): return
		# self.makewallfrom and self.makewallto are objects in the canvas,
		# so get their PLAT coordinates
		px1,py1 = self.getItemPlatCoords(self.makewallfrom)
		px2,py2 = self.getItemPlatCoords(self.makewallto)
		
		if px1==px2 and py1==py2:
			# the hallway specified is only a point, so dont make anything
			self.CanvasRightClickCallback(None)
			return
		
		xoffset = self.xoffset-self.width/2
		yoffset = self.yoffset-self.width/2
		xlow = min(px1,px2)
		xhi = max(px1,px2)
		ylow = min(py1,py2)
		yhi = max(py1,py2)

		# add the end points to the PLAT if they aren't in the ChosenList yet
		if (xlow,ylow) not in self.platObject.ChosenList:
			self.platObject.ChosenList.append((xlow,ylow))
			self.platObject.Nodes[xlow][ylow].active = 1
		if (xhi,yhi) not in self.platObject.ChosenList:
			self.platObject.ChosenList.append((xhi,yhi))
			self.platObject.Nodes[xhi][yhi].active = 1

		# drawing a vertical hallway
		if px1==px2:
			x = px1
			for y in range(ylow,yhi): # connect the dots
				if (x,y) not in self.platObject.ChosenList:
					# add the point if it isnt in the ChosenList
					self.platObject.ChosenList.append((x,y))
					self.platObject.Nodes[x][y].active = 1
					# draw the node on the canvas
					self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
				if not ((x,y+1) in self.platObject.Nodes[x][y].Linked or ((y+1<self.platObject.y) and (x,y) in self.platObject.Nodes[x][y+1].Linked)):
					# add the link if it isnt already there
					self.platObject.Nodes[x][y].Linked.append((x,y+1))
					self.platObject.Nodes[x][y+1].Linked.append((x,y))
					# draw the hallway on the canvas
					self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale+self.width+1,xoffset+x*self.scale+self.width,yoffset+(y+1)*self.scale-1,fill="red",outline="red",tags=("hallway_v",('coords',x,y,x,y+1)))
		# drawing a horizontal hallway
		elif py1==py2:
			y = py1
			for x in range(xlow,xhi): # connect the dots
				if (x,y) not in self.platObject.ChosenList:
					# add the point if it isnt in the ChosenList
					self.platObject.ChosenList.append((x,y))
					self.platObject.Nodes[x][y].active = 1
					# draw the node on the canvas
					self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
				if not ((x+1,y) in self.platObject.Nodes[x][y].Linked or ((x+1<self.platObject.x) and (x,y) in self.platObject.Nodes[x+1][y].Linked)):
					# add the link if it isnt already there
					self.platObject.Nodes[x][y].Linked.append((x+1,y))
					self.platObject.Nodes[x+1][y].Linked.append((x,y))
					# draw the hallway on the canvas
					self.canvas.create_rectangle(xoffset+x*self.scale+self.width+1,yoffset+y*self.scale,xoffset+(x+1)*self.scale-1,yoffset+y*self.scale+self.width,fill="red",outline="red",tags=("hallway_h",('coords',x,y,x+1,y)))

	# given PLAT coords, return canvas coordinates
	def PlatToCanvas(self,x,y):
		return ((self.xoffset+x*self.scale),(self.yoffset+y*self.scale))
	# given canvas coords, return PLAT coordinates
	def canvasToPlat(self,x,y):
		return (int(round((x-self.xoffset)/self.scale)),int(round((y-self.yoffset)/self.scale)))
	# return the PLAT coords of an item (coords must be specified in the item's tag)
	def getItemPlatCoords(self,item):
		for tag in self.canvas.gettags(item):
			if string.find(tag,'coords') != -1:
				t = tag.split()
				return (int(t[1]),int(t[2]))
	
	# left button held down while cursor moved.
	# -draw a selection box
	def CanvasB1MotionCallback(self,event):
		items=self.canvas.find_withtag("select-box")
		if len(items) == 0:
			# selection box doesnt exist yet, so draw one
			self.UnHighlight()
			item = self.canvas.create_rectangle(event.x,event.y,event.x,event.y,outline="yellow",tags=("select-box",("coords",event.x,event.y)))
		else: item = items[0] #selection box exists, so save it as item

		# get the coords of the selection box
		# (this is just the point where the mouse was first clicked 
		#  on the canvas when making the box, not all of the coords of the rectangle)
		for tag in self.canvas.gettags(item):
			if string.find(tag,'coords') != -1:
				break
		t = tag.split()
		x = t[1] # x value of starting point of box
		y = t[2] # y value of starting point of box

		# need to compare starting point of box with current mouse position to draw box correctly		
		xlow = min(x,event.x)
		xhi = max(x,event.x)
		ylow = min(y,event.y)
		yhi = max(y,event.y)
		self.canvas.coords(item,xlow,ylow,xhi,yhi) # modify the select-box's coordinates on the canvas

	# left mouse button was released
	#  -highlight items in select box if it exists
	def CanvasB1ReleaseCallback(self,event):
		items=self.canvas.find_withtag("select-box")
		if len(items)!=0:
			item = items[0]
			(x1,y1,x2,y2) = self.canvas.coords(item)
			items = self.canvas.find_enclosed(x1, y1, x2, y2) # all of the items enclosed by the select-box
			if len(items)>0:
				for i in items:
					tags = self.canvas.gettags(i)
					if "floor" in tags or "hallway_h" in tags or "hallway_v" in tags:
						newtags = tags + ('highlight',) # add highlight tag to i
						self.canvas.itemconfig(i,outline="yellow",tags = newtags) # highlight i
			self.canvas.delete("select-box") # delete the select-box
	
	# mouse has moved over the canvas
	#  -if making a wall, redraw the line to show where the wall will be made
	def CanvasMotionCallback(self,event):
		if self.makewallfrom:
			px1,py1 = self.getItemPlatCoords(self.makewallfrom)			
			px2,py2 = self.canvasToPlat(event.x,event.y)
			if px1==px2 or py1==py2:
				line = self.canvas.find_withtag('line')[0]
				x1,y1 = self.PlatToCanvas(px1,py1)
				x2,y2 = self.PlatToCanvas(px2,py2)
				if x2 > 0 and x2 < 600 and y2 > 0 and y2 < 600: #make sure the line is in bounds before drawing it
					self.canvas.coords(line,x1,y1,x2,y2)

	# left button clicked on canvas
	#  -if drawing hall, make it
	def CanvasClickCallback(self,event):
		if(self.platObject==0): return
		if self.makewallfrom:
			line = self.canvas.find_withtag('line')[0]
			(x0,y0,x1,y1) = self.canvas.coords(line)
			x,y = self.canvasToPlat(x1,y1)
			
			####### temporary fix ##########
			# dont draw hallways that would go out of the PLAT's bounds
			if x<0 or y<0 or x>=self.platObject.x or y>= self.platObject.y:
				tkMessageBox.showwarning("ERROR","Out of Range",parent=self.master)
				self.CanvasRightClickCallback(None)
				return
			################################

			# remove the line used to mark where the wall will be built			
			self.canvas.delete('line')
			xoffset = self.xoffset-self.width/2
			yoffset = self.yoffset-self.width/2
			for item in self.canvas.find_withtag(('coords',x,y)):
				# if ending point of the wall is an existing floor, then make wall to there 
				if "floor" in self.canvas.gettags(item):
					self.makewallto = item
					break
			if not self.makewallto:
				# no self.makewallto, so make it
				self.makewallto = self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
			self.MakeWall() # make the hallway
			self.makewallfrom=None
			self.makewallto=None

	# right mouse click on canvas
	# -cancel make wall actions
	# -unhighlight items
	# -call floor's right click callback (for hotspots)
	def CanvasRightClickCallback(self,event):
		if(self.platObject==0): return
		if self.makewallfrom:
			(x,y) = self.getItemPlatCoords(self.makewallfrom)
			if (x,y) not in self.platObject.ChosenList:
				self.canvas.delete(self.makewallfrom)				
			self.makewallfrom=None
			self.makewallto=None
			self.canvas.delete('line')
		if len(self.canvas.find_withtag(CURRENT))==0:
			self.UnHighlight()
		elif "hotspot" in self.canvas.gettags(CURRENT):
			self.FloorRightClkCallback(event)

	# left double click on canvas, start making wall
	def CanvasDblClickCallback(self,event):
		if(self.platObject==0): return
		self.canvas.delete('line')
		x,y = self.canvasToPlat(event.x,event.y)

		####### temporary fix ##########
		# dont draw a wall if it goes out of the PLAT's bounds
		if x<0 or y<0 or x>=self.platObject.x or y>= self.platObject.y:
			tkMessageBox.showwarning("ERROR","Out of Range",parent=self.master)
			return
		################################
		
		xoffset = self.xoffset-self.width/2
		yoffset = self.yoffset-self.width/2
		for item in self.canvas.find_withtag(('coords',x,y)):
			if "floor" in self.canvas.gettags(item):
				# if making wall from an existing floor
				self.makewallfrom = item
				(x0,y0,x1,y1)=self.canvas.coords(item)
				self.Highlight(self.makewallfrom)
				self.canvas.create_line((x0+x1)/2,(y0+y1)/2,(x0+x1)/2,(y0+y1)/2,fill="yellow",tags=('line'))
				return
		# no existing floor, make our own
		item = self.canvas.create_rectangle(xoffset+x*self.scale,yoffset+y*self.scale,xoffset+x*self.scale+self.width,yoffset+y*self.scale+self.width,fill="black",outline="red",tags=("floor",('coords',x,y)))
		self.makewallfrom = item
		self.Highlight(self.makewallfrom)
		(x0,y0,x1,y1)=self.canvas.coords(item)
		self.canvas.create_line((x0+x1)/2,(y0+y1)/2,(x0+x1)/2,(y0+y1)/2,fill="yellow",tags=('line'))

	# left click on floor, highlight it	   
	def FloorCallback(self,event):
		self.Highlight()
	# left click on horizontal wall, highlight it
	def H_WallCallback(self,event):
		self.Highlight()
	# left click on vertical wall, highlight it
	def V_WallCallback(self,event):
		self.Highlight()
	# unhighlight all items in the canvas
	def UnHighlight(self):
		for item in self.canvas.find_withtag("highlight"):
			self.canvas.dtag(item,"highlight")
			self.canvas.itemconfig(item,outline="red")
	# highlight h_item if was passed to this function, otherwise highlight CURRENT item 
	#  (CURRENT is item involved in most recent callback)
	def Highlight(self,h_item=None):
		if h_item==None:
			h_item = self.canvas.find_withtag(CURRENT)[0]
		self.UnHighlight()
		newtags = self.canvas.gettags(h_item) + ('highlight',)
		self.canvas.itemconfig(h_item,outline="yellow",tags = newtags)

	# right click on floor, handle hotspots
	def FloorRightClkCallback(self,event):
		hashotspot = 0
		self.currentitem = None
		x,y = self.canvasToPlat(event.x,event.y)
		for item in self.canvas.find_withtag(('coords',x,y)):
			if "floor" in self.canvas.gettags(item):
				self.currentitem = item # the floor that was clicked
			elif "hotspot" in self.canvas.gettags(item):
				hashotspot = 1 # the floor has a hotspot already
		if not self.currentitem:
			return
		self.Highlight(self.currentitem) # highlight the floor
		menu = Menu(self.master, tearoff=0) # menu for hotspots option
		self.hotspotvar = IntVar() # used to save the value of the hotspot selected in menu
		if not hashotspot:
			# show menu for adding hotspots
			for hs in range(1,len(self.targetmaphotspots)+1):
				if len(self.canvas.find_withtag(("num",hs)))==0:
					menu.add_radiobutton(label="Hotspot %d"%hs,variable=self.hotspotvar,value=hs,command=self.AddHotspot)
		else:
			# show menu for removing hotspots
			menu.add_command(label="Remove Hotspot", command=self.RemoveHotspot)
		menu.post(event.x_root, event.y_root)
		
	# remove hotspot from self.currentitem 
	def RemoveHotspot(self):
		x,y = self.getItemPlatCoords(self.currentitem)
		for item in self.canvas.find_withtag(("coords",x,y)):
			tags = self.canvas.gettags(item)
			if ("hotspot") in tags:
				self.canvas.delete(item)
	# add hotspot to self.currentitem 
	def AddHotspot(self):
		hotspot=self.hotspotvar.get()
		item = self.currentitem
		platcoords = self.getItemPlatCoords(item)
		canvascoords = self.PlatToCanvas(platcoords[0],platcoords[1])
		item = self.canvas.create_text(canvascoords[0],canvascoords[1],text=hotspot,fill="white",tags=(("hotspot"),("num",hotspot),("coords",platcoords[0],platcoords[1])))

# call Execute from another python program to display the GUI
def Execute(LayoutFileName, OutputFileName):
	"""Returns 1 if drawing was successful, 0 otherwise"""
	sys.argv = ['DrawMap.py']
	root = Tk()
	root.focus_force()
	DM = DrawMap(root,LayoutFileName,OutputFileName)
	root.mainloop()
	if DM.success:
		return 1
	else:
		return 0

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.1.1.1 $')
	if m:
		return m.group(1)
	else:
		return None    