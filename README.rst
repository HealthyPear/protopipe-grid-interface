=================================
Protopipe GRID interface |codacy|
=================================

.. |codacy| image:: https://app.codacy.com/project/badge/Grade/fecd056c3826433e91d4a7e0b0557434
   :target: https://www.codacy.com/gh/HealthyPear/protopipe-grid-interface/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=HealthyPear/protopipe-grid-interface&amp;utm_campaign=Badge_Grade

This software provides an interface between the
`Protopipe CTA prototype pipeline <https://github.com/cta-observatory/protopipe>`_ 
and the `DIRAC GRID tools <http://diracgrid.org/>`_.
 
It is required for using *protopipe* to analyse large scale simulation productions on the DIRAC grid.
The interface is run from the virtual environment provided by the container of `CTADIRAC <https://github.com/cta-observatory/CTADIRAC>`_.

.. warning::
   Usage of the pipeline on an infrastucture different than the DIRAC grid has not yet been fully tested.
   This interface code is higly bound to DIRAC, but the scripts which manage download, merge and upload of files
   could be easily adapted to different infrastructures.

.. contents::

Requirements
------------

Missing packages
++++++++++++++++

The CTADIRAC container doesn't provide everything *protopipe* needs, but this can be solved easily by issuing the following command inside the container,

``pip install -r requirements.txt``

DIRAC GRID certificate
++++++++++++++++++++++

In order to access the GRID utilities you will need a certificate associated with an
account.

You can find all necessary information 
`here <https://forge.in2p3.fr/projects/cta_dirac/wiki/CTA-DIRAC_Users_Guide#Prerequisites>`_.

Options for containerization
----------------------------

.. note::
  Depending on you chosen solution, any of the following choices constitutes a separate requirement.

- Single user working from personal machine

The *Docker* container might be enough for you.

- User working on a more or less shared environment (HPC machine or server)

In case you are not allowed to use *Docker* for security reasons, another supported option is *Singularity*.
In that case the choice will depend on which operative system you are working and the privileges you are allowed to have:

  - on *Linux* make sure *Singularity* is installed and accessible to your user,
  
  - on *Windows* or *macos*, you will need to install *Vagrant*.

Docker
++++++

The container used by the interface requires the `installation of Docker <https://docs.docker.com/get-docker/>`_.

To enter the container (and the first time downloading the image),

``docker run --rm -v $HOME/.globus:/home/dirac/.globus -v $PWD/shared_folder:/home/dirac/shared_folder -v [...]/protopipe:/home/dirac/protopipe -v [...]/protopipe-grid-interface:/home/dirac/protopipe-grid-interface -it ctadirac/client``

where ``[...]`` is the path of your source code on the host

.. warning::
   There is yet no container for a released version of *protopipe*.
   In that case you can link its folder from your python environment installation on the host (``import protopipe; protopipe.__path__``).

.. warning::
   If you are using *macos* you could encounter some disk space issues.
   Please check `here <https://docs.docker.com/docker-for-mac/space/>`_ and `here <https://djs55.github.io/jekyll/update/2017/11/27/docker-for-mac-disk-space.html>`_ on how to manage disk space.


Vagrant
+++++++

All users, regardless of their operative systems, can use this interface via
`Vagrant <https://www.vagrantup.com/>`_. 

The *VagrantFile* provided with the interface code allows to download a virtual 
machine in form of a *Vagrant box* which will host the actual container.

The user needs only to edit a couple lines to link the source codes of the
pipeline and this interface.

The *VagrantFile* defines creates automatically also the ``shared_folder``
used by the interface to setup the analysis.

Singularity
+++++++++++

`Singularity <https://sylabs.io/docs/>`_ is already installed and ready to use from the *Vagrant box* 
obtained by using the *VagrantFile*.
Linux users that do not want to use *Vagrant* will need to have *Singularity* installed
on their systems and they will need to edit their own environment accordingly.

For pure-*Singularity* users (aka on Linux machines without *Vagrant*) 
bind mounts for *protopipe*, its grid interface and the shared_folder 
will work in the same way: ``--bind path_on_host:path_on_container``.

Note that the DIRAC grid certificate should be already available, since *Singularity* mounts the user's home by default.
For more details, please check e.g. `system-defined bind paths <https://sylabs.io/guides/3.8/user-guide/bind_paths_and_mounts.html#system-defined-bind-paths>`_.

Depending on the privileges granted on the host there are 2 ways to get a working container.

Using the CTADIRAC Docker image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Method #1**

Provided you have at least *Singularity 3.3*, you can pull directly the CTADIRAC Docker image from *DockerHub*, but you will need to use the ``fakeroot`` mode.
This mode grants you root privileges *inside* the container.

``singularity build --fakeroot ctadirac_client_latest.sif docker://ctadirac/client``

``singularity shell --fakeroot ctadirac_client_latest``

``. /home/dirac/dirac_env.sh``

**Method #2**

You shouldn't need root privileges for this to work (not throughly tested),

``singularity build --sandbox --fix-perms ctadirac_client_latest.sif docker://ctadirac/client``

``singularity shell ctadirac_client_latest``

``. /home/dirac/dirac_env.sh``

Building the Singularity image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Support for *Singularity* has been dropped by the mantainers of *CTADIRAC*,
but the recipe for the container has been saved here.

With any of the methods described below you won't need to do ``. /home/dirac/dirac_env.sh``,
the commands will be already stored in your ``$PATH``.

.. warning::
   The recipe ``CTADIRAC_singularity`` is maintained by the author; if any bug arises,
   reverting to the methods described above (if possible) will provide you with a working environment.

If you have root privileges you can just build your own image with,

``singularity build ctadirac_client_latest.sif CTADIRAC_singularity``

otherwise you have to either,

- revert to the ``--fakeroot`` mode 
  (use it also to enter the container just like the methods above)

- build the image remotely at ``https://cloud.sylabs.io`` using the ``--remote`` flag
  (for this you will need to interface with that servce to generate an access token)

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
