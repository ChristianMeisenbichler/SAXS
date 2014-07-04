
Compare With Fit2d
------------------

The program fit2d, which this package aims to partly replace, is the standard, so we better include a comparison plot here:

.. plot::

   import matplotlib.pyplot as plt
   import numpy as np
   data=np.loadtxt('data/fit2d' ,skiprows=4 )
   plt.plot(data[:,0],data[:,1],label="fit2d")
   data=np.loadtxt('data/saxsdog' ,skiprows=4 )
   plt.plot(data[:,0],data[:,1],label="saxsdog")
   plt.ylabel('Intensity [counts/pixel]')
   plt.xlabel('q [1/nm]')
   plt.yscale('log')
   plt.title("Compare Fit2d and SAXS Package")

Okay, this doesn't show much but if we plot the difference:

.. plot::

   import SAXS
   arg=["../doc/data/fit2d","../doc/data/saxsdog"]
   o={}
   o=SAXS.AttrDict(o)
   o['compare']=True
   o.log=False
   o.yax='linear'
   o.xax='linear'
   o.title="Difference"
   o.legend=True 
   o.plotfile=""
   SAXS.makeplot(o,arg)
 
Still looks okay.
   
.. plot:: 

   import SAXS
   arg=["../doc/data/fit2d","../doc/data/saxsdog"]
   o={}
   o=SAXS.AttrDict(o)
   o.yax='linear'
   o.xax='linear'
   o['compare']=False
   o.log=False
   o.title="From the middle"
   o.legend=True
   o.plotfile=""
   o.skip=350 
   o.clip=480
   SAXS.makeplot(o,arg)


.. plot:: 
 
   import SAXS
   arg=["../doc/data/fit2d","../doc/data/saxsdog"]
   o={}
   o=SAXS.AttrDict(o)
   o['compare']=False
   o.log=False
   o.yax='linear'
   o.xax='linear'
   o.title="Tail Region"
   o.legend=True
   o.plotfile=""
   o.skip=850
   o.clip=40
   SAXS.makeplot(o,arg)

In the Tail region the blue halo (Poisson error) signifies that there are not enough counts to make good statistics.
   
.. plot:: 

   import SAXS
   arg=["../doc/data/fit2d","../doc/data/saxsdog"]
   o={}
   o=SAXS.AttrDict(o)
   o['compare']=False
   o.log=True
   o.yax='linear'
   o.xax='linear'
   o.title="Close to Beam"
   o.legend=True
   o.plotfile=""
   o.skip=13
   o.clip=960 
   SAXS.makeplot(o,arg)
   