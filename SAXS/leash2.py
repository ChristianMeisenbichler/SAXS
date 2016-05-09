
from PyQt4 import  QtGui
from PyQt4 import  uic
from PyQt4 import  QtCore
import sys,os
import connectdialog
import calibeditor
import leashmenue
import Leash
import json
from jsonschema import validate,ValidationError
import plotdatathread
import plotpanel
import histpanel
import checkServerCalibchanged
import collections
import consolidatepanel
from multiprocessing import Process,Value
from Server import saxsdogserver
from PyQt4.Qt import QMessageBox
class LeashUI(QtGui.QMainWindow):
    def __init__(self,app,parent=None):
        super(LeashUI,self).__init__(parent)
        self.clipboard=app.clipboard()
        try:
            self.confs=json.load(open(os.path.expanduser("~"+os.sep+".saxsdognetwork")))
        except IOError:
            self.confs=[]
        try:
            validate( self.confs,json.load(open(os.path.dirname(__file__)+os.sep+'NetworkSchema.json')))
        except ValidationError as e:
            errormsg=QtGui.QErrorMessage(parent=self)
            errormsg.setWindowTitle("Your SAXSDog Network is not configured correctly)")
            errormsg.showMessage(str(e))
            errormsg.exec_()
            sys.exit()
        
            
        self.connectdialog=connectdialog.connectdialog( self.confs,self)
        self.connectdialog.exec_()
        selected=self.connectdialog.confindex
        if  self.connectdialog.ok:
            if selected>=0:
                reconnectresult=self.connectdialog.serverstatus[selected].result
            else:
                reconnectresult={}
        else:
            sys.exit()
        self.netconf=self.confs[selected]
       
        self.localserver=None
        if selected==-1:
            dirdialog=QtGui.QFileDialog()
            serverdir=dirdialog.getExistingDirectory(parent=self, caption="Choose the Image Data Directory")
            self.localserverstop=Value('i',0)
            self.localserver=Process(target=saxsdogserver,
                                     args=(self.confs[-1],"Local",self.localserverstop,unicode(serverdir)))
            self.localserver.start()
        self.parscecommandline()
        self.loadui(reconnectresult)
        self.setLocale(QtCore.QLocale("C"))
        if not "Name" in self.netconf:
            self.netconf["Name"]="Unnamed"
    def loadui(self,reconnectresult):
        
        self.mainWindow=super(LeashUI,self)
        self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash")
        self.appdir=os.path.dirname(__file__)+os.sep
        self.mainWindow.setWindowIcon(QtGui.QIcon(self.appdir+"icons"+os.sep+"program.png"))
        self.tab=QtGui.QTabWidget()
        self.calib=QtGui.QWidget()
        self.caliblayout=QtGui.QHBoxLayout()
        self.calib.setLayout(self.caliblayout)
        self.calibeditor=calibeditor.calibeditor(self)
        self.caliblayout.addWidget(self.calibeditor)
        self.submitlayout=QtGui.QVBoxLayout()
        self.caliblayout.addLayout(self.submitlayout)
        self.queuestatuslabel=QtGui.QLabel("No queue on server.")
        self.filestatuslabel=QtGui.QLabel("")
        self.submitbutton=QtGui.QPushButton("Start Server Queue")
        self.submitlayout.addWidget(self.queuestatuslabel)
        self.submitlayout.addWidget(self.filestatuslabel)
        self.submitlayout.addWidget(self.submitbutton)
        self.submitlayout.addStretch()
        self.tab.addTab( self.calib , "Calib")
        self.plotpanel=plotpanel.plotpanel(self.tab)
        plottab=self.tab.addTab( self.plotpanel , "Plots")
        
        
        self.histpanel=histpanel.histpanel(self)
        self.tab.addTab( self.histpanel , "History")
        self.mainWindow.setCentralWidget (self.tab  )
        self.connect(self.submitbutton,QtCore.SIGNAL('clicked()'),self.startqueue)
        self.connect(self.calibeditor.model,QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),self.statusmodified)
        self.errormessage=QtGui.QErrorMessage()
        self.menue=leashmenue.menueitems(self)
        self.connect(self.calibeditor.model, QtCore.SIGNAL("fileNameChanged()"),self.updatewindowtitle)
        self.plotthread=plotdatathread.plotthread(self)
        self.connect(self.plotthread,QtCore.SIGNAL("plotdata(QString)"),self.plotpanel.plot)
        self.connect(self.plotthread,QtCore.SIGNAL("plotdata(QString)"),self.histpanel.plot)
        self.connect(self.plotthread,QtCore.SIGNAL("histupdate(QString)"),self.histpanel.timestep)
      
        
        if not  self.localserver:
            self.checkServerCalibchanged=checkServerCalibchanged.checkServerCalibChangedThread(self)
            self.connect(self.plotthread,QtCore.SIGNAL("ServerQueueTimeChanged()"),  self.checkServerCalibchanged.start)
            self.connect(self.checkServerCalibchanged,QtCore.SIGNAL("ServerQueueChanged(QString)"),self.notifyServerChange)
        if  reconnectresult and reconnectresult["result"]=="cal":
            self.calibeditor.model.loadservercalib(reconnectresult)
            self.calibeditor.reset()
            self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: Server Calibration")
            self.setqueuesynced()
           
        elif len(self.args)>0:
            filename=self.args[0]
            self.calibeditor.model.loadfile(filename)
            self.calibeditor.reset()
            self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: "+filename)
            self.menue.appendrecentfile(filename)
        
        self.plotthread.start()
        self.consolidatepanel=consolidatepanel.consolidatepanel(self)
        self.tab.addTab( self.consolidatepanel , "Consolidate")
    def parscecommandline(self):
      
        self.options,self.args= Leash.parsecommandline()
    def startqueue(self):
        data=self.calibeditor.model.getjson()
        self.calibeditor.model.save()
        argu=["new", data]
        result={}
        title = str(data['Title'])
        usrfolder = str(data['Directory'][0])
        titlestr='The title and the selected user folder do NOT match. Are you sure you are user: ' + str(usrfolder) +' ?' 
        if title.find(usrfolder)==-1:
            res=QMessageBox.warning(self, self.tr("User folder"),self.tr(titlestr), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        else:
            res = QMessageBox.Yes
        if res==QMessageBox.Yes:
            try:
                result=json.loads(Leash.initcommand(self.options,argu,self.netconf))
            except Exception as e:
                self.errormessage.setWindowTitle("Server Error")
                self.errormessage.setMinimumSize(400, 300)
                self.errormessage.showMessage( str(e))
            if 'result' in result and result['result']=="new queue":
                self.setqueuesynced()
                self.plotthread.start()
            else:
                self.errormessage.setWindowTitle("Server Error")
                self.errormessage.setMinimumSize(400, 300)
                self.errormessage.showMessage( result["data"]["Error"])
    def setqueuesynced(self):
        self.queuestatuslabel.setText("Queue started.")
        self.filestatuslabel.setText("Local calibration synced")
        if self.calibeditor.model.filename:
            self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: "+self.calibeditor.model.filename)
        else:
            self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: Servercalibration")
    def statusmodified(self):
        self.filestatuslabel.setText ("Local calibration modified.")
        if self.calibeditor.model.filename:
            self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: "+self.calibeditor.model.filename)
        else:
            self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: Servercalibration")
    def updatewindowtitle(self):
        self.mainWindow.setWindowTitle(self.netconf["Name"]+" SAXS Leash: "+self.calibeditor.model.filename)
    def notifyServerChange(self,serverdata):
        message =QtGui.QMessageBox()
        message.setText("The Server Calibration Changed")
        message.setInformativeText("Do you want to load the new Calibration from the server")
        message.setStandardButtons( message.Cancel)
        Okbutton=message.addButton( "Load", message.AcceptRole)
        result=message.exec_()
       
        if result==0:
              ServerData=json.loads(unicode(serverdata),object_pairs_hook=collections.OrderedDict)
              self.calibeditor.model.loadservercalib(ServerData)
              self.calibeditor.reset()
    def cleanup(self):
        
        if  self.localserver:
            self.localserverstop.value=1
            argu=["abort"]
            result=json.loads(Leash.initcommand(self.options,argu,self.netconf))
        
def LeashGUI():
    
    app=QtGui.QApplication(sys.argv)
    form=LeashUI(app)
    form.show()
    app.exec_()
    form.cleanup()
if __name__ == "__main__":
   
    LeashGUI( )