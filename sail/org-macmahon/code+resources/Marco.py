from plastk.rl.loggingrli import TextList
from nltk.draw import BoxWidget, CanvasFrame, CanvasWidget, TextWidget, StackWidget, ColorizedList
from nltk.draw.tree import TreeWidget
from nltk.draw.featurestructure import FVM
from nltk.featurestructure import FeatureStructure
import POMDP.Viewer

class Follower:
    def __init__(self,read,parse,frame,model,executor,NLUQ=None):
        self.read = read
        self.parse = parse
        self.frame = frame
        self.model = model
        self.executor = executor
        self.NLUQueue = NLUQ
        self.stages = [('Reading', self.read),
                       ('Parsing', self.parse),
                       ('Framing', self.frame),
                       ('Modeling', self.model),
                       ('Executing', self.executor.execute),
                       ]
    
    def follow(self,instructions):
        text,CaughtError,CaughtErrorTxt    = self.read(instructions,instructID)
        parses,CaughtError,CaughtErrorTxt  = self.parse(text,instructID)
        frames,CaughtError,CaughtErrorTxt  = self.frame(parses,instructID)
        models,CaughtError,CaughtErrorTxt  = self.model(frames,instructID)
        results,CaughtError,CaughtErrorTxt = self.executor.execute(models,instructID)
        return (text,parses,frames,models,results),CaughtError,CaughtErrorTxt

def alignToStack(widget,stack,y):
    coords = widget.bbox()
    if not coords or len(coords) != 4: return y
    (x1, y1, x2, y2) = coords
    try:
        widget.move(0, y-y1)
    except TypeError, e: print widget, coords, e
    y += y2-y1 + stack._space
    stack.update(widget)
    return y

class StackableStack(StackWidget):
    def __init__(self,parent,name, **args):
        self.parent = parent
        self.name = name
        self.index = 0
        self.label = TextWidget(parent._canvas, self.labelText(), **args)
    
    def setIndex(self, index):
        self.index = index
        self.label.set_text(self.labelText())
    
    def labelText(self):
        return '%s %d'%(self.name,self.index)

class TextStack(StackableStack):
    def __init__(self,parent,name,**args):
        StackableStack.__init__(self,parent,name,**args)
        self.max_index = 20
        self.texts = []
        for i in range(self.max_index):
            tw = TextWidget(parent._canvas,str(i),justify='left')
            tw.bind_click(self.select)
            self.texts.append(tw)
        self.stack = StackWidget(parent._canvas, align='left', ordered=True,
                                 *self.texts)
        StackWidget.__init__(self, parent._canvas, self.label, self.stack,
                             align='left',ordered=True)
    
    def setTextList(self,text_list):
        self.index = 0
        for i,text in enumerate(text_list):
            self.texts[i].set_text(text)
            self.texts[i].show()
        for i in range(len(text_list),self.max_index):
            self.texts[i].set_text('')
            self.texts[i].hide()
        self.text_list = text_list
    
    def setIndex(self,index,stack,y):
        StackableStack.setIndex(self,index)
        self.update(self.label)
        ypost = self.alignToStack(stack,y)
        for i,text in enumerate(self.texts):
            text['color'] = 'black'
            text['font'] = ('helvetica',-12)
            if i < len(self.texts):
                alignToStack(self.texts[i],self.stack,y)
        if self.index < len(self.texts):
            self.texts[self.index]['color'] = 'blue'
            self.texts[self.index]['font'] = ('times',-15,'bold')
            self.stack.update(self.texts[self.index])
        return y
    
    def setColor(self,color):
        self.texts[self.index]['color'] = color
    
    def select(self,textWidget):
        self.parent.view_index = int(textWidget._text)
        self.parent.redraw()
    
    def alignToStack(self,stack,y):
        (x1, y1, x2, y2) = self.bbox()
        self.move(0, y-y1)
        (x1, y1, x2, y2) = self.bbox()
        #for i,text in enumerate(self.texts): print 'TextStack.alignToStack',i,text.bbox()
        coords = self.texts[-1].bbox()
        if not coords or len(coords) != 4: return y
        (a,b,c,ly2) = coords
        #print 'TextStack.alignToStack',y,y1,y2,ly2,stack._space
        y += ly2-y1 + stack._space
        stack.update(self)
        return y

class LabeledStructure(StackableStack):
    def __init__(self,parent,name,widgetMaker,setFn,nullEntry,agent,source,**args):
        StackableStack.__init__(self,parent,name,**args)
        self.nullEntry = nullEntry
        self.widget = widgetMaker(parent._canvas, nullEntry)
        self.setFn = setFn
        self.agent = agent
        self.source = source
        StackWidget.__init__(self, parent._canvas, self.label, self.widget,
                             align='left',ordered=True)
    
    def setIndex(self,index,stack,y):
        StackableStack.setIndex(self,index)
        source = getattr(self.agent,self.source)
        #print 'setIndex',self.setFn,self.widget,source
        if self.index < len(source):
            value = source[self.index]
        else:
            value = self.nullEntry
        getattr(self.widget,self.setFn)(value)
        alignToStack(self.label,self,y)
        alignToStack(self.widget,self,y)
        return alignToStack(self,stack,y)
    
    def setColor(self,color): self.label['color'] = color

class ActionConditionList(TextList):
    name = 'Compound Action Conditions'
    def get_line(self):
        return self.rli.agent.actionCond

class ViewDescriptionList(TextList):
    name = 'View Descriptions'
    def get_line(self):
        return self.rli.agent.viewDesc

class NLTKFrame(CanvasFrame):
    NLUQueue = None
    def __init__(self,root,rli):
        CanvasFrame.__init__(self,root)
        self.rli = rli
        self.view_index = self.index = 0
        self.text = ''
        self.parses = []
        self.frames = []
        self.models = []
        self.result = self.index = 0
        self.actionCond = ''
        self.viewDesc = ''
        self.director = None
        self.StartPlace = None
        self.DestPlace = None
        self.instructionSet = None
        self.model_change = True
        self.stages = {'Reading' : 'text',
                       'Parsing' : 'parses',
                       'Framing' : 'frames',
                       'Modeling' : 'models',
                       'Executing' : 'result',
                       'CompoundAction' : 'actionCond',
                       'Recognize' : 'viewDesc',
                       'Director' : 'director',
                       'Start Place' : 'StartPlace',
                       'Destination' : 'DestPlace',
                       'Set' : 'instructionSet',
                       }

        labelKW = {'color':'blue', 'font':('times',-15,'bold')}
        self.sentenceStack = TextStack(self,'Sentences',**labelKW)

        self.frame = LabeledStructure(self,
                                      'Frame', FVM, 'set_fvm', FeatureStructure(none=0),
                                      self,'frames',
                                      **labelKW)
        self.frame.widget._topwidget = ''

        self.model = LabeledStructure(self,
                                      'Model', TextWidget, 'set_text', 'None',
                                      self,'models',
                                      **labelKW)
        
        self.children = [self.sentenceStack, self.frame, self.model]
        self.lingStack = StackWidget(self._canvas,align='left',ordered=True,
                                     *self.children)
        self.add_widget(self.lingStack)

    def __call__(self): pass

    def handleNLU(self):
        message = self.NLUQueue.get()
        if type(message) == tuple:
            label,value = message
            if type(getattr(self,self.stages[label])) == list:
                for item in getattr(self,self.stages[label]): del item
            setattr(self,self.stages[label], value)
            print 'handleNLU:: processed message:',self.stages[label],getattr(self,self.stages[label])
            if label in ('Modeling'): self.model_change = self.rli.agent.new_id = True
            if label == 'CompoundAction': self.rli.agent.actionCond = self.actionCond
            if label == 'Recognize': self.rli.agent.viewDesc = self.viewDesc
        else:
            raise TypeError, ('Unknown type of message',message,type(message))

    def changeModel(self):
        if ('. ') in self.text: self.sentenceStack.setTextList(self.text.split('. '))
        else: self.sentenceStack.setTextList([self.text])

    def redraw(self):
        while self.NLUQueue and not self.NLUQueue.empty(): self.handleNLU()
        if self.model_change: self.changeModel()
        if (self.model_change or self.result != self.index or self.index != self.view_index):
            if self.result != self.index and self.index == self.view_index:
                self.index = self.view_index = self.result
            else: self.index = self.view_index
            if (self.index < len(self.sentenceStack.text_list)): color = 'dark green'
            else: color = 'blue'
            
            (left, top, right, bot) = self.lingStack.bbox()
            y = top + self.lingStack._space
            for child in self.children:
                child.setColor(color)
                y = child.setIndex(self.index,self.lingStack,y)
            
            (topLeft, topTop, topRight, topBottom) = self.sentenceStack.label.bbox()
            (botLeft, botTop, botRight, botBottom) = self.model.bbox()
            self._canvas['scrollregion'] = ('%d %d %d %d' % 
                                           (min(topLeft,botLeft),
                                            min(topTop,botTop),
                                            max(topRight,botRight),
                                            max(topBottom,botBottom)))
            self._canvas.xview_moveto(0)
            self._canvas.yview_moveto(0)
            
            if self.model_change:
                self.rli.agent.set_instruction_id(
                    self.director,self.StartPlace,self.DestPlace,self.instructionSet)
                self.model_change = self.rli.agent.new_id = False

class FollowerAgentProxy(POMDP.Viewer.AgentProxy):
    def __init__(self,actionQ,observationQ,**args):
        super(FollowerAgentProxy,self).__init__(actionQ,observationQ,**args)
        self.actionCond = None
        self.viewDesc = None
        self.new_id = False
        self.director = 0
        self.StartPlace = 0
        self.DestPlace = 0
        self.instructionSet = 0

    def set_instruction_id(self,director,StartPlace,DestPlace,instructionSet):
        (self.director,self.StartPlace,self.DestPlace,self.instructionSet) = (
            director,StartPlace,DestPlace,instructionSet)
