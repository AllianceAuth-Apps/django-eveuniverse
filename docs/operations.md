# Operations Guide

The operations guide describes how to install, configure and maintain *django-eveuniverse*.

## Installation

To install django-eveuniverse into your Django project please follow the these steps:

### Install from PyPI

You can install this app directly from PyPI:

```bash
pip install django-eveuniverse
```

### Update settings

Next add `eveuniverse` to `INSTALLED_APPS` in your project's settings file.

By default only the core models are automatically loaded on-demand. If you want to also include some of the additional models please add them to your settings.

```{eval-rst}
.. seealso::
    For an overview of all settings please see :ref:`operations-settings`.
```

### Setup celery

This app uses [Celery](https://docs.celeryproject.org/en/stable/index.html) for loading large sets of data, e.g. with the load commands. Please make sure celery is setup and working for your Django project.

In addition you need to have a configuration for celery_once.

```{note}
Note that in case your installation is running with Alliance Auth, then you already have a celery once configuration and can skip this step.
```

Eve Universe comes with generic Django backend, which should work with most Django installations and which can be setup by adding this to your celery configuration file (e.g. `celery.py`):

```python
celery_app.conf.ONCE = {
    "backend": "eveuniverse.backends.DjangoBackend",
    "settings": {},
}
```

Or you can use one of the backends provided with celery_once. See [celery-once](https://github.com/cameronmaske/celery-once#backends) for more information.

```{note}
**Note on celery worker setup**

For an efficient loading of large amounts of data from ESI we recommend a thread based setup of celery workers with at least 10 concurrent workers. (e.g. `celery -A myapp worker --pool threads --concurrency 10` )

For example on our test system with 20 threads the loading of the complete Eve Online map (with the command: **eveuniverse_load_data map**) consisting of all regions, constellation and solar systems took only about 15 minutes.
```

### Finalize installation

```bash
python manage.py migrate
```

Finally restart your Django instance so your changes become effective.

## Updating

```{eval-rst}
.. hint::
    Before updating please always check the release notes for any special instructions on updating or important changes that might affect your project.
```

To update your installation first install the new version:

```bash
pip install -U django-eveuniverse
```

Then run Django migrations:

```bash
python manage.py migrate
```

And finally restart your Django instance so your changes become effective.

```{eval-rst}
.. _operations-settings:
```

## Settings

Here is a list of available settings for this app. They can be configured by adding them to your local Django settings file.

```{note}
All settings are optional and the app will use the documented default settings if they are not used.
```

```{important}
Many settings will enable the automatic loading of related models. For example: if you enable Planets, all related planet object are automatically loaded when updating a solar system. This will significantly increase load times of objects, so we recommend to only enable additional models that are functionally needed.

The preferred approach is load related model on demand with the `enabled_sections` feature. Please see {ref}`load_related_models_on_demand` for more details.
```

```{eval-rst}
.. automodule:: eveuniverse.app_settings
    :members:
```

```{eval-rst}
.. _operations-management-commands:
```

## Management commands

The following management commands are available:

### eveuniverse_load_data

This command will load large sets of data from ESI into local database for selected topics. This is useful to optimize performance or when you want to provide the user with drop-down lists covering all values in a topic (e.g. ship types). Available topics are:

- **map**: All regions, constellations and solar systems
- **ships**: All ship types
- **structures**: All structures types
- **types**: All types

Here is how you can use this command (not including default Django arguments):

```text
usage: manage.py eveuniverse_load_data [-h]
                        [--types-enabled-sections {dogmas,graphics,market_groups,type_materials,industry_activities} [{dogmas,graphics,market_groups,type_materials,industry_activities} ...]]
                        [--map-enabled-sections {dogmas,graphics,market_groups,type_materials,industry_activities} [{dogmas,graphics,market_groups,type_materials,industry_activities} ...]]
                        [--version] [-v {0,1,2,3}] [--settings SETTINGS]
                        [--pythonpath PYTHONPATH] [--traceback] [--no-color]
                        [--force-color] [--skip-checks]
                        {map,ships,structures,types} [{map,ships,structures,types} ...]

Load large sets of data from ESI into local database for selected topics

positional arguments:
  {map,ships,structures,types}
                        Topic(s) to load data for

options:
  -h, --help            show this help message and exit
  --types-enabled-sections {dogmas,graphics,market_groups,type_materials,industry_activities} [{dogmas,graphics,market_groups,type_materials,industry_activities} ...]
                        List of enabled sections for types, ships and structures topics
  --map-enabled-sections {dogmas,graphics,market_groups,type_materials,industry_activities} [{dogmas,graphics,market_groups,type_materials,industry_activities} ...]
                        List of enabled sections for map topic
```

### eveuniverse_purge_all

This command will purge ALL data of your models.

### eveuniverse_load_types

This command loads large sets of types as specified from ESI into the local database.

Here is how you can use this command (not including default Django arguments):

```text
usage: manage.py eveuniverse_load_types [-h] [--category_id CATEGORY_ID]
                        [--category_id_with_dogma CATEGORY_ID_WITH_DOGMA]
                        [--group_id GROUP_ID] [--group_id_with_dogma GROUP_ID_WITH_DOGMA]
                        [--type_id TYPE_ID] [--type_id_with_dogma TYPE_ID_WITH_DOGMA]
                        [--disable_esi_check]
                        app_name

Loads large sets of types as specified from ESI into the local database. This is a helper command meant
to be called from other apps only.

positional arguments:
  app_name              Name of app this data is loaded for

options:
  -h, --help            show this help message and exit
  --category_id CATEGORY_ID
                        Eve category ID to be loaded excl. dogma
  --category_id_with_dogma CATEGORY_ID_WITH_DOGMA
                        Eve category ID to be loaded incl. dogma
  --group_id GROUP_ID   Eve group ID to be loaded excl. dogma
  --group_id_with_dogma GROUP_ID_WITH_DOGMA
                        Eve group ID to be loaded incl. dogma
  --type_id TYPE_ID     Eve type ID to be loaded excl. dogma
  --type_id_with_dogma TYPE_ID_WITH_DOGMA
                        Eve type ID to be loaded incl. dogma
  --disable_esi_check   Disables checking that ESI is online
```

## Database tools

On some DBMS like MySQL it is not possible to reset the database and remove all eveuniverse tables with the standard "migrate zero" command. The reason is that eveuniverse is using composite primary keys and Django seams to have problems dealing with that correctly, when trying to roll back migrations.

As workaround you will need remove all tables with SQL commands. To make this easier we are providing a SQL script that contains all commands to drop the tables. The process for "migrating to zero" is then as follows:

1. Run SQL script `drop_tables.sql` on your database
2. Run `python manage.py migrate eveuniverse zero --fake`
