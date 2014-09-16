.. raw:: html

    <style> .red {color:red} </style>

.. role:: red

:.. _required:

 The ':red:`*`' signifies a required Field.

The SAXS configuration file specifies the parameters of a SAXS sensor calibration. It is written in the JSON format which governs the general syntax.


:Type:
  object
:Contains:
  :ref:`Title <Title>`, :ref:`Tilt <Tilt>`:red:`*`, :ref:`BeamCenter <BeamCenter>`:red:`*`, :ref:`DedectorDistanceMM <DedectorDistanceMM>`:red:`*`, :ref:`Imagesize <Imagesize>`:red:`*`, :ref:`MaskFile <MaskFile>`:red:`*`, :ref:`Oversampling <Oversampling>`:red:`*`, :ref:`PixelSizeMicroM <PixelSizeMicroM>`:red:`*`, :ref:`PixelPerRadialElement <PixelPerRadialElement>`:red:`*`, :ref:`Wavelength <Wavelength>`:red:`*`, :ref:`PolarizationCorrection <PolarizationCorrection>`
:Required:
  True
:JSON Path:
  * :ref:`# <root>` 

Example JSON: 

.. code:: json

    {
      "PixelSizeMicroM": [
        172.0
      ],
      "Imagesize": [
        1043,
        981
      ],
      "PixelPerRadialElement": 1,
      "Tilt": {
        "TiltRotDeg": 0,
        "TiltAngleDeg": 0
      },
      "MaskFile": "AAA_integ.msk",
      "Oversampling": 3,
      "Wavelength": 1.54,
      "BeamCenter": [
        800.0,
        400.0
      ],
      "DedectorDistanceMM": 1000.0
    }

.. _Title:

Title
--------------------

:Type:
  string
:Required:
  False
:JSON Path:
  * :ref:`# <root>` [':ref:`Title <Title>`']

Example JSON: 

.. code:: json

    {"Title": ""}

.. _Tilt:

Tilt
--------------------

The sensor, usually is not perfectly perpenticular to the ray direction. The tilt angle can be specified by giving the following paramters.


:Type:
  object
:Contains:
  :ref:`TiltRotDeg <TiltRotDeg>`:red:`*`, :ref:`TiltAngleDeg <TiltAngleDeg>`:red:`*`
:Required:
  True
:JSON Path:
  * :ref:`# <root>` [':ref:`Tilt <Tilt>`']

Example JSON: 

.. code:: json

    {"Tilt": {"TiltRotDeg": 0,"TiltAngleDeg": 0}}

.. _TiltRotDeg:

TiltRotDeg
--------------------

This gives the angel of the tilt direction.


:Type:
  number in degree
:Required:
  True
:Default:
  0
:JSON Path:
  * :ref:`# <root>` [':ref:`Tilt <Tilt>`'][':ref:`TiltRotDeg <TiltRotDeg>`']

Example JSON: 

.. code:: json

    {"TiltRotDeg": 0}

.. _TiltAngleDeg:

TiltAngleDeg
--------------------

This gives the angle between the ray direction and the normal to the sensor plane.


:Type:
  number in degree
:Required:
  True
:Default:
  0
:JSON Path:
  * :ref:`# <root>` [':ref:`Tilt <Tilt>`'][':ref:`TiltAngleDeg <TiltAngleDeg>`']

Example JSON: 

.. code:: json

    {"TiltAngleDeg": 0}

.. _BeamCenter:

BeamCenter
--------------------

Gives the beam center in pixel coorinates.


:Type:
  array(2) items: number number 
:Required:
  True
:Default:
  [800.0, 400.0]
:JSON Path:
  * :ref:`# <root>` [':ref:`BeamCenter <BeamCenter>`']

Example JSON: 

.. code:: json

    {"BeamCenter": [800.0,400.0]}

.. _DedectorDistanceMM:

DedectorDistanceMM
--------------------

Distance between diffraction center and sensor.


:Type:
  number in Millimeters
:Required:
  True
:Default:
  1000.0
:JSON Path:
  * :ref:`# <root>` [':ref:`DedectorDistanceMM <DedectorDistanceMM>`']

Example JSON: 

.. code:: json

    {"DedectorDistanceMM": 1000.0}

.. _Imagesize:

Imagesize
--------------------

Size of sensor image in pixel.


:Type:
  array(2) items: number number 
:Required:
  True
:Default:
  [1043, 981]
:JSON Path:
  * :ref:`# <root>` [':ref:`Imagesize <Imagesize>`']

Example JSON: 

.. code:: json

    {"Imagesize": [1043,981]}

.. _MaskFile:

MaskFile
--------------------

Path of Maskfile


:Type:
  string
:Required:
  True
:Default:
  AAA_integ.msk
:JSON Path:
  * :ref:`# <root>` [':ref:`MaskFile <MaskFile>`']

Example JSON: 

.. code:: json

    {"MaskFile": "AAA_integ.msk"}

.. _Oversampling:

Oversampling
--------------------

Oversampling factor for radial integration. The higher, the longer the setup but the higher the accuracy. More then 3 is probably overkill. 


:Type:
  number
:Required:
  True
:Default:
  3
:JSON Path:
  * :ref:`# <root>` [':ref:`Oversampling <Oversampling>`']

Example JSON: 

.. code:: json

    {"Oversampling": 3}

.. _PixelSizeMicroM:

PixelSizeMicroM
--------------------

The pixel size on the sensor.


:Type:
  array(2) items: number 
:Required:
  True
:Default:
  [172.0]
:JSON Path:
  * :ref:`# <root>` [':ref:`PixelSizeMicroM <PixelSizeMicroM>`']

Example JSON: 

.. code:: json

    {"PixelSizeMicroM": [172.0]}

.. _PixelPerRadialElement:

PixelPerRadialElement
--------------------

Expresses the width of a radial step in terms of pixels. '1' means :math:`\delta R\approx 1` :ref:`PixelSizeMicroM`.


:Type:
  number
:Required:
  True
:Default:
  1
:JSON Path:
  * :ref:`# <root>` [':ref:`PixelPerRadialElement <PixelPerRadialElement>`']

Example JSON: 

.. code:: json

    {"PixelPerRadialElement": 1}

.. _Wavelength:

Wavelength
--------------------

Refined wavelength.


:Type:
  number in Angstrom
:Required:
  True
:Default:
  1.54
:JSON Path:
  * :ref:`# <root>` [':ref:`Wavelength <Wavelength>`']

Example JSON: 

.. code:: json

    {"Wavelength": 1.54}

.. _PolarizationCorrection:

PolarizationCorrection
--------------------

The scattering direction id dependend on the light polarization. This may be acconted for with the polarization correction.


:Type:
  object
:Contains:
  :ref:`Fraction <Fraction>`:red:`*`, :ref:`Angle <Angle>`:red:`*`
:Required:
  False
:Default:
  OrderedDict([(u'Fraction', 0.95), (u'Angle', 0)])
:JSON Path:
  * :ref:`# <root>` [':ref:`PolarizationCorrection <PolarizationCorrection>`']

Example JSON: 

.. code:: json

    {"PolarizationCorrection": {"Angle": 0.0,"Fraction": 0.95}}

.. _Fraction:

Fraction
--------------------

Fraction of light polarized in the given (:ref:`Angle`) direction.


:Type:
  number
:Required:
  True
:Default:
  0.95
:JSON Path:
  * :ref:`# <root>` [':ref:`PolarizationCorrection <PolarizationCorrection>`'][':ref:`Fraction <Fraction>`']

Example JSON: 

.. code:: json

    {"Fraction": 0.95}

.. _Angle:

Angle
--------------------

Angle of the polarization plane.


:Type:
  number in degree
:Required:
  True
:Default:
  0.0
:JSON Path:
  * :ref:`# <root>` [':ref:`PolarizationCorrection <PolarizationCorrection>`'][':ref:`Angle <Angle>`']

Example JSON: 

.. code:: json

    {"Angle": 0.0}

