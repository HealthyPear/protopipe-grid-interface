========================
Protopipe GRID interface
========================

This software provides an interface between the
`Protopipe CTA prototype pipeline <https://github.com/cta-observatory/protopipe>`_ 
and the `DIRAC GRID tools <http://diracgrid.org/>`_.
 
It is required for using *protopipe* to analyze large scale simulation
productions.

The interface is used from the virtual environment container stored
`here <https://github.com/HealthyPear/CTADIRAC>`_, which is a spin-off of `CTADIRAC <https://github.com/cta-observatory/CTADIRAC>`_.

Contents
--------

- interface code to the DIRAC GRID framework
- configuration file to setup the analysis on the GRID
- auxiliary scripts to download/merge data tables and upload estimation models

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
`Vagrant <https://www.vagrantup.com/>`_. This interface comes with a *VagrantFile* which allows to download a Vagrant box
in which to adapt the virtual environment to the local setup.

The *VagrantFile* defines also a suggested directory tree structure, shared 
between the virtual and local environments. A ``shared_folder`` containing an ``analyses`` folder where to store all the various analyses.
The ``create_dir_structure.py`` auxiliary script allows to create a directory structure for 
a new analysis folder, mirrored with the one stored on the user's home in the GRID file catalog.

For Linux users, it is in not required to use Vagrant, but it is suggested as the Vagrant box contains already *Singularity*.

Singularity
+++++++++++

`Singularity <https://sylabs.io/docs/>`_ allows to use the DIRAC tools within 
a container. The vagrant box obtained by using the *VagrantFile* that comes with this interface
has this software already installed ans ready to use.

Linux users that do not want to use *Vagrant* will need to install Singularity
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
