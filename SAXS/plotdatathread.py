import json,os
import atrdict
import numpy as np
from Leash import initcommand
import time
from PyQt4 import  QtGui
from PyQt4 import  QtCore
class plotthread(QtCore.QThread):
    def __init__(self,app):
         super(plotthread, self).__init__()
         self.app=app
         self.lastcount=0
         self.queuestarttime=None
    def run(self):
        self.queuestarttime=None
       
        while True:
            resultstr=initcommand(self.app.options,["stat"],self.app.netconf)
            result=json.loads(resultstr)
            time.sleep(1)
            if 'start time' in result['data']["stat"]:
                starttime=result['data']["stat"]['start time']
                if self.queuestarttime and self.queuestarttime!=starttime:
                    self.emit(QtCore.SIGNAL('ServerQueueTimeChanged()'))
            
                self.queuestarttime=starttime
                
            if ( 'images processed' in  result['data']["stat"]):
                
                if(result['data']["stat"]['images processed']!=self.lastcount):
                    self.lastcount=result['data']["stat"]['images processed']
                   
                   

                    plotdata=result=initcommand(self.app.options,["plotdata"],self.app.netconf)
                    self.emit(QtCore.SIGNAL('plotdata(QString)'), plotdata)
                else:
                    self.emit(QtCore.SIGNAL('histupdate(QString)'),resultstr)
            elif result["result"]=="Error":
                self.emit(QtCore.SIGNAL('ProtocolError(QString)'), plotdata)
            