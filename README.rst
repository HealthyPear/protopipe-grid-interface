========================
Protopipe GRID interface
========================

This software provides an interface between the
`Protopipe CTA prototype pipeline <https://github.com/cta-observatory/protopipe>`_ 
and the `DIRAC GRID tools <http://diracgrid.org/>`_.
 
It is required for using *protopipe* to analyze large scale simulation
productions.

The interface can be used from a virtual environment container stored
`here <https://github.com/HealthyPear/CTADIRAC>`_
as a spin-off of `CTADIRAC <https://github.com/cta-observatory/CTADIRAC>`_.

Contents
--------

- interface code for jobs handling
- configuration file for setup of the analysis jobs on the grid
- auxiliary bash/python scripts to download/merge data tables and models upload

Requirements
------------

GRID certificate
++++++++++++++++

In order to access the GRID utilities you will need a certificate associated with an
account.

You can fin all necessary information 
`here <https://forge.in2p3.fr/projects/cta_dirac/wiki/CTA-DIRAC_Users_Guide#Prerequisites>`_.

Vagrant
+++++++

All users, regardless of their operative systems, can use this interface via
`Vagrant <https://www.vagrantup.com/>`_.

The interface code comes with a *VagrantFile* which allows to adapt the virtual 
environment to the local setup.

The *VagrantFile* comes with a suggested directory tree structure shared 
between the virtual and local environments, i.e. a shared
``data`` folder containing an ``analyses`` folder where to store all the various analyses.
Use the ``create_dir_structure.py`` auxiliary script from *protopipe* to create 
each new analysis folder ready to use by this interface.

For Linux users is in not required to use Vagrant, but it is suggested.

Singularity
+++++++++++

`Singularity <https://sylabs.io/docs/>`_ allows to use the DIRAC tools within 
the virtual environment. The vagrant box obtained by using the *VagrantFile* 
comes with this software already installed.

Linux users that do not want to use *Vagrant* will need Singularity installed
on their systems and they will need to edit their own environment accordingly.
In this case, the simplest solution is to use ``$HOME`` as a shared folder.

Documentation
-------------

The documentation for installation and usage of this interface
is stored along with that of the pipeline itself at
`this webpage <https://cta-observatory.github.io/protopipe/>`_.

Enquiries
---------

If you find a problem or a bug related to either this interface or its relation
to the DIRAC client, please open an issue in the 
`repository <https://github.com/HealthyPear/protopipe-grid-interface>`_.
