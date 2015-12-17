 
 
from optparse import OptionParser
import re,os
from datetime import tzinfo, timedelta, datetime
import json,csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from scipy import misc
import tables as tb
import hashlib,pickle
import re
from jsonschema import validate,ValidationError
import os
import StringIO
#msilib import seems to cause an error on the cc01-cluster
#commented out by MB on Sept. 30th 15
#from msilib import Directory

def readtiff(imagepath):
    '''
    Read the tif header (#strings)
    '''
    f = open(imagepath, "rb")
    i=0
    data={"filename":os.path.basename(imagepath)}
  
    p = re.compile('[ -~]{4,100}')
    for line in f:
        for token in p.findall(line):
            m=re.match(r"(\d+):(\d+):(\d+)\s+(\d+):(\d+):(\d+)", token)
            if m:
                 data['date']=datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 
                                       int(m.group(4)), int(m.group(5)),int( m.group(6))
                                       ).isoformat()
            else:
                    m=re.match(r".+?(\w+)\s*[:=]\s*(.+)",token)
                    if m:
                        number=re.search("(\d+\.*\d*)\s+(\w+)",m.group(2))
                        if number:
                            
                            data[m.group(1)+" ["+number.group(2)+"]"]=float(number.group(1))
                           
                        else:
                            data[m.group(1)]={}
                            if re.match(r"^\s*\d+\s*$",m.group(2)):
                                data[m.group(1)]=int(m.group(2))
                            else:
                                data[m.group(1)]=m.group(2)
                    else:
                         
                        m=re.match(r"#\s*(.+?)([e\-\d\.]+)\s+([a-zA-Z]+)",token)
                        if m:
                            
                            data[m.group(1)+"["+m.group(3)+"]"]=float(m.group(2))
                           
                        else:
                            pass
                            #print token
                
        i+=1
        if i>20: break
    return data

def readlog(logfile):
    '''
    read CSV into pandas data frame
    '''
     
    dframe=pd.read_csv(logfile,sep="\t" )
    dframe[dframe.columns[0]]= (pd.to_datetime(dframe[dframe.columns[0]],unit="s"))
    dframe.reset_index()
    dframe=dframe.set_index(dframe.columns[0])
    return dframe

def imgtohdf(conf,imgdirectory,outputdirecory):
    '''
    add images in dir to hdf5 location
    '''
    filename=os.path.normpath(os.sep.join([os.path.normpath(outputdirecory),
                                       conf["OutputFileBaseName"]]))+".hdf"
    h5file = tb.open_file(filename, mode = "a", title = "Test file")
    print "open: "+filename
    try:
        group=h5file.get_node("/", "Images")
    except tb.exceptions.NoSuchNodeError:
        group = h5file.create_group("/", 'Images', 'Dedector Images')
   
    for path, subdirs, files in os.walk(imgdirectory):
        for name in files:
            if name.endswith('tif'):
                imagefilename=os.path.join(path, name)
                data=misc.imread(imagefilename)
                
                id="h"+hashlib.sha224(imagefilename).hexdigest()
                try:
                    h5file.get_node("/Images", id)
                except tb.exceptions.NoSuchNodeError:
                    
                    h5file.createArray(group, id , data,
                                   imagefilename)
    h5file.close()

def graphstohdf(conf,fileslist,outputdirecory):
    '''
    add images in dir to hdf5 location
    '''
    filename=os.path.normpath(os.sep.join([os.path.normpath(outputdirecory),
                                       conf["OutputFileBaseName"]]))+".hdf"
    h5file = tb.open_file(filename, mode = "a", title = "Test file")
    print "open: "+filename
    try:
        group=h5file.get_node("/", "Graphs")
    except tb.exceptions.NoSuchNodeError:
        group = h5file.create_group("/", 'Graphs', 'Plotable Graphs')
    for kind in fileslist:
        try:
            h5file.get_node("/Graphs", kind)
        except tb.exceptions.NoSuchNodeError:
            h5file.create_group("/Graphs", kind,   kind)
       
        
        for graphfile in fileslist[kind]:
            
            if kind=="JSON":
                jsondata=json.load(open(graphfile,"r"))
                 
                try:
                    imagefilename=jsondata[0]["Image"]
                except Exception as e:
                   
                    continue
                 
            else:
                chifile=open(graphfile,"r").readlines()
                imagefilename= chifile[0].split(",")[0]
            
            id="h"+hashlib.sha224(imagefilename).hexdigest()
            try:
                node= h5file.get_node("/Graphs/"+kind, id)
            except tb.exceptions.NoSuchNodeError:
                node= h5file.create_group("/Graphs/"+kind, id ,   imagefilename)
            if kind=="JSON":
                h5file.createArray(node, "JSON", json.dumps(jsondata,indent=2), "chifile" )
            else:
                h5file.createArray(node, "CHI", "".join(chifile), "chifile" )
    h5file.close()
    


def readimglog(filename):
    """
    Read the log files the detector writes along with the images
    """
    logf=open(filename) 
    logfstr=""
    for i,line in enumerate(logf):
        if i==0:
            continue
        elif line.startswith("----"):
            continue
        elif len(line.split())<3:
             logfstr+="NaN NaN " +line
        else:
            logfstr+=line
    df=pd.read_csv( StringIO.StringIO(logfstr), 
            sep=" ", 
            skipinitialspace=True,
            header=None , 
            names=["Time Requested","Time Measured","End Date Time" ,"File Name"],
            )
    df["End Date Time"]=pd.to_datetime(df["End Date Time"])
   
    return df
 
def readallimages(dir):
    """
    read header from all images and collect files list
    """
    frameinit=False
    imgframe=pd.DataFrame()
    imglogframe=pd.DataFrame()
    chilist=[]
    imagecount=0
    for path, subdirs, files in os.walk(dir):
        for name in files:
            if name.endswith('tif'):
                imgpath=os.path.join(path, name)
                print imgpath
                row=readtiff(imgpath)
                row['filepath']=imgpath
                row['id']="h"+hashlib.sha224(imgpath).hexdigest()
                rowframe=pd.DataFrame()
             
                rowframe=rowframe.append(row,ignore_index=True)
                rowframe["date"]=pd.to_datetime(rowframe['date'])
                rowframe=rowframe.set_index(["date"])
                
                
                    
                imgframe=imgframe.append(rowframe)
              
            elif  name.endswith('log'):
                logpath=os.path.join(path, name)
                imglogframe=imglogframe.append(readimglog(logpath))
            elif name.endswith("chi") or name.endswith("json") :
                chilist.append(os.path.join(path, name))
    
    imgframe.columns+=" (Img)"
    imglogframe.columns+=" (ImgLog)"
    
    print imgframe.columns
    print imglogframe.columns

    if True:
        imgframe["File Name (Img)"]=(imgframe["Image_path (Img)"]+imgframe['filename (Img)'])
        merged=pd.merge(imglogframe,imgframe, 
                        left_on="File Name (ImgLog)",
                        right_on= "File Name (Img)")
        merged=merged.set_index("End Date Time (ImgLog)")
    if False:
        merged=imgframe
        
    print merged.columns.values
    return merged,chilisttodict(chilist)
  
def compileconffromoptions(options, args):
    """
    If data merge is used as command line tool this compiles a json config according to 
    :ref:`consroot`
    
    """
    conf= {
     "TimeOffset": float(options.timeoffset), 
     "LogDataTables": [
       {
         "TimeOffset": 0.0, 
         "TimeEpoch":"Mac",
         "FirstImageCorrelation": options.syncfirst, 
         "Name": "Peak", 
         "Files": [
           {
             "RemotePath": [
                args[1]
             ],
            "LocalPath":""
           } 
         ]
       }, 
       {
         "TimeOffset": 0.0, 
    "TimeEpoch":"Mac",
         "FirstImageCorrelation": False, 
         "Name": "Dlog", 
         "Files": [
           {
             "RemotePath": [
               args[2]
             ],
            "LocalPath":""
           } 
           
         ]
       }
     ], 
     "OutputFormats": {
       "csv": False, 
       "hdf": False, 
       "exel": False, 
       "json": False
     }, 
     "OutputFileBaseName": "merged", 
     "HDFOptions": {
       "IncludeCHI": options.includechi, 
       "IncludeTIF": options.includetifdata
     }
    } 
    suffix=options.outfile.split(".")[-1]
    knownoutput=False
    for format in conf["OutputFormats"]:
        if suffix=="xls":
            conf["OutputFormats"]["exel"]=True
            knownoutput=True
        if suffix==format:
            conf["OutputFormats"][format]=True
            knownoutput=True
    #print json.dumps(conf,  indent=2)
    if not knownoutput:
        print options.outfile +": File format not supported."
    return conf
def merge():
    '''saxs data merger'''
    
    parser = OptionParser()
    usage = "usage: %prog [options] iMPicture/dir peakinteg.log datalogger.log"
    parser = OptionParser(usage)
    parser.add_option("-t", "--timeoffset", dest="timeoffset",
                      help="Time offset between logging time and time in imagedata.", metavar="SEC",default=0)
    parser.add_option("-1", "--syncfirst", dest="syncfirst",
                      help="Sync time by taking the time difference between first shutter action and first image.", 
                      action="store_true",default=False)
    parser.add_option("-o", "--outfile", dest="outfile",
                      help="Write merged dataset to this file. Format is derived from the extesion.(.csv|.json|.hdf)", metavar="FILE",default="")
    parser.add_option("-b", "--batch", dest="batch",
                      help="Batch mode (no plot).", 
                       action="store_true",default=False)
    parser.add_option("-c", "--includechi", dest="includechi",
                      help="Include radial intensity data (.chi) in hdf.", 
                       action="store_true",default=False)
    parser.add_option("-f", "--includetif", dest="includetifdata",
                      help="Include  all image data in hdf.", 
                       action="store_true",default=False)
                     
    parser.add_option("-C", "--conf", dest="conffile",
                      help="Use config in  FILE to merge the data (ignore other options) ", metavar="FILE",default="")
  
    (options, args) = parser.parse_args(args=None, values=None)
    if len(args)<1:
         parser.error("Incorrect number of arguments. --help for more")
        
    if options.conffile!="":
        conf=json.load(open(options.conffile,"r"))
    else:
        conf=compileconffromoptions(options, args)

    directory=args[0]
    mergedTable,filelists,plotdata=mergedata(conf,directory)
    if not options.batch:
        plt.show()
    
    writeTable(conf,mergedTable)
    writeFileLists(conf ,filelists)
    if conf["OutputFormats"]["hdf"] and conf['HDFOptions']["IncludeTIF"]:
        imgtohdf(conf,directory,".")
    if conf["OutputFormats"]["hdf"] and conf['HDFOptions']["IncludeCHI"]:
        graphstohdf(conf,filelists,".")
    
def writeTable(conf,mergedTable,directory="."):
    basename=os.path.normpath(os.sep.join([os.path.normpath(directory),conf["OutputFileBaseName"]]))
    for format in conf["OutputFormats"]:
        if conf["OutputFormats"][format]:
           
            if format=="json":
                mergedTable.to_json(basename+"."+format)
            elif format=="csv":
                mergedTable.to_csv(basename+"."+format)
            elif  format=="exel":
                mergedTable.to_excel(basename+"."+"xls")
                format="xls"
            elif format=="hdf":
                try:
                    os.remove(basename+"."+"hdf")
                except:
                    pass
                mergedTable.to_hdf(basename+"."+"hdf","LogData")
                
            print "write: " + basename+"."+format
def writeFileLists(conf ,filelists,directory=".",serverdir=""):
    basename=os.path.normpath(os.sep.join([directory,conf["OutputFileBaseName"]]))
    for kind in filelists:
        texfilename= basename+kind+".txt"
        listfile=open(texfilename,"w")
        for filename in filelists[kind]:
            
            listfile.write(os.path.normpath(filename[len(serverdir):])+"\n")
        listfile.close()
        print "write: " +texfilename

def cleanuplog(logframe,logTable):
    logframe.columns+=" ("+logTable["Name"]+")"
    logframe.index=logframe.index-timedelta(seconds=logTable["TimeOffset"])
    if logTable["TimeEpoch"]=="Mac":
       logframe.index=logframe.index- ( datetime.fromtimestamp(0)-datetime(1904, 1, 1, 0,0,0))
       
def chilisttodict(chi):
    chidict={}
    for chifile in chi:
        if chifile.endswith(".chi"):
            parts=chifile.split("_c")
            if len(parts)==1:
                basename=chifile[:-4]
                typelabel="R"
            else:
                basename="_c".join(parts[:-1]).split(os.sep)[-1]
                saxdogpart=parts[-1]
                typelabel=saxdogpart[0]
                nummatch=re.match(r"(\w\d+)",saxdogpart)
                if nummatch:
                    typelabel=nummatch.group(1)
                    
               
            if basename not in chidict:
                chidict[basename]=[{typelabel:chifile}]
            else:
                chidict[basename].append({typelabel:chifile})
        else:
             basename=chifile[:-5]
             if basename not in chidict:
                chidict[basename]=[{"JSON":chifile}]
             else:
                chidict[basename].append({"JSON":chifile})
            
    filelists={}
    for basename in sorted(chidict.keys()):
            fileset= chidict[basename]
            for file in fileset :
                kind= file.keys()[0]
                if kind in  filelists :
                    filelists[kind].append(file[kind])
                else:
                    filelists[kind]=  [file[kind]]
    return filelists

def mergelogs(conf,attachment=None,directory="."):
   
    schema=json.load(open(os.path.dirname(__file__)
                        +os.sep+'DataConsolidationConf.json'))
    validate(conf,schema)
  
    
    
    if not "LogDataTables" in conf:
         conf["LogDataTables"]=[]
    tablea=None
    tableb=None
    firstImage=None
    for tnumber,logTable in enumerate(conf["LogDataTables"]):
        
        for filenum ,logfile in enumerate(logTable["Files"]):
            if logfile["LocalPath"]=="":
                buffer=open(os.sep.join(logfile["RemotePath"]))
            elif attachment and json.loads(attachment[0])["filename"]==logfile["LocalPath"]:
                buffer=StringIO.StringIO(json.loads(attachment.pop(0))["data"])
            else:
                pass
                buffer=open(logfile["LocalPath"])
            tmplog=readlog(buffer)
            if filenum==0:
                logframe=tmplog
            else:
                logframe=logframe.append(tmplog).sort_index()
        cleanuplog(logframe,logTable)
        print conf["TimeOffset"]
        basename=os.path.normpath(os.sep.join([os.path.normpath(directory), logTable["Name"]]))
        print (basename+".csv")
        logframe.to_csv(basename+".csv")
   
        print timedelta(seconds=conf["TimeOffset"])
        logframe.index=logframe.index-timedelta(seconds=conf["TimeOffset"])
        if logTable["FirstImageCorrelation"]:
            firstImage=logframe.index.min()
            peakframe=logframe
        elif logTable["Name"]=="Peak":
            peakframe=logframe
        elif type(peakframe)==type(None):
            peakframe=logframe
        if tnumber >=1:
            tableb=logframe
            tablea=tablea.join(tableb, how='outer') 
        else:
            tablea=logframe
            
    return tablea,firstImage,peakframe

def mergedata(conf,dir,attachment=None):
    print "mergedata"
    logsTable,firstImage,peakframe=mergelogs(conf,attachment=attachment)
    imd,chi=readallimages(dir)
    mergedt= mergeimgdata(dir,logsTable,imd,peakframe,firstImage=firstImage)
    syncplotdata=syncplot(peakframe,imd)
    return mergedt,chi,syncplotdata

def mergeimgdata(dir,tablea,imd,peakframe,firstImage=None):
    index=[]
    for pos in range(imd.index.shape[0]):    
            index.append(imd.index[pos]-timedelta(seconds=(imd['Exposure_time [s] (Img)'][pos])))
    imd.index=index  
    if firstImage:
        delta=(imd.index.min()-firstImage)
        tablea.index=tablea.index+delta
        peakframe.index=peakframe.index+delta
        print "Time shift:" +str(delta)
    else:
        delta=timedelta(seconds=0)
    
    #basename= os.path.normpath(os.sep.join([os.path.normpath(directory),conf["OutputFileBaseName"]]))
    #imd.to_csv(basename+"imd.csv") 
    mergedt=imd.join(tablea,how="outer")
    #mergedt.to_csv(basename+"mergedt_join.csv")
    
    
    
    
    mergedt=imd.join(tablea,how="outer").interpolate(method="time")
    #mergedt.to_csv(basename+"mergedt_join_int.csv")
    
    for pos in range(0, imd.index.shape[0]):
        mergedt_pos = mergedt.index.get_loc(imd.index[pos])
        exp_time = mergedt['Exposure_time [s] (Img)'][mergedt_pos]
        if exp_time>=2:
            mergedt.index = pd.to_datetime(mergedt.index)
            mergedt_pos_t_start = mergedt.index.searchsorted(mergedt.index[mergedt_pos+1])
            mergedt_pos_t_stop = mergedt.index.searchsorted(mergedt.index[mergedt_pos] + timedelta(seconds=exp_time))
            time_sum = np.array(mergedt.index[mergedt_pos_t_stop], dtype='datetime64[ns]') -\
                       np.array(mergedt.index[mergedt_pos_t_start], dtype='datetime64[ns]')
            int = np.trapz(mergedt['Ioni         (Dlogger)'][mergedt_pos_t_start:mergedt_pos_t_stop].values,\
                  x=mergedt.index[mergedt_pos_t_start:mergedt_pos_t_stop].values)           
            mergedt['Ioni         (Dlogger)'][mergedt_pos]=int/time_sum
            int = np.trapz(mergedt['Shutter      (Dlogger)'][mergedt_pos_t_start:mergedt_pos_t_stop].values,\
                  x=mergedt.index[mergedt_pos_t_start:mergedt_pos_t_stop].values)           
            mergedt['Shutter      (Dlogger)'][mergedt_pos]=int/time_sum
            int = np.trapz(mergedt['Current      (Dlogger)'][mergedt_pos_t_start:mergedt_pos_t_stop].values,\
                  x=mergedt.index[mergedt_pos_t_start:mergedt_pos_t_stop].values)           
            mergedt['Current      (Dlogger)'][mergedt_pos]=int/time_sum
            int = np.trapz(mergedt['Pot          (Dlogger)'][mergedt_pos_t_start:mergedt_pos_t_stop].values,\
                  x=mergedt.index[mergedt_pos_t_start:mergedt_pos_t_stop].values)           
            mergedt['Pot          (Dlogger)'][mergedt_pos]=int/time_sum
            int = np.trapz(mergedt['Diode        (Dlogger)'][mergedt_pos_t_start:mergedt_pos_t_stop].values,\
                  x=mergedt.index[mergedt_pos_t_start:mergedt_pos_t_stop].values)           
            mergedt['Diode        (Dlogger)'][mergedt_pos]=int/time_sum
            #int = np.trapz(mergedt['Cur_Pot1     (Dlogger)'][mergedt_pos_t_start:mergedt_pos_t_stop].values,\
            #      x=mergedt.index[mergedt_pos_t_start:mergedt_pos_t_stop].values)           
            #mergedt['Cur_Pot1     (Dlogger)'][mergedt_pos]=int/time_sum

    #mergedt.to_csv(basename+"mergedt_join_manint.csv")
    mergedt=mergedt[mergedt.index.isin(imd.index)]
    #smergedt.to_csv(basename+"mergedt_join_int_isin.csv")
    
    #mergedt=imd.join(tablea,how="outer").interpolate(method="zero")
    #mergedt=mergedt[mergedt.index.isin(imd.index)]
    
    return mergedt,delta
def syncplot(shiftedreduced,imd):
        imd['Exposure_time [s] (Img)'][:].plot(style="ro")  
        shiftedreduced['Duration (Peak)'][shiftedreduced['Duration (Peak)']>0].plot(style="x")
        plt.legend( ('Exposure from Images', 'Exposure from Shutter'))
        plt.xlabel("Time")
        plt.ylabel("Exosure Time [s]")
        plt.title("Corellation")
       
        data= {"Images":json.loads(pd.DataFrame(imd['Exposure_time [s] (Img)']).to_json(orient="index")),
                "Shutter":json.loads(pd.DataFrame(shiftedreduced['Duration (Peak)']).to_json(orient="index"))}
        
        
        return data
if __name__ == '__main__':
    merge()
   
