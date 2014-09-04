

.. _geometry:

The Geometry
------------
The plane of the sensor is not perfectly normal to the beam. So in order to calculate witch 
pixel is on witch cone in the diffracted light, we need to express the geometry somehow.

Every pixel has the polar coordinates :math:`r`, :math:`\phi` with the projected diffraction center in the origin.
For each pixel (P) the triangle S,C,P (Sample, Center, Pixel, :math:`\theta`, :math:`\beta`, :math:`\gamma`) 
can be fully expressed with the law of cosines.


.. figure:: Dreieck.*
   
   The SCP triangle.

:math:`l` is the distance the light travels from the diffraction center to the sensor.

.. math::
   l^2=d^2+r^2 - 2 d r \cos(\pi/2+\alpha)

:math:`r` is the radial coordinate of the pixel P.

.. math::
   r^2=l^2+d^2 -2 l d \cos(\theta)
   
from these two formulas the diffraction angle (here) :math:`\theta` can be computed.

.. math::
   \theta=\arccos(-r^2 -l^2 -d^2 2 l d)

.. _alpha:

.. figure:: winkel.*

   Angle between two planes.


:math:`\alpha` comes from the following relation in figure :ref:`alpha`



The angle between the sensor plane and the normal plane to the ray is given by :math:`\tau`. 
The slope :math:`s` derived from  :math:`\tau` is 

.. math::
   s=\sin(\tau)

On the (red) unit circle in the plane of the sensor the distance to the plane normal to the ray is expressed as

.. math::
    h=\sin(\phi)s

The angle :math:`\alpha` is therefore:

.. math::
   \alpha=\arcsin(\sin(\tau)\sin(\phi))
   
in Python code this is :py:func:`SAXS.calc_theta`:

.. code::

   def calc_theta(r,theta,d,tilt,tiltdir):
      alpha=np.arcsin(np.sin(tilt)*np.sin(theta+tiltdir))
      lsquared=d**2 +r**2 -2*d*r*np.cos(np.pi/2+alpha)
      return np.arccos(-(r**2-lsquared-d**2)/(2*np.sqrt(lsquared)*d))
 
  
   
This angle :math:`\theta` then is calculated for every sub pixel in the sensor. 
This number then can be rescaled and rounded to the nearest integer in order to get
unique integer labels for all the pixels. This labels are the index of the radial interval.

Tilt Angle Correction Test
~~~~~~~~~~~~~~~~~~~~~~~~~~

To check if the tilt angle correction is working, lets create some fake calibration data, with the following peaks 
in the diffraction curve:

.. plot::
   
   import matplotlib.pyplot as plt
   import numpy as np
   rmax= 1003
   x=np.arange(rmax)/100000.0 /3
   y=(3*np.exp(-(x/6.0e-5)**2) 
   	   +np.exp(-((x-0.5e-3)/1.0e-5)**2) 
   	   +np.exp(-((x-1.0e-3)/1.0e-5)**2) 
   	   +np.exp(-((x-1.5e-3)/1.0e-5)**2) 
   	   +np.exp(-((x-2.0e-3)/1.0e-5)**2) 
   	   +np.exp(-((x-2.50e-3)/1.0e-5)**2))
   plt.plot(y)
   plt.title(r"Simulated Powder Diffraction")
   plt.ylabel("Intensity")
   plt.xlabel("$n^{th}$ r")

.. plot:: 
   
   import matplotlib.pyplot as plt
   import numpy as np
   import SAXS,json
   from scipy import misc
   geo=json.load(open("calgeo.json")) 
   misc.imsave("emptymask.tif",np.zeros(geo['Imagesize']))
   Cal=SAXS.calibration('calgeo.json')  
   rmax= 1002   
   x=np.arange(rmax)/100000.0 /3
   y=(3*np.exp(-(x/6.0e-5)**2) 
         +np.exp(-((x-0.5e-3)/1.0e-5)**2) 
         +np.exp(-((x-1.0e-3)/1.0e-5)**2) 
         +np.exp(-((x-1.5e-3)/1.0e-5)**2) 
         +np.exp(-((x-2.0e-3)/1.0e-5)**2) 
         +np.exp(-((x-2.50e-3)/1.0e-5)**2))
    
   
   powder=Cal.ITransposed.dot((y*30000+1000)*Cal.Areas).reshape((Cal.config['Imagesize'][0],Cal.config['Imagesize'][1]))*10000
   misc.imsave("powder.tif", powder)
   plt.imshow(powder)  
   plt.title(r"Simulated Powder Diffraction")
	

This was done with this configuration file:  

.. literalinclude:: calgeo.json

Which amounts to a large tilt, lets see what Fit2d makes of it

.. code:: 

   INFO: SOLUTION 2
   INFO: Best fit beam centre (X/Y mm) =   66.78356      138.9544
   INFO: Best fit beam centre (X/Y pixels) =   388.2765      807.8745
   INFO: Cone  1 best fit 2 theta angle (degrees) =   1.392646
   INFO: Cone  2 best fit 2 theta angle (degrees) =   2.780810
   INFO: Cone  3 best fit 2 theta angle (degrees) =   4.168858
   INFO: Cone  4 best fit 2 theta angle (degrees) =   5.556975
   INFO: Cone  5 best fit 2 theta angle (degrees) =   6.944765
   INFO: Best fit angle of tilt plane rotation (degrees) =   73.59509
   INFO: Best fit angle of tilt (degrees) =  -10.00601
   INFO: Estimated coordinate radial position error (mm) =  0.7136476E-02
   INFO: Estimated coordinate radial position error (X pixels) =  0.4149114E-01
   

Seems OK.

