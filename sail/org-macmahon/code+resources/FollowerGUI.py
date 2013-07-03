import Queue,thread
from Robot.Meanings import str2meaning
from POMDP.Viewer import ImageView

from plastk.rl.queue import QueuePOMDPProxy
from Marco import NLTKFrame, ActionConditionList, ViewDescriptionList, FollowerAgentProxy
from plastk.rl.facegridworld import MarkovLocPOMDPWorld, FaceGridWorldDisplay
from plastk.rl.loggingrli import LoggingRLI, EpisodeVarPlotter, NewColumn, ActionList, SensationList
from Tkinter import Frame,Button
import Pmw

from Harness import Directors,Maps,Positions,PositionSets
Directors.append('INPUT')

def validate_instructionID(instructionID):
    if not instructionID: return Pmw.OK
    if instructionID.count('_') != 5: return Pmw.PARTIAL
    director,env,start,dest,txt,set = instructionID.split('_')
    Map = env[:-1]
    posset = env[-1]
    if (director in Directors and
        Map in Maps and
        posset in PositionSets and
        start in Positions and
        dest in Positions and
        start != dest and
        txt == 'Dirs' and
        set in ('1.txt', '2.txt')
        ):
        return Pmw.OK
    return Pmw.PARTIAL

class InstructionIDEntry(Frame):
    instructionQ = None
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.rli = rli
        self.root = root
        self.entryfield = Pmw.EntryField(
            root, labelpos = 'n', value = '',
            label_text = 'Instruction Set ID',
            command = self.set_instructionID,
            validate = validate_instructionID,
            )
        self.entryfield.pack()
        self.episode = False

    def redraw(self):
        if self.rli.agent.new_id:
            self.instructionID = '_'.join((
                self.rli.agent.director,
                self.rli.env.name,
                self.rli.agent.StartPlace,
                self.rli.agent.DestPlace,
                'Dirs',
                self.rli.agent.instructionSet
                ))
            self.entryfield.setentry(self.instructionID)
            self.entryfield.invoke()
            self.rli.agent.new_id = False
            if self.rli.gui_runstate == 'Episode':
                self.episode = True
                if self.instructionQ.full(): self.instructionQ.get()
                self.instructionQ.put(('State','Episode'))
            elif self.rli.gui_runstate == 'Stop' and self.episode:
                if self.instructionQ.full(): self.instructionQ.get()
                self.set_instructionID()

    def set_instructionID(self):
        validity = self.entryfield.checkentry()
        print 'Setting:', self.entryfield.getvalue()
        if validity == Pmw.OK:
            if not self.instructionQ.full() and not self.rli.agent.new_id:
                print 'Inserting into queue:', self.entryfield.getvalue()
                self.instructionQ.put(('ID',self.entryfield.getvalue()))
            instructionText = self.root.instructionText.text.getvalue()
            if instructionText:
                print 'Inserting instructions into queue:', instructionText
                self.instructionQ.put(('Text',instructionText))

    def set_field(self,field,value):
        if not self.entryfield.checkentry(): return
        text = self.entryfield.getvalue() or 'EDA_Grid0_1_2_Dirs_1.txt'
        director,env,start,dest,txt,set = text.split('_')
        if field == 'director': director = value
        elif field == 'env': env = value
        elif field == 'start': start = value
        elif field == 'dest': dest = value
        else: print 'Unknown field',field
        #if '0' not in env: env = env+'0'
        self.entryfield.setentry('_'.join((director,env,start,dest,txt,set)))

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
    def redraw(self): self.row.invoke(self.get_value())
    def set_field(self,value): self.root.instructionID.set_field(self.field,value)

class DirectorRow(RadioRow):
    button_texts = Directors
    label_text = 'Director'
    field = 'director'
    def get_value(self): return self.rli.agent.director or Pmw.END

class EnvRow(RadioRow):
    button_texts = [Map+PosSet for Map in Maps for PosSet in PositionSets]
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

class InstructionTextEntry(Frame):
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.rli = rli
        self.root = root
        self.text = Pmw.ScrolledText(root,
                                     text_width=30, text_height=15,
                                     labelpos='n',
                                     label_text='Instruction text',
                                     )
        self.text.pack()
    def redraw(self): pass

class InstructionIDInfo(Frame):
    def __init__(self, root, rli, **args):
        Frame.__init__(self, root, **args)
        self.widgetNames = ('instructionID','director','env','start','dest')
        for name,widget in zip(self.widgetNames,
                               (InstructionIDEntry,DirectorRow,EnvRow,StartRow,DestRow)):
            temp = widget(self, rli, **args)
            setattr(self,name,temp)
            temp.pack(side='left',expand=1)
        self.ok = Button(self, text='Enter', command=self.instructionID.entryfield.invoke)
        self.ok.pack(side='top',after=self.instructionID,anchor='n')
        self.instructionText = InstructionTextEntry(root,rli,**args)
        self.instructionText.pack(side='bottom',expand=1,anchor='s')
    def redraw(self):
        for widgetName in self.widgetNames:
            getattr(self,widgetName).redraw()

def run(executor,follower,POMDPs,Robot,Recognizer,Instructions,pomdp_name='Grid'):
    ActionQ = Queue.Queue(1)
    ObservationQ = Queue.Queue(1)
    follower.NLUQueue = NLTKFrame.NLUQueue = executor.NLUQueue = Queue.Queue(25)
    instructionQ = InstructionIDEntry.instructionQ = Queue.Queue(20)

    pomdpProxy = QueuePOMDPProxy(ActionQ, ObservationQ, str2meaning, False)
    pomdp = POMDPs[pomdp_name]
    pomdpProxy.setPOMDP(pomdp)
    executor.setRobot(Robot(pomdpProxy, pomdp_name, Recognizer))
    executor.robot.NLUQueue = executor.NLUQueue

    rli = LoggingRLI(name='InstructionFollower', rename_old_data=False)#, gui_button_orient='vertical'
    rli.init(FollowerAgentProxy(ActionQ, ObservationQ),
             MarkovLocPOMDPWorld(pomdp=pomdp, crumbs=True))
    Instructions = [i for i in Instructions if '_%s%d_'%(pomdp_name,pomdp.PosSet) in i]
    CorpusDirectors = {}
    for ri in Instructions:
        CorpusDirectors[ri.split('-')[1].split('_')[0]] = True
    CorpusDirectors = CorpusDirectors.keys()
    CorpusDirectors.sort()
    DirectorRow.button_texts = CorpusDirectors + ['INPUT']
    EnvRow.button_texts = ['%s%d'%(pomdp_name,pomdp.PosSet)]
    thread.start_new_thread(follower.run, (Instructions, instructionQ))
    rli.gui(
        InstructionIDInfo, NewColumn,
        ImageView, FaceGridWorldDisplay, NewColumn,
        NLTKFrame, NewColumn,
        ViewDescriptionList,  SensationList, ActionConditionList, ActionList, NewColumn,
        )
    return 0

