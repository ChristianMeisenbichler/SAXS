from PyQt4.QtCore import *
from PyQt4.QtGui import  *
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import json,os
import atrdict
import numpy as np
from Leash import initcommand
import time
class plotthread(QThread):
    """
    Thread to handle requesting data over the network and prepare 
    figures for displaying in  the main thread.
    """
    def __init__(self,mw):
        QThread.__init__(self)
        self.mw=mw
        mw.data.rate=np.zeros(50)
        mw.data.time=np.ones(50)
        mw.plotthreadgo=True
        self.yscale="symlog"
    def setyscale(self,state):
        """
        On check state changed from y-scale check box widget
        """
        if state==0:
            self.yscale="linear"
        else:
            self.yscale="symlog"
        self.emit( SIGNAL('update(QString)'), "changed scale" )
    def run(self):
        """
        special method of Qtread subclass. this is caled when the .start() method is called to 
        initiate the thread.
        """
        mw=self.mw
        ax = mw.figure.add_subplot(111)
        axhist=mw.figurehist.add_subplot(111)
        ax.set_ylabel('Intensity [counts/pixel]')
        ax.set_xlabel('q [1/nm]')
        axhist.set_ylabel('Rate')
        axhist.set_xlabel('time')
        conf=json.load(open(os.path.expanduser("~"+os.sep+".saxsdognetwork")))
        argu=["plotdata"]
        o=atrdict.AttrDict({"server":""})
        result=initcommand(o,argu,conf)
        # discards the old graph
        ax.hold(False)
        # plot data
        object=json.loads(result)
        if object['result']=="Empty":
           pass
        else:
            try:
                data=np.array(object['data']['array']).transpose()
                data[data==0]=np.NaN
                skip=0
                clip=1
                clipat=0
                ax.plot(data[skip:-clip,0],data[skip:-clip,1])
                ax.fill_between( data[skip:-clip,0] ,
                                 np.clip(data[skip:-clip,1]-data[skip:-clip,2],clipat,1e300),
                                 np.clip(data[skip:-clip,1]+data[skip:-clip,2],clipat,1e300),
                                 facecolor='blue' ,alpha=0.2,linewidth=0,label="Count Error")
                #ui.figure.title(object['data']['filename'])
                ax.set_yscale(self.yscale)
            except:
                pass
        try:
            mw.data.stat=object['data']["stat"]
            mw.data.rate[0]=mw.data.stat['pics']/mw.data.stat['time interval']
           
            mw.data.time[0]=mw.data.stat['time interval']+ mw.data.time[1]
           
            axhist.plot(mw.data.time,mw.data.rate,lw=2)
            axhist.fill_between(mw.data.time,0,mw.data.rate,alpha=0.4)
            axhist.set_ylim( [0,np.max(mw.data.rate)])
            axhist.set_xlim( [np.min(mw.data.time),np.max(mw.data.time)+1])
            axhist.set_ylabel('Rate [/s]')
            axhist.set_xlabel('Time [s]')
            mw.data.time=np.roll(mw.data.time,1)
            mw.data.rate=np.roll(mw.data.rate,1)
            axhist.hold(False)
        except:
            pass
            # refresh canvas
        self.emit( SIGNAL('update(QString)'), "data plotted" )
