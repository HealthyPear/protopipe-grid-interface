========================
Protopipe GRID interface
========================

This software provides an interface between the
`Protopipe CTA prototype pipeline <https://github.com/cta-observatory/protopipe>`_ 
and the `DIRAC GRID tools <http://diracgrid.org/>`_.
 
It is required for using this pipeline to analyse large scale simulation
productions.

The interface is run from a copy of the virtual environment container stored
`here <https://github.com/HealthyPear/CTADIRAC>`_, which is a spin-off of `CTADIRAC <https://github.com/cta-observatory/CTADIRAC>`_.

Contents
--------

- VagrantFile
- interface code to the DIRAC GRID
- configuration file to setup the analysis on the GRID
- auxiliary scripts to 
  
  - download/merge data tables,
  - upload estimation models,
  - setup an analysis working environment.

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
`Vagrant <https://www.vagrantup.com/>`_ (recommended). 

The *VagrantFile* allows to download a virtual 
environment in form of a *Vagrant box* which will host the container.

The user needs only to edit a couple lines to link the source codes of the
pipeline and this interface.

The *VagrantFile* defines also a ``shared_folder`` containing

- an ``analyses`` folder where to store the analyses,
- a ``productions`` folder where to store the lists of simulation files

The ``create_analysis_tree.py`` auxiliary script allows to create a directory 
structure for each new analysis, mirrored with the one stored on the user's 
home in the GRID file catalog.

Singularity
+++++++++++

`Singularity <https://sylabs.io/docs/>`_ allows to use the DIRAC tools within 
a container. 

This software is already installed and ready to use from the *Vagrant box* 
obtained by using the *VagrantFile*.

Linux users that do not want to use *Vagrant* will need to install *Singularity*
on their systems and they will need to edit their own environment accordingly.

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
