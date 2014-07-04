

Integration as Matrix-Vector Multiplication
-------------------------------------------

Every SAXS image :math:`\mathbf p` is a list of pixels that have an intensity value. 
This 2d array might as well be addressed as a vector with all the pixels addressable with one index :math:`\mathbf p_i`.

The integration over pixels that are within a certain radial interval is 
in any case a weighted sum of some of the pixels.

This weighted sum is a scalar product with another vector containing the weight factors. 
As only the pixels in a radius interval are counted, most of these factors are 0.

.. math::

   r=\mathbf c \cdot \mathbf p

As we intend to do all the radial intervals at once, we write it as a matrix vector product.

.. math::

   \mathbf r=\mathbf X \cdot \mathbf p 
   
The columns are the weight factors for the :math:`i^{th}` radial element.
Rearranged in the order of the image, this looks like the ring element relevant for the radial Point.

This matrix would be quite big as it has the dimensions len(:math:`\mathbf r`)*len(:math:`\mathbf p`). Fortunately most 
of the entries are 0 and we can use a sparse matrix representation which uses only about ~len(:math:`\mathbf p`) 
of memory, as every pixel is counted only once, or, as we will see, about once.



.. plot:: 

	import matplotlib.pyplot as plt
	import matplotlib.cm as cm
	import numpy as np
	import SAXS,json
	from scipy import misc
	geo=json.load(open("calgeo.json")) 
	misc.imsave("emptymask.tif",np.zeros(geo['Imagesize']))  

	Cal=SAXS.calibration(geo)  
	ring=Cal.I[100].todense().reshape((Cal.config['Imagesize'][0],Cal.config['Imagesize'][1]))
	misc.imsave("ring.png",ring[110:350,250:550])
	misc.imsave("ring.pdf",ring[110:350,250:550]) 
	geo['Oversampling']=1
	Calnov=SAXS.calibration(geo)  
	ringnov=Calnov.I[100].todense().reshape((Cal.config['Imagesize'][0],Cal.config['Imagesize'][1]))
	misc.imsave("ringNoOv.png",ringnov[110:350,250:550]) 
	misc.imsave("ringNoOv.pdf",ringnov[110:350,250:550]) 

.. _CircleNoAA

.. figure:: ringNoOv.*

	The vector :math:`\mathbf c` displayed as image.
	
Figure :ref:`CircleNoAA` Scows the data of such a matrix column.
 
Oversampling
------------

.. _Circle:

.. figure:: ring.*
	
	Ring with antialiasing / oversampling.
	
A pixel might lie on the border of two radial intervals, making it 
unclear to which one it should be added. By only choosing the nearest 
one, one may get artifacts in the resulting curve especially when only few pixels contribute.
So, how could we calculate to which fraction a pixel should account to one radial interval?

The idea here is to use an algorithm comparable to antialiasing in computer graphics. 
We will divide a much larger picture into the radial intervals and downsample it to the real pixels. 
Which results in nicely balanced factors for the border pixels that add 
up nicely over joining  intervals such that the intensity is conserved. If one looks closer at image :ref:`Circle` ,
one sees that the ring has soft edges. Quite as it would have through antialiasing.
   