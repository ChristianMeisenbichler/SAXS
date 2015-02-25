'''
Created on 22.04.2014

@author: chm
'''
 
import numpy as np
from scipy import misc
import matplotlib.pyplot as plt
import scipy.sparse as sp
import json
import pickle
import hashlib, binascii
import os, sys
from threading import Thread,current_thread,active_count 
import StringIO,base64
#from numba import jit
 
from jsonschema import validate
"""
Module ...
"""
class calibration:
    """
    This class represents a calibration for SAXS diffraction. 
    After initialization, the :py:meth:`integrate` method can compute the radial intensity very fast.
    
    :param string config: is the path to the :ref:`root`:
 
    """
    
    def __init__(self,config,mask=None,attachment=None):
        
        if type(config) is str:
            #open config and check schema
            caldict=json.load(open(config))
        elif  type(config) is dict:
            caldict=config
           
        else:
            print "calibrarion takes a config object as path or dictionary"
            raise TypeError (config)
        schemapath=os.path.dirname(__file__)+'/schema.json'
       
        schema=(json.load(open(schemapath)))
        validate(caldict,schema)
        #calculate a hash for all configdata
  
        self.config=caldict
        if not mask:
            mask=caldict["Masks"][0]
        self.maskconfig=mask
    
        self._setupcalibration(mask,attachment)
         
 
    
    def polcorr(self,Pfrac,rot):
        complexp=self.__complexCoordinatesOfPicture(1)
        pixelsize=self.config["Geometry"]['PixelSizeMicroM'][0]*1e-3 #
        r=np.absolute(complexp)*pixelsize
        phi=np.angle(complexp)
        
      
        d=self.config["Geometry"]['DedectorDistanceMM']
        tilt=self.config["Geometry"]['Tilt']['TiltAngleDeg']/180.0*np.pi
        tiltdir=self.config["Geometry"]['Tilt']['TiltRotDeg']/180.0*np.pi
        
        theta=calc_theta(r,phi,d,tilt,tiltdir)
       
        
       
        corr=(Pfrac*(1.0 -np.square(np.sin(phi-rot)*np.sin(theta)))+
            (1.0-Pfrac)*(1.0-np.square(np.cos(phi-rot)*np.sin(theta))))
       
        return corr

    def _setupcalibration(self,mask,attachment):
        """
        Pre-calculate the data for the integration. This is done at initialization.
        """
        
       
        # Calculate array of size img with the distance from center as entries
        pixelsize=self.config["Geometry"]['PixelSizeMicroM'][0]*1e-3 #all length in millimeters
        oversampling=mask['Oversampling']
        complexp=self.__complexCoordinatesOfPicture(oversampling)
        r=np.absolute(complexp)*pixelsize
        phi=np.angle(complexp)

        d=self.config["Geometry"]['DedectorDistanceMM']
        tilt=self.config["Geometry"]['Tilt']['TiltAngleDeg']/180.0*np.pi
        tiltdir=self.config["Geometry"]['Tilt']['TiltRotDeg']/180.0*np.pi
        theta=calc_theta(r,phi,d,tilt,tiltdir)
        self.corr=np.ones((self.config["Geometry"]['Imagesize'][0],self.config["Geometry"]['Imagesize'][1]))
        if 'PolarizationCorrection' in self.config:
            frac = self.config["PolarizationCorrection"]
             #Nanometer
            self.corr=np.divide(self.corr,self.polcorr(frac['Fraction'], frac['Angle']/180.0*np.pi-np.pi/2))
        # rescale the theta that the radial regions connected to a label are about 1 pixel wide
        if 'PixelPerRadialElement' in mask:
            self.scale=1/np.max(theta)*np.max(r)/pixelsize/mask['PixelPerRadialElement']
            pixelper=mask['PixelPerRadialElement']
        else:
            pixelper=1.0
            self.scale=1/np.max(theta)*np.max(r)/pixelsize
        
        labels=np.array(theta*self.scale,dtype=int)
        self.maxlabel=np.max(labels)
        mask=openmask(mask["MaskFile"],attachment)
        self.A=labelstosparse(labels,mask,oversampling)
        self.ITransposed =self.A
        self.I,self.Areas,self.oneoverA=rescaleI(self.A,self.corr)
        
        self.thetagrid=(np.arange(self.maxlabel+1)+0)/self.scale   
        if "Wavelength" in self.config:
            Angstrom=1.00001495e-1
            self.qgrid=4*np.pi*np.sin(self.thetagrid/2)/self.config['Wavelength']/Angstrom
        
      
    def integrate(self,image):
        """
        Integrate a picture.
        
        :param numpy.array(dim=2) image: Sensor image to integrate as 2d `NumPy` array 
        :returns: Returns Angle and intensity vector as a tuple (angle,intensity)
        """
        return  (self.thetagrid,self.I.dot(image.flatten() ))
    def integratechi(self,image,path):
        """
        Integrate and save to file in "chi" format.
        
        :param np.array() image: Image to integrate as numpy array
        :param string path: Path to save the file to
        :returns: Scattering curve data as numpy array 
        """
        r= self.I.dot(image.flatten() )

        data=np.array([self.qgrid[len (self.qgrid)-len(r):] , r , np.sqrt(r*self.Areas) *self.oneoverA]).transpose()
      
        
        headerstr=path+"\n"
        headerstr+="q [nm^-1]\n"
        headerstr+="Intensity\n"
        headerstr+="   "+str(data.shape[0])+""
        
        np.savetxt(path, data, fmt='%.18e', delimiter=' ', newline='\n ', header=headerstr, footer='', comments='')
        
        
        
        return data.transpose()
   
    def integrateerror(self,image):
        """
        Integrates an image and computes error estimates.
        
        :param np.array() image: Image to integrate as numpy array
        :returns: The intensity the standard deviation and the Poisson statistics error in a numpy array.
        """
        radial=self.I.dot(image.flatten()) 
        means=self.ITransposed.dot(radial*self.Areas)
        dev=np.square(image.flatten()-means)
        stddev=np.sqrt(self.I.dot(dev))
        poissonerr=np.sqrt(radial*self.Areas)*self.oneoverA
        rsq=(2*np.sin(self.thetagrid)*self.config['DedectorDistanceMM']
             *np.pi*self.config['PixelSizeMicroM'][0]*1e-3**2)
        return  np.array([radial,stddev ,poissonerr])
    
    def plot(self,image,outputfile="",startplotat=0 ,fig=None):
        """
        Plot integrated function for image in argument.
        
        :param numpy.array(dim=2) image: Sensor image to integrate as 2d `NumPy` array
        :param string outputfile: File to write plot to. Might be any image format supported by matplotlib.
        :param integer startplotat: radial point from which to start the plot
        """
        ## Do not use that in a multithread environment!!
        #if active_count()>0:
       
            
                    
        fun=self.integrateerror(image)
       
        nonzero=fun[0]>0
        #print "error:" ,np.sum(fun[1][nonzero])
        if not fig:fig=plt.figure()
        fig.clf()
        
        ax = fig.add_subplot(111)
        ax.fill_between( self.qgrid[nonzero], np.clip(fun[0][nonzero]-fun[1][nonzero],1,1.0e300),fun[0][nonzero]+fun[1][nonzero],facecolor='yellow' ,linewidth=0,alpha=0.5)
        ax.fill_between( self.qgrid[nonzero], np.clip(fun[0][nonzero]-fun[2][nonzero],1,1.0e300),fun[0][nonzero]+fun[2][nonzero],facecolor='blue' ,alpha=0.2,linewidth=0)
        ax.plot(self.qgrid[nonzero],fun[0][nonzero])
      
        
        plt.ylabel('Intensity [counts/pixel]')
        plt.xlabel('q [1/nm]')
        plt.yscale('log')
        plt.title(outputfile)
        
       
      
        if outputfile=="":   
               #.show()
               pass
        else:
               fig.savefig(outputfile)
         
        return fig
         
            
    
    
       
   
    def __complexCoordinatesOfPicture(self,oversampling):
        """
        Generates array containing coordinates relative to beam center as complex numbers. 
        This is used to calculate the angles
        
        :param obj config:
        :param int oversampling:
        """
        imagesize=self.config["Geometry"]['Imagesize']
        beamcenter=self.config["Geometry"]['BeamCenter']
        return cplwcener(imagesize,beamcenter,oversampling)
def cplwcener(imagesize,beamcenter,oversampling):
        return np.add.outer(
                         1j*(np.arange(0,
                                             imagesize[0],
                                             1./oversampling,
                                             dtype=np.float_)
                                   -imagesize[0]
                                   +beamcenter[0]),
                        (np.arange(0,
                                             imagesize[1],
                                             1./oversampling,
                                             dtype=np.float_)
                                   - beamcenter[1])
                         )

def labelstosparse(labels,mask,oversampling):
        ind=np.argsort(labels.flatten())
        sortedl=labels.flatten()[ind]
        newcol=sortedl-np.roll(sortedl,1)
        length=sortedl.shape[0]
        coli=np.array(np.where(newcol>0)[0])
        coliptr= np.concatenate(([0],coli,[length]))
        m= sp.csc_matrix((np.ones(length),ind,coliptr))
        sc=scalemat(mask.shape[0],mask.shape[1],oversampling)
        A=sp.csc_matrix((sc.dot(m)))
        return sp.csc_matrix((A.data*mask.flatten()[A.indices],A.indices,A.indptr))

def rescaleI(sparse,corr):
        areas=sparse.transpose().dot(np.ones(sparse.shape[0]))
        #corect for sensor shape 
        areaswithoutzero=np.where(areas>0.0 ,areas,-1.0)
        oneoverA=np.where(areaswithoutzero>0,1.0/areaswithoutzero,0)
        #calculate factors for area
        l=sparse.indptr
        b=np.roll(sparse.indptr,1) # l-b is repeating count for each column
        #update sparse data
        data=sparse.data*np.repeat(oneoverA,(l-b)[1:])*corr.flatten()[sparse.indices] 
        sparse.data=data
        return sparse.transpose(), areas,  oneoverA
def calc_theta(r,phi,d,tilt,tiltdir):
        """
        Calculates the difraction angle from pixel coordinates. It does work when called with arrays. 
        See :ref:`geometry`
        
        :param float r: Distance to beamcenter.
        :param float phi: Angle[rad] from polar sensor plane coordinates.
        :param float d: distance to difraction center.
        :param float tilt: Angle[rad] of sensor plane tilt.
        :param float tiltdir: Angle[rad] of direction of tilt.
        :returns:  theta
        """
        alpha=np.arcsin(np.sin(tilt)*np.sin(phi+tiltdir+np.pi/2))
        lsquared=d**2 +r**2 -2*d*r*np.cos(np.pi/2+alpha)
        return np.arccos(-(r**2-lsquared-d**2)/(2*np.sqrt(lsquared)*d))
    
   
        
def scalemat(Xsize,Ysize,ov):
        """
        Computes a scaling projection for use in computing the pixel weights for integration
        
        :param int Xsize: Picture size in X direction.
        :param int Ysize: Picture size in Ydirection.
        :param int ov: Number of oversampling ticks in x ynd y direction
        :param array corr: Polarizationn an other correction factors
        :returns: sparce matrix toing the scaling
        """
    
        cell=np.add.outer(np.arange(ov)*Ysize*ov,np.arange(ov))
        grid=np.add.outer(np.arange(0,Xsize*Ysize*ov*ov,Ysize*ov*ov),np.arange(0,Ysize*ov,ov))
        cindices=np.add.outer(grid,cell).flatten()
        return sp.csr_matrix((np.ones(len(cindices))/ov**2,
                     cindices,
                     np.arange(0,Ysize*Xsize*ov**2+1,ov*ov)),
                    dtype=np.float,shape=(Ysize*Xsize,Ysize*Xsize*ov**2))
     
    
def openmask(mfile,attachment=None):
    """
    Open the mask file especialy the \*.msk file. Unfortunately there is no library
    module for msk files available also no documentation. So, for the msk file, we have a very brittle hack
    it works for our sensor. Nevermind any other resolution or size.
    
    :param object config: Calibration config object.
    :returns: Mask as logical numpy array.
    """
    if attachment:
        mfilestream=  base64.b64decode(attachment['data'])
    else:
        mfilestream=open(mfile).read()
    if mfile.endswith('.msk'):
        import bitarray
        maskb=bitarray.bitarray( endian='little')
        
        maskb.frombytes(mfilestream) 
        maskl=np.array(maskb.tolist())
        fin=open(mfile , "rb")
        import struct
        fin.seek(0x10)
        (y,)= struct.unpack('i', fin.read(4))
        fin.seek(0x14)
        x,=struct.unpack('i', fin.read(4))
        word=32
        padding= word - y % word
        yb=y+padding
        off=8192
        mask=maskl[off:x*yb+off].reshape(x, yb)
        cropedmask=np.flipud(mask[0:x,0:y])
        # save the mask in order to controll if it worked
        #misc.imsave("mask.png",cropedmask)
        return  np.logical_not(cropedmask)
    else:
        mask= np.where(misc.imread(mfilestream)!=0,False,True)
        print mask
        return mask
