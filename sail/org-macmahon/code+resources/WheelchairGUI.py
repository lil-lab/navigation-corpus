#this file contains the code for the buttons on the GUI:
# simulator, navigation, environment, start, and dest buttons
# along with the text box for display of current information
import Queue,thread
from Robot.Meanings import str2meaning
from POMDP.Viewer import ImageView, AgentProxy

from plastk.rl.queue import QueuePOMDPProxy
from plastk.rl.facegridworld import MarkovLocPOMDPWorld, FaceGridWorldDisplay
from plastk.rl.loggingrli import LoggingRLI, EpisodeVarPlotter, NewColumn, ActionList, SensationList
from Tkinter import Frame,Button
from RouteRunner import Positions, Maps
import Pmw

def validate_routeID(routeID):
    if not routeID: return Pmw.OK
    if routeID.count('_') != 2: return Pmw.PARTIAL
    env,start,dest = routeID.split('_')
    if (env[:-1] in Maps and 
        start in Positions and
        dest in Positions and
        start != dest
        ):
        return Pmw.OK
    return Pmw.PARTIAL

class RouteIDEntry(Frame):
    instructionQ = None
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.rli = rli
        self.root = root
        self.entryfield = Pmw.EntryField(
            root, labelpos = 'n', value = '',
            label_text = 'Route ID',
            command = self.set_routeID,
            validate = validate_routeID,
            )
        self.entryfield.pack()
        self.episode = False

    def redraw(self):
        if self.rli.agent.new_id:
            #something weird happens, initially, self.rli.agent.* are used in this, then they are overwritten somewhere with self.rli.agent.*+1 (it seems)
            self.routeID = '_'.join((
                self.rli.env.name+'0',
                str(self.rli.agent.StartPlace),
                str(self.rli.agent.DestPlace),
                ))
            self.entryfield.setentry(self.routeID)
            self.entryfield.invoke()
            self.rli.agent.new_id = False
            if self.rli.gui_runstate == 'Episode':
                self.episode = True
                if self.instructionQ.full(): self.instructionQ.get()
                self.instructionQ.put(('State','Episode'))
            elif self.rli.gui_runstate == 'Stop' and self.episode:
                if self.instructionQ.full(): self.instructionQ.get()
                self.set_routeID()

    def set_routeID(self):
        validity = self.entryfield.checkentry()
        print 'Setting:', self.entryfield.getvalue()
        if validity == Pmw.OK:
            if not self.instructionQ.full() and not self.rli.agent.new_id:
                print 'Inserting into queue:', self.entryfield.getvalue()
                self.instructionQ.put(('ID',self.entryfield.getvalue()))

    def set_field(self,field,value):
        if not self.entryfield.checkentry(): return
        text = self.entryfield.getvalue() or 'Grid0_1_2'
        env,start,dest = text.split('_')
        if field == 'env': env = value
        elif field == 'start': start = value
        elif field == 'dest': dest = value
        else: print 'Unknown field',field
        if '0' not in env and '1' not in env: env = env+'0'
        self.entryfield.setentry('_'.join((env,start,dest)))

class RadioRow(Frame):
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.rli = rli
        self.root = root
        self.row = Pmw.RadioSelect(root,
                                   labelpos = 'nw',
                                   orient = 'vertical',
                                   frame_borderwidth = 1,
                                   frame_relief = 'ridge',
                                   label_text = self.label_text,
                                   padx = 2,
                                   Button_padx = 0,
                                   command = self.set_field,
                                   )
        for text in self.button_texts:
            self.row.add(text)
        self.row.pack(side='left',fill='y',expand=0)
        if self.rli.agent.new_id:
            if self.field == "start" and self.rli.agent.StartPlace is not None:
                self.row.invoke(int(self.rli.agent.StartPlace) - 1)
            if self.field == "dest" and self.rli.agent.DestPlace is not None:
                self.row.invoke(int(self.rli.agent.DestPlace) - 1)

    def redraw(self): self.row.invoke(self.get_value())
    def set_field(self,value): self.root.routeID.set_field(self.field,value)

class EnvRow(RadioRow):
    button_texts = Maps
    label_text = 'Env'
    field = 'env'
    def get_value(self): return self.rli.env.name or Pmw.END

class StartRow(RadioRow):
    button_texts = Positions
    label_text = 'Start'
    field = 'start'
    def get_value(self): return self.rli.agent.StartPlace or Pmw.END

class DestRow(RadioRow):
    button_texts = Positions
    label_text = 'Dest'
    field = 'dest'
    def get_value(self): return self.rli.agent.DestPlace or Pmw.END

class RouteIDInfo(Frame):
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.widgetNames = ('routeID','env','start','dest')
        for name,widget in zip(self.widgetNames,
                               (RouteIDEntry,EnvRow,StartRow,DestRow)):
            temp = widget(self, rli, **args)
            setattr(self,name,temp)
            temp.pack(side='left',expand=1)
        self.ok = Button(self, text='Enter', command=self.routeID.entryfield.invoke)
        self.ok.pack(side='top',after=self.routeID,anchor='n')
    def redraw(self):
        for widgetName in self.widgetNames:
            getattr(self,widgetName).redraw()

class InstructionNav(Frame):
    instructionQ = None
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.nav_control = Pmw.RadioSelect(root,
                                            labelpos = 'w',
                                            orient = "horizontal",
                                            command = self.set_instruction,
                                            label_text = '',
                                            frame_borderwidth = 1,
                                            frame_relief = 'ridge')
        self.nav_control.pack(side='top',fill='none')
        # Add some buttons to the RadioSelect.
        for text in ('TurnLeft','TravelFwd', 'TurnRight', 'Stop','AutoNav'):
            self.nav_control.add(text)
        self.nav_control.invoke('Stop')

    def set_instruction(self, instr):
        if not self.instructionQ.full():
            print 'Inserting into queue:', instr
            self.instructionQ.put(('NavID',instr))
    def redraw(self): pass

from FollowerGUI import InstructionIDEntry, InstructionIDInfo

def run(Executor,Robot,Routes,Pomdp,map_dir='Maps',Instructions=False):
    ActionQ = Queue.Queue(1)
    ObservationQ = Queue.Queue(1)
    if Instructions:
        instructionQ = InstructionIDEntry.instructionQ = Queue.Queue(20)
        controls = (InstructionIDInfo, NewColumn,)
    else:
        Executor.instructionQ = InstructionNav.instructionQ =RouteIDEntry.instructionQ = Queue.Queue(20)
        controls = (InstructionNav, RouteIDInfo, NewColumn,)

    pomdpProxy = QueuePOMDPProxy(ActionQ, ObservationQ, str2meaning, False)
    Pomdp.map_dir = map_dir
    pomdpProxy.setPOMDP(Pomdp)
    Executor.setRobot(Robot(pomdpProxy, Pomdp.name))
    
    rli = LoggingRLI(name='WheelchairAgent', rename_old_data=False)
    rli.init(AgentProxy(ActionQ, ObservationQ),
             MarkovLocPOMDPWorld(pomdp=Pomdp, crumbs=True, recolor_crumbs_on_pose_set=True))

    #i couldn't find where these values were set in Matt's code, so I set it here, which is not good, because it eventually gets overwritten somewhere else
    rli.agent.new_id = True
    rli.agent.StartPlace = Executor.Start
    rli.agent.DestPlace = Executor.Target

    thread.start_new_thread(Executor.run,(Routes,))

    guiColumns =  controls + (
        ImageView, FaceGridWorldDisplay, NewColumn,
        SensationList, ActionList, NewColumn,
        )

    rli.gui(*guiColumns)
    return 0
