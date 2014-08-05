
Install
=======


The SAXS Package is distributes as a Python package. So in order to use it, you need a Python system installed.
It depends on following Python modules that don't come with the standard Python::

   numpy scipy matplotlib jsonschema bitarray watchdog sphinxcontrib-programoutput\
    sphinxcontrib-programscreenshot pyzmq

they are all available through "pip" so the command::

   >>pip numpy scipy matplotlib jsonschema bitarray watchdog sphinxcontrib-programoutput\
    sphinxcontrib-programscreenshot pyzmq
Should get all the modules.
For Windows, use the Anaconda Python distribution which includes pip.

The code can be obtained on github: https://github.com/ChristianMeisenbichler/SAXS where you would
also find a "Download Zip" button.
After unpacking or cloning with git you end up with a directory called "SAXS" containing the files. 
Go there, and type into the commad line:

.. code::

   python setup.py install

This installs the Python module where it is found by Python, creates the command line tools and
installs them on the system. Where that is, depends on the Python installation. 
The setup script will also try to satisfy all the dependencies by downloading and installing them. 
