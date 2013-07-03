from nltk.token import Token
from nltk.tree import TreeToken

class Frame(dict):
    def __init__(self,Tree=[],F=None):
        dict.__init__({})
        if F:
            self.update(F)
        if not Tree: return self
        Current = Frame()
        for child in Tree.children():
            if isinstance(child,TreeToken):
                #if child.node() == 'PUNCT': pass
                Current = Frame(child,Current)
            elif isinstance(child,Token): pass #Do nothing with Token value
            else: print 'Unmatched token', Tree.node(), child

        self[Tree.node()] = Current
        return self

    def __repr__(self):
      s = ''
      for k,v in self.items():
          if isinstance(v,Frame): s += '{'+k+':'+v.__repr__()+'}, '
          elif v: s += '{'+k+':'+v.__repr__()+'}, '
          else: s += k+', '
      return s[:-2] #chop last ,

    def __str__(self,indent=0,margin=70):
      s = ' '*indent
      rep = self.__repr__()
      if len(rep)+indent < margin:
          return s+rep
      for k,v in self.items():
          if isinstance(v,Frame): s += '\n'+' '*(indent+2)+'{'+k+':'+v.__str__(indent+2)+'}, '
          elif v: s += '\n'+' '*(indent+2)+'{'+k+':'+v.__str__()+'}, '
          else: s += '\n'+' '*(indent+2)+'{'+k+'}, '
      return s[:-2] #chop last ', '

#DirTree = Directions._tb_tokenizer.tokenize(Directions.read('FullTrees/FullTree-EMWC_Grid0_7_5_Dirs_1.txt'))
#F = Frame(DirTree[0])
#print F

