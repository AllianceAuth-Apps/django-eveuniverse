.. currentmodule:: eveuniverse

===============
API
===============

This chapter contains the developer reference documentation of the public API for *django-eveuniverse* consisting of all models, their manager methods and helpers.

.. _api-eve-models:

Models
==========

.. automodule:: eveuniverse.models
    :members:

.. _api-manager-methods:

Model Managers
====================

.. automodule:: eveuniverse.managers.entities
    :members:

.. automodule:: eveuniverse.managers.sde
    :members:

.. automodule:: eveuniverse.managers.universe
    :members:

Helpers
====================

.. automodule:: eveuniverse.helpers
    :members:

Tasks
====================

Eve Universe tasks
------------------

.. autofunction:: eveuniverse.tasks.load_eve_object

.. autofunction:: eveuniverse.tasks.update_or_create_eve_object

EveEntity tasks
---------------

.. autofunction:: eveuniverse.tasks.create_eve_entities

.. autofunction:: eveuniverse.tasks.update_unresolved_eve_entities

Object loader tasks
-------------------

.. autofunction:: eveuniverse.tasks.create_eve_entities
    :noindex:

.. autofunction:: eveuniverse.tasks.update_unresolved_eve_entities
    :noindex:

.. autofunction:: eveuniverse.tasks.load_map

.. autofunction:: eveuniverse.tasks.load_all_types

.. autofunction:: eveuniverse.tasks.load_eve_types


Other tasks
-------------------

.. autofunction:: eveuniverse.tasks.update_market_prices

Tools
====================

Testdata
-------------------

.. automodule:: eveuniverse.tools.testdata
    :members:

.. seealso::
    Please also see :ref:`developer-testdata` on how to create test data for your app.


Web APIs
========

APIs for accessing external web sites related to Eve Online.

dotlan
----------------
.. automodule:: eveuniverse.core.dotlan
    :members:

esitools
----------------
.. automodule:: eveuniverse.core.esitools
    :members:

eveimageserver
----------------
.. automodule:: eveuniverse.core.eveimageserver
    :members:

eveitems
----------------
.. automodule:: eveuniverse.core.eveitems
    :members:

evesdeapi
----------------
.. automodule:: eveuniverse.core.evesdeapi
    :members:

eveskinserver
----------------
.. automodule:: eveuniverse.core.eveskinserver
    :members:

evewho
----------------
.. automodule:: eveuniverse.core.evewho
    :members:

evexml
---------------
.. automodule:: eveuniverse.core.evexml
    :members:

zkillboard
---------------
.. automodule:: eveuniverse.core.zkillboard
    :members:
