from unittest.mock import patch

import pook
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from esi.exceptions import HTTPClientError, HTTPServerError

from eveuniverse.models import (
    EveAncestry,
    EveAsteroidBelt,
    EveCategory,
    EveConstellation,
    EveDogmaAttribute,
    EveDogmaEffect,
    EveEntity,
    EveFaction,
    EveGraphic,
    EveGroup,
    EveSolarSystem,
    EveType,
)
from eveuniverse.tests.testdata.factories_2 import (
    EveBloodlineFactory,
    EveCategoryFactory,
    EveDogmaAttributeFactory,
    EveDogmaEffectFactory,
    EvePlanetFactory,
    EveSolarSystemFactory,
    PositionFactory,
    make_esi_url,
)

MODELS_PATH = "eveuniverse.models.base"


class TestEveAncestry(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        bloodline_1 = EveBloodlineFactory()
        bloodline_2 = EveBloodlineFactory()
        pook.get(
            make_esi_url("universe/ancestries"),
            reply=200,
            response_json=[
                {
                    "bloodline_id": bloodline_1.id,
                    "description": "string",
                    "icon_id": 11,
                    "id": 1,
                    "name": "Alpha",
                    "short_description": "alpha-description",
                },
                {
                    "bloodline_id": bloodline_2.id,
                    "description": "string",
                    "icon_id": 12,
                    "id": 2,
                    "name": "Bravo",
                    "short_description": "bravo-description",
                },
            ],
        )

        # when
        obj: EveAncestry
        obj, created = EveAncestry.objects.update_or_create_esi(id=2)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, 2)
        self.assertEqual(obj.name, "Bravo")
        self.assertEqual(obj.icon_id, 12)
        self.assertEqual(obj.eve_bloodline, bloodline_2)
        self.assertEqual(obj.short_description, "bravo-description")

    @pook.on
    def test_raise_404_exception_when_object_not_found(self):
        # given
        bloodline = EveBloodlineFactory()
        pook.get(
            make_esi_url("universe/ancestries"),
            reply=200,
            response_json=[
                {
                    "bloodline_id": bloodline.id,
                    "description": "string",
                    "icon_id": 11,
                    "id": 1,
                    "name": "Alpha",
                    "short_description": "alpha-description",
                }
            ],
        )

        # when/then
        with self.assertRaises(HTTPClientError) as ex:
            EveAncestry.objects.update_or_create_esi(id=666)
            self.assertEqual(ex.exception.status_code, 404)


class TestEveAsteroidBelt(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        belt_id = 40349487
        planet = EvePlanetFactory()
        solar_system: EveSolarSystem = planet.eve_solar_system
        position = PositionFactory()
        obj_name = "Enaluri III - Asteroid Belt 1"
        pook.get(
            make_esi_url(f"universe/asteroid_belts/{belt_id}"),
            reply=200,
            response_json={
                "name": obj_name,
                "position": position,
                "system_id": solar_system.id,
            },
        )
        pook.get(
            make_esi_url(f"universe/systems/{solar_system.id}"),
            reply=200,
            response_json={
                "constellation_id": solar_system.eve_constellation.id,
                "name": "Enaluri",
                "planets": [{"asteroid_belts": [belt_id], "planet_id": planet.id}],
                "position": {
                    "x": solar_system.position_x,
                    "y": solar_system.position_y,
                    "z": solar_system.position_z,
                },
                "security_status": solar_system.security_status,
                "system_id": solar_system.id,
            },
        )

        # when
        obj: EveAsteroidBelt
        obj, created = EveAsteroidBelt.objects.get_or_create_esi(id=belt_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, belt_id)
        self.assertEqual(obj.name, obj_name)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.eve_planet, planet)


@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
class TestEveCategory(TestCase):
    """These tests also cover the manager functionality shared among
    all entity models. (1/2)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_should_load_object_from_esi_when_not_exists(self):
        # given
        category_id = 6
        pook.get(
            make_esi_url(f"universe/categories/{category_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "groups": [25, 26],
                "name": "Ship",
                "published": True,
            },
        )

        # when
        obj: EveCategory
        obj, created = EveCategory.objects.get_or_create_esi(id=category_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, category_id)
        self.assertEqual(obj.name, "Ship")
        self.assertTrue(obj.published)
        self.assertEqual(obj.eve_entity_category(), "")

    @pook.on
    def test_should_return_object_when_exists(self):
        # given
        o1 = EveCategoryFactory()

        # when
        o2: EveCategory
        o2, created = EveCategory.objects.get_or_create_esi(id=o1.id)

        # then
        self.assertFalse(created)
        self.assertEqual(o2.id, o1.id)
        self.assertEqual(o2.name, o1.name)
        self.assertTrue(o2.published)

    @pook.on
    def test_should_update_from_esi_when_it_exists(self):
        # given
        o1 = EveCategoryFactory(name="Replace me", published=False)
        pook.get(
            make_esi_url(f"universe/categories/{o1.id}"),
            reply=200,
            response_json={
                "category_id": o1.id,
                "groups": [25, 26],
                "name": "Alpha",
                "published": True,
            },
        )

        # when
        o2: EveCategory
        o2, created = EveCategory.objects.update_or_create_esi(id=o1.id)

        # then
        self.assertFalse(created)
        self.assertEqual(o2.name, "Alpha")
        self.assertTrue(o2.published)

    @pook.on
    def test_can_load_from_esi_including_children(self):
        category_id = 6
        group_id = 25
        type_id = 603
        pook.get(
            make_esi_url(f"universe/categories/{category_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "groups": [25],
                "name": "Ship",
                "published": True,
            },
        )
        pook.get(
            make_esi_url(f"universe/groups/{group_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "group_id": group_id,
                "name": "Frigate",
                "published": True,
                "types": [type_id],
            },
        )
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": 150,
                "description": "",
                "dogma_attributes": [],
                "dogma_effects": [],
                "graphic_id": 314,
                "group_id": 25,
                "market_group_id": 61,
                "mass": 997000,
                "name": "Merlin",
                "packaged_volume": 2500,
                "portion_size": 1,
                "published": True,
                "radius": 39,
                "type_id": type_id,
                "volume": 16500,
            },
        )

        # when
        obj: EveCategory
        obj, created = EveCategory.objects.get_or_create_esi(
            id=category_id, include_children=True, wait_for_children=True
        )

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, category_id)
        self.assertTrue(EveGroup.objects.filter(id=group_id).exists())
        self.assertTrue(EveType.objects.filter(id=type_id).exists())

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @pook.on
    def test_can_create_types_of_category_from_esi_including_dogmas_when_disabled(self):
        # given
        category_id = 6
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
        group_id = 25
        type_id = 603
        pook.get(
            make_esi_url(f"universe/categories/{category_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "groups": [25],
                "name": "Ship",
                "published": True,
            },
        )
        pook.get(
            make_esi_url(f"universe/groups/{group_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "group_id": group_id,
                "name": "Frigate",
                "published": True,
                "types": [type_id],
            },
        )
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": 150,
                "description": "",
                "dogma_attributes": [
                    {"attribute_id": da.id, "value": 5},
                ],
                "dogma_effects": [
                    {"effect_id": de.id, "is_default": True},
                ],
                "graphic_id": 314,
                "group_id": 25,
                "market_group_id": 61,
                "mass": 997000,
                "name": "Merlin",
                "packaged_volume": 2500,
                "portion_size": 1,
                "published": True,
                "radius": 39,
                "type_id": type_id,
                "volume": 16500,
            },
        )

        # when
        EveCategory.objects.update_or_create_esi(
            id=category_id,
            include_children=True,
            wait_for_children=True,
            enabled_sections=[EveType.LOAD_DOGMAS],
        )

        # then
        et = EveType.objects.get(id=type_id)
        self.assertTrue(
            et.dogma_attributes.filter(eve_dogma_attribute_id=da.id).exists()
        )
        self.assertTrue(et.dogma_effects.filter(eve_dogma_effect_id=de.id).exists())


@override_settings(CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_GRAPHICS", False)
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
class TestEveCategory_UpdateAll(TestCase):
    """These tests also cover the manager functionality shared among
    all entity models. (2/2)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_should_update_without_children_and_sync(self):
        # given
        category_id = 6
        group_id = 25
        type_id = 603
        pook.get(
            make_esi_url("universe/categories"),
            reply=200,
            response_json=[category_id],
        )
        pook.get(
            make_esi_url(f"universe/categories/{category_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "groups": [25],
                "name": "Ship",
                "published": True,
            },
        )
        pook.get(
            make_esi_url(f"universe/groups/{group_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "group_id": group_id,
                "name": "Frigate",
                "published": True,
                "types": [type_id],
            },
        )
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": 150,
                "description": "",
                "dogma_attributes": [],
                "dogma_effects": [],
                "graphic_id": 314,
                "group_id": 25,
                "market_group_id": 61,
                "mass": 997000,
                "name": "Merlin",
                "packaged_volume": 2500,
                "portion_size": 1,
                "published": True,
                "radius": 39,
                "type_id": type_id,
                "volume": 16500,
            },
        )

        # when
        EveCategory.objects.update_or_create_all_esi(
            include_children=False, wait_for_children=True
        )

        # then
        self.assertTrue(EveCategory.objects.filter(id=category_id).exists())
        self.assertFalse(EveGroup.objects.filter(id=group_id).exists())
        self.assertFalse(EveType.objects.filter(id=type_id).exists())

    @pook.on
    def test_should_update_with_children_and_sync(self):
        # given
        category_id = 6
        group_id = 25
        type_id = 603
        pook.get(
            make_esi_url("universe/categories"),
            reply=200,
            response_json=[category_id],
        )
        pook.get(
            make_esi_url(f"universe/categories/{category_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "groups": [25],
                "name": "Ship",
                "published": True,
            },
        )
        pook.get(
            make_esi_url(f"universe/groups/{group_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "group_id": group_id,
                "name": "Frigate",
                "published": True,
                "types": [type_id],
            },
        )
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": 150,
                "description": "",
                "dogma_attributes": [],
                "dogma_effects": [],
                "graphic_id": 314,
                "group_id": 25,
                "market_group_id": 61,
                "mass": 997000,
                "name": "Merlin",
                "packaged_volume": 2500,
                "portion_size": 1,
                "published": True,
                "radius": 39,
                "type_id": type_id,
                "volume": 16500,
            },
        )

        # when
        EveCategory.objects.update_or_create_all_esi(
            include_children=True, wait_for_children=True
        )

        # then
        self.assertTrue(EveCategory.objects.filter(id=category_id).exists())
        self.assertTrue(EveGroup.objects.filter(id=group_id).exists())
        self.assertTrue(EveType.objects.filter(id=type_id).exists())

    @pook.on
    def test_should_update_with_children_and_async(self):
        # given
        category_id = 6
        group_id = 25
        type_id = 603
        pook.get(
            make_esi_url("universe/categories"),
            reply=200,
            response_json=[category_id],
        )
        pook.get(
            make_esi_url(f"universe/categories/{category_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "groups": [25],
                "name": "Ship",
                "published": True,
            },
        )
        pook.get(
            make_esi_url(f"universe/groups/{group_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "group_id": group_id,
                "name": "Frigate",
                "published": True,
                "types": [type_id],
            },
        )
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": 150,
                "description": "",
                "dogma_attributes": [],
                "dogma_effects": [],
                "graphic_id": 314,
                "group_id": 25,
                "market_group_id": 61,
                "mass": 997000,
                "name": "Merlin",
                "packaged_volume": 2500,
                "portion_size": 1,
                "published": True,
                "radius": 39,
                "type_id": type_id,
                "volume": 16500,
            },
        )

        # when
        EveCategory.objects.update_or_create_all_esi(
            include_children=True, wait_for_children=False
        )

        # then
        self.assertTrue(EveCategory.objects.filter(id=category_id).exists())
        self.assertTrue(EveGroup.objects.filter(id=group_id).exists())
        self.assertTrue(EveType.objects.filter(id=type_id).exists())

    @pook.on
    def test_should_raise_exception_on_error(self):
        # given
        pook.get(
            make_esi_url("universe/categories"),
            reply=500,
            response_json={"error": "some error"},
        )

        # when/then
        with self.assertRaises(HTTPServerError):
            EveCategory.objects.update_or_create_all_esi(
                include_children=False, wait_for_children=True
            )


class TestBulkGetOrCreateEsi(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_load_all_from_esi(self):
        # given
        obj_1_id = 6
        obj_2_id = 7
        pook.get(
            make_esi_url(f"universe/categories/{obj_1_id}"),
            reply=200,
            response_json={
                "category_id": obj_1_id,
                "groups": [],
                "name": "Alpha",
                "published": True,
            },
        )
        pook.get(
            make_esi_url(f"universe/categories/{obj_2_id}"),
            reply=200,
            response_json={
                "category_id": obj_1_id,
                "groups": [],
                "name": "Bravo",
                "published": True,
            },
        )

        # when
        result = EveCategory.objects.bulk_get_or_create_esi(ids=[obj_1_id, obj_2_id])

        # then
        self.assertEqual({x.id for x in result}, {obj_1_id, obj_2_id})
        self.assertTrue(EveCategory.objects.filter(id=obj_1_id).exists())
        self.assertTrue(EveCategory.objects.filter(id=obj_2_id).exists())

    @pook.on
    def test_can_load_parts_from_esi(self):
        # given
        obj_1_id = 6
        obj_2_id = 7
        EveCategoryFactory(id=obj_1_id)
        pook.get(
            make_esi_url(f"universe/categories/{obj_2_id}"),
            reply=200,
            response_json={
                "category_id": obj_1_id,
                "groups": [],
                "name": "Bravo",
                "published": True,
            },
        )

        # when
        result = EveCategory.objects.bulk_get_or_create_esi(ids=[obj_1_id, obj_2_id])

        # then
        self.assertEqual({x.id for x in result}, {obj_1_id, obj_2_id})


class TestEveConstellation(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        constellation_id = 20000785
        region_id = 10000069
        pook.get(
            make_esi_url(f"universe/regions/{region_id}"),
            reply=200,
            response_json={
                "constellations": [constellation_id],
                "description": "...",
                "name": "Black Rise",
                "region_id": region_id,
            },
        )
        position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/constellations/{constellation_id}"),
            reply=200,
            response_json={
                "constellation_id": constellation_id,
                "name": "Ishaga",
                "position": position,
                "region_id": region_id,
                "systems": [30045339],
            },
        )

        # when
        obj: EveConstellation
        obj, created = EveConstellation.objects.update_or_create_esi(
            id=constellation_id
        )

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, constellation_id)
        self.assertEqual(obj.name, "Ishaga")
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.eve_region.id, region_id)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_CONSTELLATION)


@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
class TestEveDogmaAttribute(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_create_from_esi(self):
        # given
        attribute_id = 271
        pook.get(
            make_esi_url(f"dogma/attributes/{attribute_id}"),
            reply=200,
            response_json={
                "attribute_id": attribute_id,
                "default_value": 1,
                "description": "Multiplies EM damage taken by shield",
                "display_name": "Shield EM Damage Resistance",
                "icon_id": 1396,
                "name": "shieldEmDamageResonance",
                "published": True,
                "unit_id": 108,
            },
        )

        # when
        obj: EveDogmaAttribute
        obj, created = EveDogmaAttribute.objects.update_or_create_esi(id=attribute_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, attribute_id)
        self.assertEqual(obj.name, "shieldEmDamageResonance")
        self.assertEqual(obj.default_value, 1)
        self.assertEqual(obj.description, "Multiplies EM damage taken by shield")
        self.assertEqual(obj.display_name, "Shield EM Damage Resistance")
        self.assertEqual(obj.icon_id, 1396)
        self.assertTrue(obj.published)
        self.assertEqual(obj.eve_unit.id, 108)


@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", True)
class TestEveDogmaEffect(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_create_from_esi(self):
        # given
        attribute_1_id = 271
        attribute_2_id = 463
        effect_id = 1816
        pook.get(
            make_esi_url(f"dogma/attributes/{attribute_1_id}"),
            reply=200,
            response_json={
                "attribute_id": attribute_1_id,
                "default_value": 1,
                "description": "Multiplies EM damage taken by shield",
                "display_name": "Shield EM Damage Resistance",
                "icon_id": 1396,
                "name": "shieldEmDamageResonance",
                "published": True,
                "unit_id": 108,
            },
        )
        pook.get(
            make_esi_url(f"dogma/attributes/{attribute_2_id}"),
            reply=200,
            response_json={
                "attribute_id": attribute_2_id,
                "default_value": 0,
                "description": "",
                "display_name": "",
                "high_is_good": True,
                "icon_id": 0,
                "name": "shipBonusCF",
                "stackable": True,
            },
        )
        pook.get(
            make_esi_url(f"dogma/effects/{effect_id}"),
            reply=200,
            response_json={
                "description": "",
                "display_name": "",
                "effect_category": 0,
                "effect_id": effect_id,
                "icon_id": 0,
                "modifiers": [
                    {
                        "domain": "shipID",
                        "func": "ItemModifier",
                        "modified_attribute_id": attribute_1_id,
                        "modifying_attribute_id": attribute_2_id,
                        "operator": 6,
                    }
                ],
                "name": "shipShieldEMResistanceCF2",
            },
        )

        # when
        obj: EveDogmaEffect
        obj, created = EveDogmaEffect.objects.update_or_create_esi(id=effect_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, effect_id)
        self.assertEqual(obj.name, "shipShieldEMResistanceCF2")
        self.assertEqual(obj.display_name, "")
        self.assertEqual(obj.effect_category, 0)
        self.assertEqual(obj.icon_id, 0)
        modifiers = obj.modifiers.first()
        self.assertEqual(modifiers.domain, "shipID")
        self.assertEqual(modifiers.func, "ItemModifier")
        self.assertEqual(
            modifiers.modified_attribute,
            EveDogmaAttribute.objects.get(id=attribute_1_id),
        )
        self.assertEqual(
            modifiers.modifying_attribute,
            EveDogmaAttribute.objects.get(id=463),
        )
        self.assertEqual(modifiers.operator, 6)


class TestEveFaction(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_create_from_esi(self):
        # given
        faction_id = 500001
        solar_system = EveSolarSystemFactory()
        pook.get(
            make_esi_url("universe/factions"),
            reply=200,
            response_json=[
                {
                    "corporation_id": 1000035,
                    "description": "The Caldari State is ruled by several mega-corporations. ...",
                    "faction_id": faction_id,
                    "is_unique": True,
                    "militia_corporation_id": 1000180,
                    "name": "Caldari State",
                    "size_factor": 5,
                    "solar_system_id": solar_system.id,
                    "station_count": 1503,
                    "station_system_count": 503,
                },
                {
                    "corporation_id": 1000051,
                    "description": "The Minmatar Republic was formed ...",
                    "faction_id": 500002,
                    "is_unique": True,
                    "militia_corporation_id": 1000182,
                    "name": "Minmatar Republic",
                    "size_factor": 5,
                    "solar_system_id": solar_system.id,
                    "station_count": 570,
                    "station_system_count": 291,
                },
            ],
        )

        # when
        obj: EveFaction
        obj, created = EveFaction.objects.get_or_create_esi(id=faction_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, faction_id)
        self.assertEqual(obj.name, "Caldari State")
        self.assertTrue(obj.is_unique)
        self.assertEqual(obj.militia_corporation_id, 1000180)
        self.assertEqual(obj.eve_solar_system, solar_system)
        self.assertEqual(obj.size_factor, 5)
        self.assertEqual(obj.station_count, 1503)
        self.assertEqual(obj.station_system_count, 503)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_FACTION)


class TestEveGraphic(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        id = 314
        pook.get(
            make_esi_url(f"universe/graphics/{id}"),
            reply=200,
            response_json={
                "graphic_id": 314,
                "sof_dna": "cf7_t1:caldaribase:caldari",
                "sof_fation_name": "caldaribase",
                "sof_hull_name": "cf7_t1",
                "sof_race_name": "caldari",
            },
        )

        # when
        obj: EveGraphic
        obj, created = EveGraphic.objects.get_or_create_esi(id=id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, id)
        self.assertEqual(obj.sof_dna, "cf7_t1:caldaribase:caldari")
        self.assertEqual(obj.sof_fation_name, "caldaribase")
        self.assertEqual(obj.sof_hull_name, "cf7_t1")
        self.assertEqual(obj.sof_race_name, "caldari")


class TestEveGroup(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_create_from_esi(self):
        # given
        category_id = 6
        EveCategoryFactory(id=category_id)
        group_id = 25
        group_name = "Frigate"
        pook.get(
            make_esi_url(f"universe/groups/{group_id}"),
            reply=200,
            response_json={
                "category_id": category_id,
                "group_id": group_id,
                "name": group_name,
                "published": True,
                "types": [603],
            },
        )

        # when
        obj: EveGroup
        obj, created = EveGroup.objects.get_or_create_esi(id=group_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, group_id)
        self.assertEqual(obj.name, group_name)
        self.assertTrue(obj.published)


# -------
# -------
