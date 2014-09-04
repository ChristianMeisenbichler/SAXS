 

Polarization Correction
-----------------------

The polarization correction is expected to be small at small angles, but it is deemed important.

.. math::
    I_{cor} = I_j \left[P (1 - (sin(\phi) sin(2\theta ))^2 ) 
    (1 - P )(1 - (cos(\phi) sin(2\theta ))^2 )\right]
    

where :math:`\phi`  is the azimuthal angle on the detector surface
(defined here clockwise, 0 at 12 o'clock) :math:`2\theta` the scattering
angle, and :math:`P` the fraction of incident radiation polarized
in the horizontal plane (azimuthal angle of :math:`90^{\circ}`)
The polarization correction is configured by two parameters in :ref:`PolarizationCorrection`.
Its factors are included in the integration matrix (operator).
 
This input: 

.. literalinclude:: calpol.json

	
Gives:
 
.. plot::

   import SAXS, json
   import matplotlib.pyplot as plt 
   import numpy as np
   
   Calpol=SAXS.calibration('calpol.json')  
   plt.imshow(Calpol.corr)
   plt.title(r"Polarization Correction")
   plt.colorbar()


If the correction factors are all correctly in the algorithm, 
the integration of an image containing :math:`1/I_{corr}` should give constant 1.0.

.. plot::
   
   import SAXS, json
   import matplotlib.pyplot as plt
   import numpy as np
   calfile=json.load(open('calpol.json'))
   calfile['Oversampling']=2
   Calpol=SAXS.calibration(calfile)  
   r=Calpol.integrate(1/Calpol.corr)
   nonzero=r[1]>0
   plt.title(r"Integration of Polarizationcorrection$^{-1}$")
   plt.plot(r[0][nonzero],r[1][nonzero])



Just for checking: integrating a picture with only ones gives something different:

.. plot::

   import SAXS, json
   import matplotlib.pyplot as plt
   import numpy as np
   calfile=json.load(open('calpol.json'))
   calfile['Oversampling']=2
   Calpol=SAXS.calibration(calfile)  
   r=Calpol.integrate(np.ones(Calpol.corr.shape))
   nonzero=r[1]>0
   plt.plot(r[0][nonzero],r[1][nonzero])
   plt.title(r"Integration of Picture With Constant Value 1")

This are the wiggles that come from the polarization correction pattern
   