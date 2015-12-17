import numpy as np
from  calibration import openmask,labelstosparse
import json
def yDirSliceProjector(y,x,x1,x2,mask):
    a=np.repeat(np.arange(x),y).reshape((x,y))
    maskx=np.ones((x,y),dtype=bool)
    maskx[np.logical_not(mask)]=0
    maskx[:,:x1]=0
    maskx[:,x2:]=0
    return labelstosparse(a, maskx,1)
def xDirSliceProjector(y,x,y1,y2,mask):
    a=np.tile(np.arange(y),x).reshape(x,y)
    masky=np.ones((x,y),dtype=bool)
    masky[np.logical_not(mask)]=0
    masky[:(x-y2)]=0
    masky[(x-y1):]=0
    return labelstosparse(a, masky,1)
 
class slice():
    """ 
    Initializes slice integration
    
    :param dictionary conf:  Detector calibration
    :param dictionary sliceconf: The part of detector calibration which deals with this slice.
    :param dictionary attachments: Mask data.
    
    """
    def __init__(self,conf,sliceconf,attachments=[]):
         
        x=conf["Geometry"]["Imagesize"][1]
        y=conf["Geometry"]["Imagesize"][0]
        self.x=x
        self.y=y
        self.kind="Slice"
        self.conf=conf
        self.qname=""
        self.sliceconf=sliceconf
        start=sliceconf["CutPosition"]-sliceconf["CutMargin"]
        stop=sliceconf["CutPosition"]+sliceconf["CutMargin"]
        if len (conf["Masks"])>0 and sliceconf['MaskRef']>=0:
             
            if  len ( attachments)>sliceconf['MaskRef']:
                attachment=attachments[sliceconf['MaskRef']]
            else:
                atachment=None
            self.mask=openmask(conf["Masks"][sliceconf['MaskRef']]["MaskFile"], attachment=attachment   )
        else:
            self.mask=np.zeros((x,y))
        if len(conf["Geometry"]['PixelSizeMicroM'])==1:
            conf["Geometry"]['PixelSizeMicroM'].append(conf["Geometry"]['PixelSizeMicroM'][0])
       
        if sliceconf["Direction"]=="x":
            self.Projector=xDirSliceProjector(x,y,start,stop,self.mask).transpose()
 
        elif sliceconf["Direction"]=="y":
            self.Projector=yDirSliceProjector(x,y,start,stop,self.mask).transpose()
 
        else :
            raise Exception("Invalid Direction: "+ sliceconf["Direction"])
        self.makegrid()
        self.areas=self.Projector.dot(np.ones((x,y)).flatten())
        #areaswithoutzero=np.where(self.areas>0.0 ,self.areas,-1.0)
        self.oneoverA=np.where(self.areas>0.0,1.0/self.areas ,np.NAN)
        
    def integrate(self,picture):
        return self.Projector.dot(picture.flatten())*self.oneoverA
   
    def integratechi(self,image,path,picture):
        """
        Integrate and save to file in "chi" format.
        
        :param np.array() image: Image to integrate as numpy array
        :param string path: Path to save the file to
        :returns: Scattering curve data as json structure
        """
        r= self.Projector.dot(image.flatten() ) 
        data=np.array([self.grid,
                        r *self.oneoverA, 
                        np.sqrt(r) *self.oneoverA # Poisson Error scaled
                      ]).transpose()
        collabels=[ self.qname,
                    "Intensity (Count/Pixel)",
                    "Error Margin"]
        headerstr=  json.dumps(self.conf)+"\n"
        headerstr+=json.dumps(collabels)+"\n"
        headerstr+="Intensity\n"
        headerstr+="   "+str(data.shape[0])+""
        np.savetxt(path, data, fmt='%.18e', delimiter=' ', newline='\n ', header=headerstr, footer='', comments='')
        
        return {"array":data.transpose().tolist(),
                    "columnLabels":collabels,
                    "kind":"Slice",
                    "conf":self.conf,
                    "slice":self.sliceconf}
    def plot(self,image,outputfile="",startplotat=0 ,fig=None):
        """
        dummy function in order to not trip up image queue
        """
        pass
    def makegrid(self):
        Angstrom=1.00001495e-1
        if ((self.sliceconf["Plane"]=="Vertical" and self.sliceconf["Direction"]=="y")
            or(self.sliceconf["Plane"]=="InPlane" and self.sliceconf["Direction"]=="x")):
            VerticalPixelN=self.y
            HorizontalPixeN=self.x
            VerticalBeamCenter=VerticalPixelN-self.conf["Geometry"]['BeamCenter'][0]
            HorizontalBeamCenter=self.conf["Geometry"]['BeamCenter'][1]
            VerticalPixelsize=self.conf["Geometry"]['PixelSizeMicroM'][0]/1000.0
            HorizontalPixelsize=self.conf["Geometry"]['PixelSizeMicroM'][1]/1000.0
        elif ((self.sliceconf["Plane"]=="Vertical" and self.sliceconf["Direction"]=="x")
            or(self.sliceconf["Plane"]=="InPlane" and self.sliceconf["Direction"]=="y")):
            VerticalPixelN=self.x
            HorizontalPixeN=self.y
            VerticalBeamCenter=self.conf["Geometry"]['BeamCenter'][1]
            HorizontalBeamCenter=HorizontalPixeN-self.conf["Geometry"]['BeamCenter'][0]
            VerticalPixelsize=self.conf["Geometry"]['PixelSizeMicroM'][1]/1000.0
            HorizontalPixelsize=self.conf["Geometry"]['PixelSizeMicroM'][0]/1000.0
        else:
            raise Exception("Invalid Plane orientation: "+ self.sliceconf["Plane"])
        alphaF=np.arctan((np.arange(VerticalPixelN,dtype=np.float)-VerticalBeamCenter)
                       * VerticalPixelsize
                       /self.conf["Geometry"]['DedectorDistanceMM']
                       )
        twothetaF=np.arctan((np.arange(HorizontalPixeN,dtype=np.float)- HorizontalBeamCenter)
                                 * self.conf["Geometry"]['PixelSizeMicroM'][1]/1000.0
                                 /self.conf["Geometry"]['DedectorDistanceMM']
                                 )
        if self.sliceconf["Plane"]=="Vertical":
            self.qname="GISAXS Scattering Vector $q_{z} [nm^{-1}]$"
            self.grid=2.0*np.pi/self.conf['Wavelength']/Angstrom*(np.sin(alphaF)
                                                  +np.sin(self.sliceconf["IncidentAngle"]/180.0*np.pi))
        elif self.sliceconf["Plane"]=="InPlane":
            self.qname="GISAXS Scattering Vector  $ q_{y} [nm^{-1}]$"
            self.grid=2.0*np.pi/self.conf['Wavelength']/Angstrom*(np.sin(twothetaF)
                                                    *np.cos( alphaF[self.sliceconf["CutPosition"]]))
       