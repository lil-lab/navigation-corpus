# ChooseState.py
# $Revision: 1.2 $
# $Date: 2006/09/12 22:54:16 $

from Tkinter import *
import tkFileDialog
import tkSimpleDialog
import tkMessageBox
import sys
from Navigator import *

class ChooseState:
	def __init__(self,master,layoutfile=None,outfile=None):
		master.title("Select Current State")
		self.master = master
		
		# set up the widgets on the GUI
		
		# filename frame
		f1 = Frame(master,bd=3, relief=GROOVE)
		f1.grid(row=0,column=0,padx=5,pady=5,sticky=W)
		layoutbutton = Button(f1,text="Open Layout",command = self.SetLayoutFilenames,width=12)
		layoutbutton.grid(row=0,column=0,padx=5,pady=3)  
		self.l_filename = Label(f1,width=68,text="Please select a layout",anchor=W)
		self.l_filename.grid(row=0,column=1,padx=5,pady=3)
		outfilebutton = Button(f1,text="Open OutFile",command = self.SetOutFilenames,width=12)
		outfilebutton.grid(row=1,column=0,padx=5,pady=3)  
		self.o_filename = Label(f1,width=68,text="Please select an outfile",anchor=W)
		self.o_filename.grid(row=1,column=1,padx=5,pady=3)

		# Save Data Frame
		f2 = Frame(master, bd=3, relief=GROOVE)
		f2.grid(row=1,column=0,padx=5,pady=5)
		self.savebutton = Button(f2,text="Save Data",command = self.SaveData,state=DISABLED,width=12)
		self.savebutton.grid(row=0,column=0,padx=15,pady=10)
		Button(f2,text="Clear",command = self.ClearChoices,width=12).grid(row=0,column=1,padx=15,pady=10)

		# canvas frame		
		f3 = Frame(master, bd=3, relief=GROOVE)
		f3.grid(row=2,column=0,columnspan=3,padx=5,pady=5)
		self.canvas = Canvas(f3,width=600,height=600,background="Black")
		self.canvas.grid(row=0)
		self.canvas.bind("<B1-Motion>",self.CanvasB1MotionCallback)
		self.canvas.bind("<ButtonRelease-1>",self.CanvasB1ReleaseCallback)
		self.platObject = 0
		self.layoutfilename = None
		self.outfilename = None
		self.master.bind('<Return>',self.SaveData)
		self.statevector = None

		# load layout file
		if layoutfile:
			self.SetLayoutFilenames(layoutfile)
		if outfile:
			self.SetOutFilenames(outfile)

	# choose a layout filename, load the layout		
	def SetLayoutFilenames(self,filename=None):
		if filename==None:
			# display browse files dialog if filename not given
			filename = tkFileDialog.askopenfilename(filetypes=[("Text Map",'*.txt'),("All files",'*.*')])
		if filename:
			try:
				_w,_h,_s = getPlatDim(filename)
				self.platObject=PLAT(_w,_h,_s)
				self.platObject.ReadTextImage(filename)
				self.DisplayTextMap() # display the layout in the canvas
				self.layoutfilename = filename
				if len(filename) >= 64:
					# truncate the file name so it fits in the field 
					f = filename.split('/')
					if len(f)>2:
						while len(f)>2 and len(string.join(f,'/'))>64: f.pop(1)
						if len(f)>=2:
							filename = f[0]+'/.../'+string.join(f[1:],'/')
				self.l_filename.config(text=filename)
				self.savebutton.config(state=ACTIVE)
				return 1
			except:
				# problem with the given layout file
				self.canvas.delete(ALL)
				self.layoutfilename = None
				self.savebutton.config(state=DISABLED)
				self.l_filename.config(text="Please select a layout")
				tkMessageBox.showwarning("Invalid Layout File","An error occurred while trying to load this layout file:\n\n%s" % filename)
				return 0
				
	# choose a layout filename, load the layout		
	def SetOutFilenames(self,filename=None):
		if filename==None:
			# display browse files dialog if filename not given
			filename = tkFileDialog.asksaveasfilename(filetypes=[("All files",'*.*')])
		if filename:
			self.outfilename = filename
			if len(filename) >= 64:
				# truncate the file name so it fits in the field 
				f = filename.split('/')
				if len(f)>2:
					while len(f)>2 and len(string.join(f,'/'))>64: f.pop(1)
					if len(f)>=2:
						filename = f[0]+'/.../'+string.join(f[1:],'/')
			self.o_filename.config(text=filename)
			return 1

	# show the map in the canvas				  
	def DisplayTextMap(self):
		if(self.platObject==0): return				
		self.canvas.delete(ALL)

		# get dimensions to zoom in 
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
		self.scale = scale = min(200, 200/farthest) # distance in canvas coords from one node to another
		xoffset = 300-midx*scale # x,y offsets to keep image centered,
		yoffset = 300-midy*scale #  e.g. offset+(PLAT-coord)*scale = upper left corner of node square (in canvas coords)
		self.width = width=scale/4 # width of a node in canvas coords
		self.xoffset = xoffset+self.width/2 # offset to get center of node (rather than upper left corner)
		self.yoffset = yoffset+self.width/2
		for y in range(self.platObject.y):
			for x in range(self.platObject.x):
				if (x,y) in self.platObject.ChosenList:
					# a floor
					self.canvas.create_rectangle(xoffset+x*scale,yoffset+y*scale,xoffset+x*scale+width,yoffset+y*scale+width,fill="black",outline="white",tags=("floor",('coords',x,y)))
					# draw triangle pointers from the floor
					OFFSET1 = width/2
					OFFSET2 = width/2-2
					OFFSET3 = width*3/2
					self.canvas.create_polygon(self.xoffset+x*scale+OFFSET1,self.yoffset+y*scale-OFFSET2,self.xoffset+x*scale+OFFSET1,self.yoffset+y*scale+OFFSET2,self.xoffset+x*scale+OFFSET3,self.yoffset+y*scale,fill="gray",outline="gray",tags=("marker","color gray",("coords",x,y,90)))
					self.canvas.create_polygon(self.xoffset+x*scale-OFFSET1,self.yoffset+y*scale-OFFSET2,self.xoffset+x*scale-OFFSET1,self.yoffset+y*scale+OFFSET2,self.xoffset+x*scale-OFFSET3,self.yoffset+y*scale,fill="gray",outline="gray",tags=("marker","color gray",("coords",x,y,270)))
					
					self.canvas.create_polygon(self.xoffset+x*scale+OFFSET2,self.yoffset+y*scale+OFFSET1,self.xoffset+x*scale-OFFSET2,self.yoffset+y*scale+OFFSET1,self.xoffset+x*scale,self.yoffset+y*scale+OFFSET3,fill="gray",outline="gray",tags=("marker","color gray",("coords",x,y,180)))
					self.canvas.create_polygon(self.xoffset+x*scale+OFFSET2,self.yoffset+y*scale-OFFSET1,self.xoffset+x*scale-OFFSET2,self.yoffset+y*scale-OFFSET1,self.xoffset+x*scale,self.yoffset+y*scale-OFFSET3,fill="gray",outline="gray",tags=("marker","color gray",("coords",x,y,0)))
					
					if (x+1,y) in self.platObject.Nodes[x][y].Linked or ((x+1<self.platObject.x) and (x,y) in self.platObject.Nodes[x+1][y].Linked):
						# a horizontal hallway
						self.canvas.create_rectangle(xoffset+x*scale+width+1,yoffset+y*scale,xoffset+(x+1)*scale-1,yoffset+y*scale+width,fill="white",outline="white",tags=("hallway_h",('coords',x,y,x+1,y)))
					if (x,y+1) in self.platObject.Nodes[x][y].Linked or ((y+1<self.platObject.y) and (x,y) in self.platObject.Nodes[x][y+1].Linked):
						# a vertical hallway
						self.canvas.create_rectangle(xoffset+x*scale,yoffset+y*scale+width+1,xoffset+x*scale+width,yoffset+(y+1)*scale-1,fill="white",outline="white",tags=("hallway_v",('coords',x,y,x,y+1)))

		# lift the triangle pointers to the top, incase they were overlapped by a hallway
		self.canvas.lift("marker")						
		self.canvas.tag_bind("marker","<Button-1>",self.MarkerB1Callback)

	# given PLAT coords, return canvas coords
	def PlatToCanvas(self,x,y):
		return ((self.xoffset+x*self.scale),(self.yoffset+y*self.scale))
	# given canvas coords, return PLAT coords
	def CanvasToPlat(self,x,y):
		return (int(round((x-self.xoffset)/self.scale)),int(round((y-self.yoffset)/self.scale)))
	# get an items PLAT coords (if it is specified in the tag
	def getItemCoords(self,item):
		return map(int,self.getItemParam(item,'coords').split())
	# get a param's value from the item's tags
	def getItemParam(self,item,param):
		for tag in self.canvas.gettags(item):
			if string.find(tag,param) == 0:
				return string.strip(tag[len(param):])
		return None
	# set item's param to value (in the tags)
	def setItemParam(self,item,param,value):
		tags = []
		for tag in self.canvas.gettags(item):
			if string.find(tag,param) == 0:
				tag = string.join([param,value],' ')
			tags.append(tag)
		self.canvas.itemconfig(item,tags=tuple(tags))
	# remove all of the subject's selected positions
	def ClearChoices(self):
		for item in self.canvas.find_withtag("marker"):
			self.setItemParam(item,'color',"gray")
			self.canvas.itemconfig(item,fill="gray",outline="gray")

	# save the selected positions to outfile			
	def SaveData(self,event=None):
		if self.layoutfilename == None:
			return
		items = self.canvas.find_withtag("color red") #get highlighted markers
		self.statevector = []
		for item in items:
			x,y,t = self.getItemCoords(item)
			self.statevector.append((x,y,t))
		if self.outfilename:
			try:
				OUTFILE = open(self.outfilename,'a')
				OUTFILE.write('>ChooseState:\t[')
				for (x,y,t) in self.statevector:
					OUTFILE.write('%d,%d,%d; '%(x,y,t))
				OUTFILE.write(']\n')
				OUTFILE.close()
				self.ClearChoices()
			except:
				tkMessageBox.showwarning("Output Error","An error occurred while trying to write to this file:\n\n%s" % self.outfilename)
				return
		if __name__!='__main__':
			self.master.destroy()

	# left button held down while mouse moved
	# - create or update select-box
	def CanvasB1MotionCallback(self,event):
		items=self.canvas.find_withtag("select-box")
		if len(items) == 0:
			# select box doesnt exist yet, so create it
			item = self.canvas.create_rectangle(event.x,event.y,event.x,event.y,outline="yellow",tags=("select-box",("coords",event.x,event.y)))
		else: item = items[0] # select-box exists, item points to it

		# update the select-box on the canvas		
		x,y = self.getItemCoords(item)		
		xlow = min(x,event.x)
		xhi = max(x,event.x)
		ylow = min(y,event.y)
		yhi = max(y,event.y)
		self.canvas.coords(item,xlow,ylow,xhi,yhi)

		# temp-highlight markers enclosed in the rectangle,
		# but don't want to lose information about which markers the subject
		# already highlighted (that is, if a marker leaves the scope of the
		# select box, temp-highlighted markers will be unhiglighted, but
		# previously highlighted markers will stay highlighted).
		
		self.canvas.addtag_withtag('remove','temp') # add remove tag to all temp-highlighted markers
		self.canvas.dtag(ALL,'temp') # remove all temp tags
		self.canvas.addtag_enclosed('temp',xlow,ylow,xhi,yhi) # add temp tags to markers in select-box
					
		for item in self.canvas.find_withtag('marker'):
			tags = self.canvas.gettags(item)
			if 'temp' in tags:
				# temp-highlight marker
				self.canvas.itemconfig(item,outline='red',fill='red')
			elif 'remove' in tags:
				# not in select-box anymore, restore color to previous color (which is red if the marker was highlighted by subject)
				color = self.getItemParam(item,'color')
				self.canvas.itemconfig(item,outline=color,fill=color)
		self.canvas.dtag(ALL,'remove')

	# left button released, highlight markers if select-box exists	 
	def CanvasB1ReleaseCallback(self,event):
		items=self.canvas.find_withtag("select-box")
		if len(items)!=0:
			item = items[0]
			(x1,y1,x2,y2) = self.canvas.coords(item)
			items = self.canvas.find_enclosed(x1, y1, x2, y2)
			if len(items)>0:
				for i in items:
					tags = self.canvas.gettags(i)
					if "marker" in tags:
						# set the item's tag color value to red to indicate that it is highlighted
						self.setItemParam(i,'color','red')
						self.canvas.itemconfig(i,outline="red",fill="red")
			self.canvas.delete("select-box")
		self.canvas.dtag(ALL,'temp')

	# highlight or unhighlight a marker
	def MarkerB1Callback(self,event):		
		if self.getItemParam(CURRENT,'color')=="gray":
			self.setItemParam(CURRENT,'color',"red")
			self.canvas.itemconfig(CURRENT,fill="red",outline="red")
		else:
			self.setItemParam(CURRENT,'color',"gray")
			self.canvas.itemconfig(CURRENT,fill="gray",outline="gray")

# call Execute from another python program to display the GUI
def Execute(LayoutFileName,OutputFileName=None):
	sys.argv = ['ChooseState.py']
	root = Tk()
	root.focus_force()
	LM = ChooseState(root,LayoutFileName,OutputFileName)
	root.mainloop()
	return LM.statevector

# returns the current version of the module
def GetVersion():
	import re
	m = re.match('^\$\s*Revision\s*:\s*(\d+[.\d]*)\s*\$$','$Revision: 1.2 $')
	if m:
		return m.group(1)
	else:
		return None

if __name__ == '__main__':
	try:
		sys.argv
	except:
		sys.argv=['ChooseState.py']
	root = Tk()
	LM = ChooseState(root)
	root.mainloop()