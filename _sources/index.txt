.. SAXS documentation master file, created by
   sphinx-quickstart on Wed Jun  4 10:53:22 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================
SAXS's documentation!
=====================


.. image::  tugwhite.svg

 
The SAXS Python package implements analysis tools for Small Angle X-Ray Scattering 
(SAXS) data analysis.
The first and most important one is to efficiently integrate 2d sensor data to an angle dependent
diffraction curve.



.. plot:: 
 
   import SAXS
   arg=["../doc/data/powder.chi"]
   o={}
   o=SAXS.AttrDict(o)
   o['compare']=False
   o.log=False
   o.yax='linear'
   o.xax='linear'
   o.title="Diffraction Curve"
   o.legend=False
   o.plotfile=""
   o.skip=13
   o.clip=40
   SAXS.makeplot(o,arg)
   
The SAXS module consists of a Python library and 3 command line tools: :ref:`saxsdog`, :ref:`plotchi` 
and :ref:`converter`



.. toctree::
   :maxdepth: 2
   
   install
   TheTools
   SAXSSchemaDoc
   TheTechnology
   Server
   SAXSapi
 


.. image::  tugwhite.svg
