"""Inspect pickle structure with inert objects. No import, callable or reducer execution."""
import pickletools
class Box:
    def __init__(self,kind,args=()):self.kind=kind;self.args=args;self.state=None;self.items={};self.sequence=[]
def read(data):
    stack=[];memo={};mark=object()
    def popmark():
        i=len(stack)-1
        while i>=0 and stack[i] is not mark:i-=1
        if i<0:raise ValueError('missing mark')
        values=stack[i+1:];del stack[i:];return values
    def assign(target,key,value):
        if isinstance(target,Box):target.items[key]=value
        elif isinstance(target,dict):target[key]=value
        else:raise ValueError('unexpected mapping target')
    def extend(target,values):
        if isinstance(target,Box):target.sequence.extend(values)
        elif isinstance(target,list):target.extend(values)
        else:raise ValueError('unexpected sequence target')
    for op,arg,pos in pickletools.genops(data):
        name=op.name
        if name in ('PROTO','FRAME'):continue
        if name=='STOP':
            if len(stack)!=1:raise ValueError('pickle stack at STOP')
            return stack[0]
        if name=='MARK':stack.append(mark)
        elif name in ('NONE','NEWTRUE','NEWFALSE'):stack.append({'NONE':None,'NEWTRUE':True,'NEWFALSE':False}[name])
        elif name in ('BININT','BININT1','BININT2','INT','LONG','LONG1','LONG4','FLOAT','BINFLOAT','STRING','BINSTRING','SHORT_BINSTRING','UNICODE','BINUNICODE','SHORT_BINUNICODE','BINUNICODE8','BINBYTES','SHORT_BINBYTES','BINBYTES8'):stack.append(arg)
        elif name=='GLOBAL':stack.append(Box('GLOBAL',arg))
        elif name=='STACK_GLOBAL':
            value=stack.pop();module=stack.pop();stack.append(Box('GLOBAL',str(module)+' '+str(value)))
        elif name in ('REDUCE','NEWOBJ'):
            args=stack.pop();cls=stack.pop();stack.append(Box(name,(cls,args)))
        elif name=='BUILD':
            state=stack.pop()
            if not isinstance(stack[-1],Box):raise ValueError('BUILD target')
            stack[-1].state=state
        elif name in ('BINPUT','LONG_BINPUT','PUT'):memo[int(arg)]=stack[-1]
        elif name=='MEMOIZE':memo[len(memo)]=stack[-1]
        elif name in ('BINGET','LONG_BINGET','GET'):stack.append(memo[int(arg)])
        elif name=='EMPTY_DICT':stack.append({})
        elif name=='EMPTY_LIST':stack.append([])
        elif name=='EMPTY_TUPLE':stack.append(())
        elif name=='TUPLE':stack.append(tuple(popmark()))
        elif name in ('TUPLE1','TUPLE2','TUPLE3'):
            count=int(name[-1]);v=tuple(stack[-count:]);del stack[-count:];stack.append(v)
        elif name=='DICT':
            v=popmark();stack.append(dict(zip(v[::2],v[1::2])))
        elif name=='LIST':stack.append(popmark())
        elif name=='SETITEMS':
            values=popmark()
            if len(values)%2:raise ValueError('odd mapping items')
            for k,v in zip(values[::2],values[1::2]):assign(stack[-1],k,v)
        elif name=='SETITEM':
            v=stack.pop();k=stack.pop();assign(stack[-1],k,v)
        elif name=='APPENDS':
            values=popmark();extend(stack[-1],values)
        elif name=='APPEND':value=stack.pop();extend(stack[-1],[value])
        elif name=='POP':stack.pop()
        elif name=='POP_MARK':popmark()
        elif name=='DUP':stack.append(stack[-1])
        else:raise ValueError('unsupported passive opcode: '+name+' at '+str(pos))
    raise ValueError('missing pickle STOP')

def walk(root):
    seen=set();todo=[('$',root)]
    while todo:
        path,value=todo.pop()
        if isinstance(value,(Box,dict,list,tuple)):
            if id(value) in seen:continue
            seen.add(id(value))
        yield path,value
        if isinstance(value,Box):todo.extend([(path+'.state',value.state),(path+'.args',value.args),(path+'.items',value.items),(path+'.sequence',value.sequence)])
        elif isinstance(value,dict):todo.extend((path+'['+repr(k)+']',v) for k,v in value.items())
        elif isinstance(value,(list,tuple)):todo.extend((path+'['+str(i)+']',v) for i,v in enumerate(value))
