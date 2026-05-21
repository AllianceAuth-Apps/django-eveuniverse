# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

## [2.0.0] - 2026-05-21

This release is a major update with several breaking changes.

- Switched to OpenAPI client from django-esi to replace deprecated Swagger client
- New minimum requirements: Python 3.10 & Django 4.2 & django-esi 8
- Now requires django-redis for caching

### Update notes

django-eveuniverse was initially developed to support community apps for Alliance Auth.

If you are using it for a non-Alliance Auth project please note that the OpenAPI client
in django-esi now requires django-redis as cache backend for Django.

It can be configured like this in the Django's settings file:

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

### Changed

- BREAKING CHANGE: Removed support for Django 3.2
- BREAKING CHANGE: Removed support for Python 3.8
- BREAKING CHANGE: Removed support for Python 3.8
- BREAKING CHANGE: Removed `EsiClientStub`
- BREAKING CHANGE: Removed evemicros package
- Added support for Django 5.2
- Added support for Django 6.0
- Added support for django-esi 9
- Added support fpr Python 3.13
- Field EveBloodlines.ship_types is now nullable
- Removed logger tag
- Removed outdated command `eveuniverse_fix_section_flags`
- Pinned ESI spec file
- Added test factories for all types
- Modernized test suite

### Fixed

- Does not fetch moons for EveSolarSystem when section is enabled
- Added workaround for bloodlines related schema issues (#27)

## [2.0.0a7] - 2026-05-20

## Changed

- Field EveBloodlines.ship_types is now nullable

## Fixed

- Added workaround for bloodlines related schema issues (#27)

## [2.0.0a6] - 2026-05-16

## Changed

- Restored old test factories and marked them as deprecated.
- Added more factory boy test factories

## [2.0.0a5] - 2026-05-05

## Changed

- Improved test factories
- Removed old style test factories. All testdata factories are now based on factory boy.

## [2.0.0a4] - 2026-05-03

## Changed

- Restored testdata feature
- Removed logger tag

## [2.0.0a3] - 2026-04-30

This release is a major update with several breaking changes.

- Switched to OpenAPI client from django-esi to replace deprecated Swagger client
- No longer provides tools for generating test data
- New minimum requirements: Python 3.10 & Django 4.2 & django-esi 8
- Now requires django-redis for caching

### Update notes

django-eveuniverse was initially developed to support community apps for Alliance Auth.

If you are using it for a non-Alliance Auth project please note that the OpenAPI client
in django-esi now requires django-redis as cache backend for Django.

It can be configured like this Django's settings file.

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}
```

### Changed

- Breaking Change: Removed support for Django 3.2
- Breaking Change: Removed support for Python 3.8
- Breaking Change: Removed support for Python 3.8
- Breaking Change: Removed `EsiClientStub`, testdata feature -> Use test factories instead
- Breaking Change: Removed evemicros package
- Added test factories for all types
- Removed outdated command `eveuniverse_fix_section_flags`
- Pinned swagger spec file
- Modernized HTTP related
- Added support for Django 5.2
- Added support for Django 6.0
- Added support for django-esi 9
- Added support fpr Python 3.13

### Fixed

- Does not fetch moons for EveSolarSystem when section is enabled

## [1.6.1] - 2026-04-11

### Fixed

- Some factories generate objects with incorrect IDs (e.g. EveSolarSystem)
- Tries to fetch django-esi 9 which is not compatible

## [1.6.0] - 2025-10-02

### Added

- Added task `update_stale_entities` for updating names of stale entities (#23)

### Changed

- Removed support for Django 4.0 & 4.1

## [1.5.9] - 2025-07-18

### Fixed

- Unhandled exception when ESI is offline (#25)

## [1.5.8] - 2025-07-10

### Fixed

- Reactions with ID 11 missing in industry activities (#24).

## [1.5.7] - 2025-04-04

### Changed

- Added debug logging when trying to resolve nearest celestials

## [1.5.6] - 2024-12-31

### Fixed

- CCP Lightyear != Lightyear (#16)
- Some Low Security returned as Nullsec, Inconsistent CCP Rounding (#20)
- XML conversion sometimes fails with TypeError (#21)

## [1.5.5] - 2024-07-10

### Fixed

- Autocomplete fields on admin page of other apps referring EveCategory, EveGroup or EveType did not contain unpublished objects, because they where filtered out prematurely in eveuniverse admin. For example tracker clauses in Killtracker.

## [1.5.4] - 2023-12-16

### Changed

- Improve logic for updating market prices
- Split original long running task into two smaller tasks

## [1.5.3] - 2023-10-08

### Changed

- Updated dependency to include django-esi 5.0

## [1.5.2] - 2023-10-06

### Update notes

This patch fixes a potential data issue for solar systems and planets. Please run the following command to also fix this issue in your existing data:

```sh
python manage.py eveuniverse_fix_section_flags
```

### Changed

- Added factory boy

### Fixed

- Do not mark an entity as loaded with a section if that section is not actually loaded, because it requires children to be loaded

## [1.5.1] - 2023-10-05

### Changed

- Only show published categories, groups and types on admin site

## [1.5.0] - 2023-09-20

### Changed

- EveEntity.objects.bulk_create_esi() renamed to bulk_resolve_ids()
- EveEntity.objects.bulk_create_esi() is now deprecated and will be removed in a future release

### Fixed

- EveEntity.objects.bulk_create_esi() does not resolve existing empty objects

## [1.4.1] - 2023-09-13

### Changed

- Made `EveUniverseEntityModel.DEFAULT_ICON_SIZE` and other internal methods private

### Fixed

- Made `EveUniverseEntityModel` available in public API again

## [1.4.0] - 2023-09-13

### Added

- Added abyssal deadspace property to EveSolarSystem
- Allow specifying path for testdata in Path format

### Changed

- Removed local swagger spec file
- Major refactoring and code based improvements based on feedback from pylint
- Make pylint checks mandatory
- Switched docs to alabaster theme

## [1.3.1] - 2023-08-05

### Added

- Added support for Django 4.0

### Changed

- Refactored GL script to use matrix
- Refactoring
- Added pylint to tox

### Fixed

- `EveEntity.objects.fetch_by_names_esi()` will not fetch unknown names if some names are already known

## [1.3.0] - 2023-07-11

### Added

- `EveSolarSystem.is_trig_space()``: Ability to detect if a solar system is in Triglavian space

### Fixed

- `EveSolarSystem.route_to()` no longer requests routes from ESI for systems in WH space
- `EveSolarSystem.jumps_to()` no longer requests routes from ESI for systems in WH space
- `EveSolarSystem.route_to()` / `EveSolarSystem.jumps()` now interpret all error responses from ESI route endpoint as meaning "no route"
- `EveSolarSystem.route_to()` no longer requests routes from ESI for systems in Triglavian space
- `EveSolarSystem.jumps_to()` no longer requests routes from ESI for systems in Triglavian space
- `EveSolarSystem.distance_to()` no longer requests distances from ESI for systems in Triglavian space

## [1.2.0] - 2023-06-15

### Added

- EvePlanet.type_name()

## [1.1.1] - 2023-06-04

### Fixed

- Fix image in README on PyPI

## [1.1.0] - 2023-06-04

### Added

- Models for industry activities:
  - EveIndustryActivity
  - EveIndustryActivityDuration
  - EveIndustryActivityMaterial
  - EveIndustryActivityProduct
  - EveIndustryActivitySkill

Big thanks to @iso.func for the contribution!

## [1.0.0] - 2023-05-30

### Highlights

- Enhanced functionality of eveuniverse_load_data command
- Improved stability for loading large amounts of data
- Adds support for Python 3.11
- Minimum required Django version increased to Django 3.2
- Moved to new build process (PEP 621)
- Improved typing support

### Breaking changes

The following is a list of potential breaking changes introduced with this release:

- Introduced celery_once, which requires the celery app of every installation to have a celery once configuration. Please see section "Installation / Setup celery" in the operation manual for details. Note for Alliance Auth users: This setup is fully compatible with how Alliance Auth uses celery_once. Therefore no change is required for Alliance Auth users.
- Removed deprecated constants: `EVE_CATEGORY_ID_SHIP`, `EVE_CATEGORY_ID_BLUEPRINT`, `EVE_CATEGORY_ID_STRUCTURE`, `EVE_CATEGORY_ID_SKIN`, `EVE_GROUP_ID_PLANET`, `EVE_GROUP_ID_MOON`, `EVE_GROUP_ID_ASTEROID_BELT`, `EVE_GROUP_ID_STARGATE`, `EVE_GROUP_ID_STATION`. Please use `EveCategoryId` or `EveGroupId` instead.
- Removed support for Django 2.2 (hard dependency change)
- Removed: `eveuniverse.utils.make_logger_prefix`

### Added

- Ability to load all types with load_data command and also specify sections for all load topics
- Mechanism preventing the same task running more then once (celery_once)
- Show copy button for code snippets in docs
- Ability to specify priority of child tasks when fetching objects from ESI
- Added support for Django 4.2
- Added support for Python 3.11

### Changes

- Allow loading data from multiple areas with the same load_data command
- Remove autoretry on common ESI errors, which are already covered by django-esi
- Add autoretry for operational DB errors as attempts to survive occasional deadlocks when loading lots of data from ESI
- Load tasks run with a lower task by default and priority can be configured by setting
- Removed support for Django 4.0
- Updated build process to PEP 621 specs (pyproject.toml)
- Moved configuration for isort and pylint to pyproject.toml
- Improved docs
- Improved typing support

### Fixed

- eveuniverse_load_data does not do anything when called for structures
- IDs can be 0 (e.g. category ID)

## [0.19.1] - 2023-04-05

### Fixed

- 403 error when trying to fetch type materials from ZZEVE (#14)

## [0.19.0] - 2023-01-18

## Added

- `EveSolarSystem.nearest_celestial` can now also returns stars

## Changed

- Switched from evemicros to evesdeapi for calculating nearest celestials
- Dropped support for Python 3.7. Now requires Python 3.8 or higher.

## [0.18.0] - 2022-09-19

## Added

- Command `eveuniverse_load_data` runs without user interaction via `--no-input` flag

## Changed

- Removed support for Django 2.2
- Added support for Django 4.1

## [0.17.0] - 2022-09-16

## Added

- Command `eveuniverse_load_types` runs without user interaction via `--no-input` flag (#11)

## [0.16.3] - 2022-08-01

## Changes

- `tasks.update_unresolved_eve_entities()` will now run multiple updates in parallel to speed up resolving large number of entity sets.
- `retry_backoff` reset to default for all tasks. Previous value was too large resulting in huge delays for retries.
- Switching back to the official release for django-bitfield after support for Django 4 was released.

## [0.16.2] - 2022-06-18

## Changes

- Automatic dark or light theme for Sphinx docs
- Switch to local swagger spec file
- Add wheel to PyPI deployments
- Disabled cache for `esitools.is_esi_online()`

## [0.16.1] - 2022-06-07

### Fixed

- Added missing test data in egg (#9)

## [0.16.0] - 2022-04-11

### Added

- Added field `EveType.description`

## [0.15.0] - 2022-03-10

### Added

- EveEntities can now also be fetched from ESi by name, e.g. `EveEntity.objects.get_or_create_esi(name="Merlin")`
- New method: `EveEntity.objects.fetch_by_names_esi()` for resolving names to entity objects

### Changed

- Unused parameters removed from `EveEntity.objects.get_or_create_esi()` and `EveEntity.objects.update_or_create_esi()`

### Fixed

- Field EveDogmaEffectModifier.operator can also be negative

## [0.14.0] - 2022-03-01

### Added

- Added support for Python 3.10

### Fixed

- Updated django-esi dependency to enable Django 4.0 support
- Defined AutoField

## [0.13.0] - 2022-02-28

### Added

- Added support for Django 4.0 (#10)

## [0.12.0] - 2022-02-10

### Added

- core.evexml: Tools for dealing with eve links from XML
- core.zkillboard: Generate URLs for profile pages on zKillboard

## [0.11.0] - 2022-02-02

### Added

- EveEntity.is_npc_starter_corporation

### Changed

- Stop trying to resolve known invalid IDs from ESI, e.g. 1

## [0.10.0] - 2022-01-04

### Added

- EveEntity.profile_url: URL to display this object on the default third party webpage
- EveFaction.profile_url: URL to display this object on the default third party webpage
- EveRegion.profile_url: URL to display this object on the default third party webpage
- EveSolarSystem.profile_url: URL to display this object on the default third party webpage
- EveType.profile_url: URL to display this object on the default third party webpage
- core.eveitems: URL for profile pages on eveitems webpage
- core.evewho: URL for profile pages on evewho webpage
- core.dotlan: URL for profile pages on dotlan webpage

### Changed

- Removed support for Python 3.6 & Django 3.1

### Fixed

- Missing documentation for some sections, e.g. `EveType.Section.MARKET_GROUPS`

## [0.9.0] - 2021-12-30

### Added

- `EveSolarSystem.nearest_celestial()` can not optionally filter results by group

### Changed

- Replaced `core.fuzzwork` module with `core.evemicros` for retrieving nearest celestials from API

## [0.8.2] - 2021-11-15

### Fixed

- `EveCategory.objects.update_or_create_all_esi(include_children=True, wait_for_children=False)` fails with `TypeError: update_or_create_eve_object() got an unexpected keyword argument 'entity_id'`

## [0.8.1] - 2021-10-17

### Changed

- Support for django-esi 3
- Added tests for Python 3.9, Django 3.2
- Removed tests for Django 3.0

## [0.8.0] - 2021-04-16

### Added

- New model `EveTypeMaterial` for type materials
- On-demand loading of every section(=related model disabled by default) with all manager methods
- Calculate nearest celestials within solar systems with `EveSolarSystem.nearest_celestial()`
- Added isort to CI
- Migrated to codecov

### Changed

- Removed CI tests for Django 3.0

### Fixed

- On demand loading of planets does not work probably

## [0.7.6] - 2021-01-04

### Fixed

- Removed cause for occasional transaction timeout in `EveEntity.bulk_create_esi()`
- Updated version dependency to django-esi

## [0.7.5] - 2021-01-02

### Changed

- Confirming the start of a management command now requires "y" instead of "Y" ([#3](https://gitlab.com/ErikKalkoken/django-eveuniverse/-/issues/3))

### Fixed

- EveSolarSystem.is_low_sec() and EveSolarSystem.is_high_sec() incorrect on border cases

## [0.7.4] - 2020-12-28

### Added

- Can now also return BPC icons for blueprints via EveType.icon_url()
- New parameter variant allows to specify the icon variant for EveType.icon_url()

## [0.7.3] - 2020-12-27

### Changed

- Now returns correct SKIN icons for EveTypes using the new eveskinserver. Can be turned off with new setting `EVEUNIVERSE_USE_EVESKINSERVER`.

## [0.7.2] - 2020-12-20

### Added

- Option to disable ESI checks for management command **eveuniverse_load_types**

## [0.7.1] - 2020-12-18

### Changed

- `EveType.icon_url()` can now be called with a category ID to avoid additional DB calls
- DEPRECATED: `is_blueprint` for `EveType.icon_url()`

### Fixed

- `EveType.icon_url()` now returns a generic SKIN icon for SKIN license types instead of an invalid URL

## [0.7.0] - 2020-12-16

### Added

- Boolean properties to EveEntity for identifying if an object is a certain category or if it is an NPC

## [0.6.4] - 2020-12-15

### Added

- Now submits a proper user agent with all requests to ESI

### Changed

- Removed dependency to local swagger spec file

## [0.6.3] - 2020-12-08

### Added

- Added option to load dogmas on-demand when getting/creating an EveType

## [0.6.2] - 2020-11-20

### Changed

- Management commands about if ESI is not online
- All tasks will now retry (with exponential backoff) on common HTTP errors and OSError exceptions from django-esi

## [0.6.1] - 2020-11-18

### Changed

- It is now possible to test for invalid Ids with EveEntity, e.g. `EveEntity.objects.get_or_create_esi()` will now return `None` instead of the object, if the ID was invalid.
- `EveEntity.objects.get_or_create_esi()` will now try to resolve the ID if an unresolved object with that ID already exists.

## [0.6.0] - 2020-10-28

This version adds better support for dogmas when loading types.

### Added

- Can now also get dogmas when loading types via `eveuniverse_load_types` management command
- Added option to load dogmas on-demand when updating/creating an EveType
- New function `eveuniverse.core.esitools.is_esi_online()` for querying the current status of the Eve servers
- Added info logging to load tasks
- Added info logging for `eveuniverse.tools.testdata.create_testdata()`

### Changed

- BREAKING CHANGE: Changed interface of the test tool: `eveuniverse.tools.testdata.create_testdata()`.
- Inline objects can now also be loaded async when `wait_for_children` is set to `False`
- `all_models()` is now member of `eveuniverse.models.EveUniverseBaseModel` and also returns Inline models
It requires a list of specifications instead of a dict. Also, you now need to provide the name of the model with `ModelSpec` instead of in the dict as before.
- Reduced duration for loading testdata with `eveuniverse.tools.testdata.load_testdata_from_dict()`
- Added inline models to docs
- Added core functions to docs
- Performance improvements

### Fixed

- Name field of EveDogmaEffect was too small
- Testdata creation now also supports inline models, e.g. Dogmas

## [0.5.0] - 2020-10-23

### Added

- New model `EveMarketPrice` for getting current market prices for `EveType` objects from ESI
- New setting defining max batch size in bulk methods
- New setting defining global timeout for all tasks

## [0.4.0] - 2020-10-20

### Added

- Tasks for bulk resolving and creating `EveEntity` objects
- Tasks section in the documentation

### Fixed

- Documentation update section

Thanks to Darthmoll Amatin for the contribution!

## [0.3.5] - 2020-10-13

### Fixed

- Now returns correct icon urls for blueprint types

## [0.3.4] - 2020-09-25

### Changed

- Added type checking for ids to get_or_create_esi() and update_or_create_esi()

### Fixed

- repr() now works for models with m2m relations, e.g. EveStation

## [0.3.3] - 2020-09-24

### Changed

- Added full test matrix with Django 2 and Django 3

### Fixed

- Will no longer refetch already resolved entities in bulk_create_esi

## [0.3.2] - 2020-08-17

### Fixed

- Moon failed to load when there where other planets without moons
- Load order for planet and station was not correct

## [0.3.1] - 2020-08-14

### Changed

- `EveEntity.objects.bulk_create_esi()` will now resolve all given entities from ESI, not only newly created ones

## [0.3.0] - 2020-08-11

### Added

- New management command `eveuniverse_load_types` making it easier for apps to preload the eve objects they need
- New manager method `bulk_get_or_create_esi()` for bulk loading of new eve objects.
- Type hints for all methods
- Improved documentation

### Changed

- Renamed methods that are supposed to be only used internally:
  - models.EveUniverseBaseModel: esi_mapping()
  - models.EveUniverseEntityModel and inherited models: inline_objects(), children(), esi_pk(), has_esi_path_list(), esi_path_list(), esi_path_object(), is_list_only_endpoint()
- Renamed entity_id parameter in helpers.EveEntityNameResolver.to_name()

### Fixed

## [0.2.0] - 2020-07-27

### Added

- Initial public release
