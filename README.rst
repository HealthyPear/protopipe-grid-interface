=======================================================
Protopipe DIRAC GRID interface |CI| |codacy| |coverage|
=======================================================

.. |CI| image:: https://github.com/HealthyPear/protopipe-grid-interface/actions/workflows/ci.yml/badge.svg
  :target: https://github.com/HealthyPear/protopipe-grid-interface/actions/workflows/ci.yml
.. |codacy| image:: https://app.codacy.com/project/badge/Grade/fecd056c3826433e91d4a7e0b0557434
  :target: https://www.codacy.com/gh/HealthyPear/protopipe-grid-interface/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=HealthyPear/protopipe-grid-interface&amp;utm_campaign=Badge_Grade
.. |coverage| image:: https://codecov.io/gh/HealthyPear/protopipe-grid-interface/branch/master/graph/badge.svg?token=N8GWUWSG3W
  :target: https://codecov.io/gh/HealthyPear/protopipe-grid-interface

This software provides an interface between the
`Protopipe CTA prototype pipeline <https://github.com/cta-observatory/protopipe>`_ 
and the `DIRAC GRID tools <https://dirac.readthedocs.io/en/latest/index.html>`_.

It is required for using *protopipe* to analyse large scale simulation productions on the DIRAC grid.

Requirements
------------

The are only 2 requirements:

- a python3-based installation of Anaconda (or Miniconda),
- a GRID certificate.

:note: Windows support should be available via Docker, but it has not been tested - please, refer to the documentation.

DIRAC GRID certificate
++++++++++++++++++++++

In order to access the GRID utilities you will need a certificate associated with an
account.

You can find all necessary information 
`here <https://forge.in2p3.fr/projects/cta_dirac/wiki/CTA-DIRAC_Users_Guide#Prerequisites>`_.

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
