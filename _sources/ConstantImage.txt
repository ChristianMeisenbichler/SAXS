

Integrating a Constant Image With Masked Values
-----------------------------------------------

This test shows that nothing wrong happens at mask borders. 
For thos we want to integrate an image that is one everywhere except for the masked regions

We use the following calibration without Polarization correction and mask:

.. literalinclude:: cal.json

The image we are going to integrate is exactly the array the :py:func:`SAXS.openmask` returns:

.. plot::
   
   import SAXS,json
   from scipy import misc
   import matplotlib.pyplot as plt
   import numpy as np
   conf=json.load(open('cal.json'))
   img =SAXS.openmask(conf)
   conf=json.load(open('cal.json'))
   img =SAXS.openmask(conf)
   plt.imshow(img)
   plt.colorbar()
   misc.imsave("mask.tif",img)
   
The result is constant 1 (wher the intensity is not 0), save 2e-12.

.. plot::

   import SAXS,json
   from scipy import misc
   import matplotlib.pyplot as plt
   import numpy as np
   conf=json.load(open('cal.json'))
   img =SAXS.openmask(conf)
   cal=SAXS.calibration(conf)
   r=cal.integrate(img)
   nonzero=(r[1]!=0)
   plt.plot(r[0][nonzero],r[1][nonzero])
   
   
Doing the same with Fit2d,
   
.. command-output::  fit2d -svar\#IN=mask.tif -dim2000x2000 -svar\#OUT=data/const.chi -mac../data/AAA_integ_Pilatus1M_cmd.mac
   :ellipsis: 10

results in something similar, just with less precision, about 10e-7. 
Probably because of single precission arithmetics.

.. plot::

   import SAXS,json
   from scipy import misc
   import matplotlib.pyplot as plt
   import numpy as np
   
   fit2d=np.loadtxt('data/const.chi' ,skiprows=4 )
   nonzero=fit2d[:,1]!=0
   plt.plot(fit2d[nonzero,0],fit2d[nonzero,1]/255.0)
         