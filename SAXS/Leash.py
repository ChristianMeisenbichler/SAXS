import zmq
import random
import sys
import time
import os
import json
from optparse import OptionParser
import base64
import time
import numpy as np
import matplotlib
import hashlib
 
import matplotlib.pyplot as plt

from jsonschema import validate,ValidationError
def leashsend(socket,mparts):
    socket.send_multipart(mparts)
def addauthentication(request,conf):
    """
    sign request for authentication
    """
    m=hashlib.sha512()
    request['time']=time.time()
    request['sign']=""
    m.update(json.dumps(request, sort_keys=True))
    m.update(conf['Secret']+"")
    request['sign']=m.hexdigest()
    return request
def validateResponse(message):
    """
    Validate response from saxsdog server against the schema.
    """
    try:    
        resp=json.loads(message)
        respschema=json.load((open(os.path.dirname(__file__)+os.sep+'LeashResultSchema.json')) )
        validate(resp,respschema)
        return message
    except ValidationError as e:
        print "\nError in response data format:\n"
        print e.message
        json.dump(resp, open("dump.json","w"),  indent=2)
        print """Message dumped "dump.json"""
        return json.dumps({"result":"Error","data":{"Error":e.message}})
    
def sendclose(options,arg,socket,conf):
    request={"command":"close","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
   
def sendabort(options,arg,socket,conf):
    request={"command":"abort","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
    
def sendplotdata(options,arg,socket,conf):
    request={"command":"plot","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
   
def sendplot(options,arg,socket,conf):
    """
    remote plot visualization for command line mode
    """
    
    plt.ion()
    while True:
        sendplotdata(options,arg,socket,conf)
        object=json.loads( receive(socket))
        
        #print json.dumps(object,indent=4, separators=(',', ': ')) 
        if object["result"]=="Empty":
          
            time.sleep(1)
            continue
        
        data=np.array(object['data']['array'][0]).transpose()
        skip=options.skip
        clip=options.clip
        clipat=0
        plt.plot(data[skip:-clip,0],data[skip:-clip,1])
        plt.fill_between( data[skip:-clip,0] ,
                   np.clip(data[skip:-clip,1]-data[skip:-clip,2],clipat,1e300),
                   np.clip(data[skip:-clip,1]+data[skip:-clip,2],clipat,1e300),
                   facecolor='blue' ,alpha=0.2,linewidth=0,label="Count Error")
        plt.title(object['data']['filename'])
        plt.ylabel('Intensity [counts/pixel]')
        plt.xlabel('q [1/nm]')
        plt.yscale(options.yax)
        plt.xscale(options.xax)
        plt.draw()
        plt.clf()
        time.sleep(.5)
        
def sendreaddir(options,arg,socket,conf):
    """
    read all the files in the set directory and feed them into the processing server
    """
    request={"command":"readdir","argument":{}}
     
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
   
   
def sendstat(socket,conf):
    request={"command":"stat","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
def sendgetmergedata(options,arg,socket,conf):
    request={"command":"getmergedata","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
def sendget(socket,conf):
    """
    get current calibration data
    """
    request={"command":"get","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))] )
def sendgetfileslist(socket,conf):
    """
    get list of chi files
    """
    request={"command":"fileslist","argument":{}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
   
def sendlistdir(arg,socket,conf):
    """
    get directory contents
    """
    if len (arg)<2:
        arg.append(".")
    if arg[1]=="":
        arg[1]="."
    request={"command":"listdir","argument":{"directory":arg[1].split(os.sep)}}
    leashsend(socket,[json.dumps(addauthentication(request,conf))])
   
def senddatamerge(options,arg,socket,conf):
    cal=json.load(open(arg[1],"r"))
    request={ 
             "command":"mergedata",
             "argument":{ 
                         "mergeconf":cal, 
                          }
             }
    messageparts=(json.dumps(addauthentication(request,conf)),)
    for table in cal["LogDataTables"]:
        for filedesc in table["Files"]:
            if 'LocalPath' in filedesc and filedesc["LocalPath"]!="":
                messageparts+=(json.dumps(
                                      {"filename":filedesc["LocalPath"],
                                       "data":open(filedesc["LocalPath"],"r").read()
                                       }),)
  
    leashsend(socket,messageparts)
def sendnew(options,arg,socket,conf):
    """
    upload new calibration for image processing
    """
    request={ 
             "command":"new",
             "argument":{
                         
                         "calibration":{},
                          "data":{}
                         }
             }
    if len(arg)>=2:
        try:
            if isinstance(arg[1], basestring):
                cal=json.load(open(arg[1]))
            elif isinstance(arg[1], dict):
                cal=arg[1]
            calschema=json.load(open(os.path.dirname(__file__)+'/schema.json'))
            validate(cal,calschema)
            request['argument']['calibration']=cal
           
        except (ValueError) as e:
            print e
            print "The calibration File, "+arg[1]+",is not Valid"
            sys.exit()
        except ValidationError as e:
           
            print e.message
            print "The calibration File, "+arg[1]+",is not Valid"
            sys.exit()
        
    else:
        print "Error"
        print "new command:"
        print "usage: leash new clibrationfile.json  "
        sys.exit()
    messageparts=(json.dumps(addauthentication(request,conf)),)
    for mask in cal["Masks"]:
        maskfile=mask["MaskFile"]
        messageparts+=(json.dumps(
                                  {"filename":maskfile,
                                   "data":base64.b64encode(open(maskfile,"rb").read())
                                   }),)
    leashsend(socket,messageparts)
 
   
def initcommand(options, arg,conf):
    """
    Interface for issuing leash commands
    """
   
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.setsockopt(zmq.LINGER, 1)
    if options.server=="":
        server=conf['Server']
    else:
        server=options.server
    if __name__=="__main__":print "conecting:",server
    socket.connect (server)
 
    if arg[0]=="close":
         result= sendclose(options,arg,socket,conf)
    elif arg[0]=="new":
         result= sendnew(options,arg,socket,conf)
    elif arg[0]=="mergedata":
         result=senddatamerge(options,arg,socket,conf)
    elif arg[0]=="getmergedata":
         result=sendgetmergedata(options,arg,socket,conf)
    elif arg[0]=="abort":
         result= sendabort(options,arg,socket,conf)
    elif arg[0]=="plot":
         result= sendplot(options,arg,socket,conf)
    elif arg[0]=="plotdata":
         result=sendplotdata(options,arg,socket,conf)
    elif arg[0]=="readdir":
         result= sendreaddir(options,arg,socket,conf)
    elif arg[0]=="stat":
         result= sendstat(socket,conf)
    elif arg[0]=="get":
        result=sendget(socket,conf)
    elif arg[0]=="listdir":
        result=sendlistdir(arg,socket,conf)
    elif arg[0]=="fileslist":
        result=sendgetfileslist(socket,conf)
    else:
        raise ValueError(arg[0])


    answer=receive(socket)
    
    socket.close()
    
    context.term()
    return answer


def receive(socket):   
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    plist= poller.poll(100000)
    if  len(plist)==1:
        data=socket.recv()
        return validateResponse(data)
    else:
        return json.dumps({"result":"Error","data":{"Error":"Timeout"}})
     
  
    
                        
def parsecommandline(mode=""):
    
    parser = OptionParser()
    usage = ("usage: %prog "+
             '|'.join(
                      json.load(open(os.path.dirname(__file__)+'/LeashRequestSchema.json')
                        )["properties"]["command"]['enum']
                      ) +" [options] [arguments]"
       )
    parser = OptionParser(usage)
    parser.add_option("-S", "--server", dest="server",
                      help='URL of "Saxsdog Server"', metavar="tcp://HOSTNAME:PORT",default="") 
    parser.add_option("-s", "--skip", dest="skip",
                          help="plot: Skip first N points."
                          , metavar="N",default=0 ,type="int")   
    parser.add_option("-k", "--clip", dest="clip",
                      help="plot: Clip last N points."
                      , metavar="N",default=1 ,type="int")
    parser.add_option("-x",'--xaxsistype',dest='xax',metavar='TYPE',default='linear',
                       help="plot: Select type of X axis scale, might be [linear|log|symlog]")
    parser.add_option("-y",'--yaxsistype',dest='yax',metavar='TYPE',default='linear',
                       help="plot: Select type of Y axis scale, might be [linear|log|symlog]")
    parser.add_option("-N",'--serverno',dest='serverno', default=0,
                       help="select server from config list by index default:0")
    (options, args) = parser.parse_args(args=None, values=None)
    if mode=="commandline" and len(args)<1:
        parser.error("incorrect number of arguments")
    
    return  (options, args)
def saxsleash():
    """
    The command line leash.
    """
    (options,arg)=parsecommandline(mode="commandline")
    
    conf=json.load(open(os.path.expanduser("~"+os.sep+".saxsdognetwork")))
    validate(conf,json.load(open(os.path.dirname(__file__)+os.sep+'NetworkSchema.json')))
    try:
        result=initcommand(options,arg,conf[int(options.serverno)])
    except ValueError as e:
        print '"'+arg[0]+'" is not a valid command. See -h for help.'
        print e
        sys.exit()
    print json.dumps(json.loads(result),indent=4, separators=(',', ': '))
    validateResponse(result)
    
    
if __name__ == '__main__':
    saxsleash()
    