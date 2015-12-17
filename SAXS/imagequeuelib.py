# coding: utf8
from threading import Thread,current_thread,active_count

import time
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from AddToQueue import addtoqueue
from scipy import misc
import os,sys
from PIL import Image,TiffImagePlugin
 
import numpy as np
from multiprocessing import Queue ,Value
from Subproccompatibility import Process
from Queue import Empty, Full
import matplotlib.pyplot as plt
import zmq
import json
import time
import datamerge
#from SAXS.tifffile import   TiffFile 
def funcworker(self,threadid):
   """
   Function for subprocesses
   """
   while self.stopflag.value==0: 
        try:
            try:
                picture = self.picturequeue.get(timeout=1)
            except KeyboardInterrupt:
                break
            except Empty:
                continue
            self.procimage(picture,threadid)
         
        except KeyboardInterrupt:
            pass 
        except Exception as e:
            print 
   
def filler(queue,dir):
            filequeue=[] 
            print "filler" + dir
            
            for path, subdirs, files in os.walk(dir):
                for name in files:
                    if name.endswith('tif'):
                        queue.put(os.path.join(path, name))      
class imagequeue:
    """
    This class keeps a queue of images which may be worked on in threads.
    
    :param SAXS.calibration Cal: The SAXS Calibration to use for the processing
    :param optparser options: The object with the comandline options of the saxsdog
    :param list args: List of command line options
    
    """
    def __init__(self,Cals,options,directory,conf):
         
         self.pool=[]
         self.cals=Cals
         self.conf=conf
         self.options=options
         self.picturequeue=Queue()
         self.histqueue=Queue(maxsize=10000)
         self.plotdataqueue=Queue(maxsize=1)
         self.directory=directory
         self.allp=Value('i',0)
         self.stopflag=Value('i',0)
         self.dirwalker=None
         self.observer=None
         if not options.plotwindow: 
              plt.switch_backend("Agg")
         self.fig=plt.figure()
         if  options.plotwindow: 
              plt.ion()
       
    def getlastdata(self):
          print "getdatata" + str(self.lastfile)
          return self.lastfile,self.lastdata
    
    def fillqueuewithexistingfiles(self):
        """
        Fill the queue with the list of images that is already there.
        """
       
                
        if self.options.walkdirinthreads:
            self.dirwalker=Thread(target=filler,args=(self.picturequeue,self.directory))
            self.dirwalker.start()
        else:
           
            filler(self.picturequeue,self.directory)
        
    def procimage(self,picture,threadid):
            filelist={}
            max=60
            if not self.options.silent: print "[",threadid,"] open: ",picture 
            for i in range(max):
                try:
                    image=misc.imread(picture)
                except KeyboardInterrupt:
                    return
                except IOError as e:
                    try:
                        print "cannot open ", picture, ", lets wait.", max-i ," s"
                        print e.message,  sys.exc_info()[0]
                        time.sleep(1)
                        continue
                    except KeyboardInterrupt:
                        return
                except:
                    print "############"
                    print   sys.exc_info()
                    continue
                if image.shape==tuple(self.cals[0].config["Geometry"]["Imagesize"]):
                    break
                print "cannot open ", picture, ", lets wait.", max-i ," s"
                time.sleep(1)
                    
            else:
                print "image ", picture, " has wrong format"
                return
            
            if self.options.outdir!="":
                basename=self.options.outdir+os.sep+('_'.join(picture.replace('./','').split(os.sep))[:-3]).replace('/',"_")
                basename=basename.replace(':', '').replace('.','')
            else:
                reldir=os.path.join( 
                                      os.path.dirname(picture),
                                      self.options.relpath)
                if not os.path.isdir(reldir):
                    os.mkdir(reldir)
                basename=os.path.join( reldir,
                                      os.path.basename(picture)[:-4])
            data=[]
            integparams={}
            imgMetaData=datamerge.readtiff(picture)
            if "date" in imgMetaData:
                imgTime=imgMetaData["date"]
            else:
                imgTime=""            
            for calnum,cal in enumerate(self.cals):   
                if len(list(enumerate(self.cals)))==1:
                    filename=basename
                else:
                    filename=basename+"_c"+cal.kind[0]+str(calnum)
                chifilename=filename+".chi"
                filelist[cal.kind+str(calnum)]=chifilename
                if not self.options.resume or not os.path.isfile(chifilename):
                    result=cal.integratechi(image,chifilename,picture)
                    result["Image"]=picture
                    if "Integparam" in result:
                        integparams[cal.kind[0]+str(calnum)]=result["Integparam"]                                        
                    data.append(result)
                    if threadid==0 and self.options.plotwindow:
                        # this is a hack it really schould be a proper GUI
                       
                        cal.plot(image,fig=self.fig)
                        plt.draw()
                       
                             
                if self.options.writesvg: 
                    
                    if not self.options.resume or not os.path.isfile(filename+'.svg'):
                         cal.plot(image,filename+".svg",fig=self.fig)
                if self.options.writepng:
                     if not self.options.resume or not os.path.isfile(filename+'.svg'):
                          misc.imsave(filename+".png",image)
                if self.options.silent:
                    if np.mod(self.allp.value,100)==0:
                        print "[",threadid,"] ",self.allp.value
                else:
                    print "[",threadid,"] write: ",filename+".chi" 
            with self.allp.get_lock():
                self.allp.value+=1
                
            filelist["JSON"]=basename+".json"
            
            try:
                self.histqueue.put({"Time":float(time.time()),
                                "ImgTime":imgTime, 
                                "FileList":filelist,
                                "BaseName":basename,
                                "IntegralParameters":integparams},block=False)
            except Full:
                print "Full"
            return basename ,data
    def start(self):  
        """
        Start threads and directory observer.
        """
        #start threads
        
        for threadid in range(1,self.options.threads):
            print "start proc [",threadid,"]"
           
            worker=Process(target=funcworker, args=(self,threadid))
            worker.daemon=True
            self.pool.append(worker)
            worker.start() 
            #self.processimage(picture,options)
        self.starttime=time.time() 
        if self.options.watch:
            eventhandler=addtoqueue(self.picturequeue)
            self.observer = Observer()
            self.observer.schedule(eventhandler, self.args[0], recursive=True)
            self.observer.start()
        #We let the master process do some work because its useful for matplotlib.
        if not self.options.nowalk:
            self.fillqueuewithexistingfiles()
        if self.options.servermode:
              
             from Leash import addauthentication
        try:
            while ( self.options.servermode or 
                    (not self.picturequeue.empty()) 
                    or (self.dirwalker and self.dirwalker.is_alive() )
                    or self.options.watch): 
                    try:
                        picture = self.picturequeue.get(timeout=1)
                    except Empty:
                        continue
                    lastfile, data =self.procimage(picture,0)
                    
                    if self.options.servermode:
                        request={"command":"putplotdata","argument":{"data":{
                                "result":"plot","data":{"filename":lastfile,"graphs":data,
                                                        "stat":{}}
                                  }}}
                     
                        self.plotdataqueue.put(request)
                    if np.mod(self.allp.value,500)==0:
                        self.timreport()
        except KeyboardInterrupt:
            pass
        
        self.stop()
        self.timreport()
        return self.allp.value, time.time()-self.starttime
    def stop(self):
        print "\n\nWaiting for the processes to terminate."
        if self.observer:
            self.observer.stop()
            self.observer.observer.join(1)   
        
        
        self.stopflag.value=1
        for worker in self.pool:
            print "join worker"
            worker.join(1)
        if self.dirwalker:
           
            self.dirwalker.join(1)
        print "empty pic queue"
        while True:
            try:
                self.picturequeue.get(False)
            except Empty:
                break
        print "empty hist queue"
        while True:
            try:
                self.histqueue.get(False)
            except Empty:
                break
        print "empty plot queue"
        while True:
            try:
                self.plotdataqueue.get(False)
            except Empty:
                break
        if os.sys.platform!="win32":
            try:
                self.histqueue.close()
                self.plotdataqueue.close()
            except Exception as e:
                print e
    def timreport(self):
        tottime=time.time()-self.starttime
        count=self.allp.value
        #print count
        if count==0:
            print "We didn't do any pictures "
        else:
            print "\n\nelapsed time: ",tottime
            print "\nProcessed: ",count," pic"
            print " time per pic: ", tottime/count,"[s]"
            print " pic per second: ",count/tottime,"[/s]"
        time.sleep(1)
        