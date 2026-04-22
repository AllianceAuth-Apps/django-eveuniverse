import datetime as dt
from typing import NamedTuple
from unittest.mock import Mock, patch

import pook
from django.core.cache import cache
from django.test import TestCase
from django.utils.timezone import now

from eveuniverse.models import (
    EveAsteroidBelt,
    EveEntity,
    EveMarketGroup,
    EveMarketPrice,
    EveMoon,
    EvePlanet,
    EveRace,
    EveRegion,
    EveSolarSystem,
    EveStar,
    EveStation,
)
from eveuniverse.tests.testdata.factories_2 import (  # EveMoonFactory,
    EveConstellationFactory,
    EveMarketPriceFactory,
    EvePlanetFactory,
    EveRaceFactory,
    EveSolarSystemAbyssalSpaceFactory,
    EveSolarSystemFactory,
    EveSolarSystemHighSecFactory,
    EveSolarSystemLowSecFactory,
    EveSolarSystemNullSecFactory,
    EveSolarSystemTrigSpaceFactory,
    EveSolarSystemWSpaceFactory,
    EveTypeFactory,
    PositionFactory,
    make_esi_url,
)

MODELS_PATH = "eveuniverse.models.base"


class TestEveMarketGroup(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_fetch_group(self):
        # given
        id = 4
        name = "Ships"
        description = "Capsuleer spaceships of all sizes and roles, ..."
        pook.get(
            make_esi_url(f"markets/groups/{id}"),
            reply=200,
            response_json={
                "description": description,
                "market_group_id": id,
                "name": name,
                "types": [],
            },
        )

        # when
        obj: EveMarketGroup
        obj, created = EveMarketGroup.objects.get_or_create_esi(id=id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.description, description)


class TestEveMarketPriceManager(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_add_new_prices_from_esi_but_for_existing_types_only(self):
        # given
        et = EveTypeFactory()
        adjusted_price = 306988.09
        average_price = 306292.67
        pook.get(
            make_esi_url("markets/prices"),
            reply=200,
            response_json=[
                {
                    "adjusted_price": adjusted_price,
                    "average_price": average_price,
                    "type_id": et.id,
                },
                {"adjusted_price": 123.45, "average_price": 678.90, "type_id": 420},
            ],
        )

        # when
        result = EveMarketPrice.objects.update_from_esi()

        # then
        self.assertEqual(result, 1)
        self.assertEqual(EveMarketPrice.objects.count(), 1)
        et.refresh_from_db()
        self.assertEqual(float(et.market_price.adjusted_price), adjusted_price)
        self.assertEqual(float(et.market_price.average_price), average_price)

    @pook.on
    def test_should_not_update_prices_which_are_not_stale_1(self):
        # given
        et = EveTypeFactory()
        mp = EveMarketPriceFactory(eve_type=et)
        pook.get(
            make_esi_url("markets/prices"),
            reply=200,
            response_json=[
                {
                    "adjusted_price": 12,
                    "average_price": 42,
                    "type_id": et.id,
                }
            ],
        )

        # when
        result = EveMarketPrice.objects.update_from_esi()

        # then
        self.assertEqual(result, 0)
        et.refresh_from_db()
        self.assertEqual(float(et.market_price.adjusted_price), mp.adjusted_price)
        self.assertEqual(float(et.market_price.average_price), mp.average_price)

    @pook.on
    def test_should_update_stale_prices(self):
        # given
        et = EveTypeFactory()
        mocked_update_at = now() - dt.timedelta(minutes=65)
        with patch("django.utils.timezone.now", Mock(return_value=mocked_update_at)):
            EveMarketPriceFactory(eve_type=et)

        adjusted_price = 306988.09
        average_price = 306292.67
        pook.get(
            make_esi_url("markets/prices"),
            reply=200,
            response_json=[
                {
                    "adjusted_price": adjusted_price,
                    "average_price": average_price,
                    "type_id": et.id,
                },
                {"adjusted_price": 123.45, "average_price": 678.90, "type_id": 420},
            ],
        )

        # when
        result = EveMarketPrice.objects.update_from_esi(minutes_until_stale=60)

        # then
        self.assertEqual(result, 1)
        et.refresh_from_db()
        self.assertEqual(float(et.market_price.adjusted_price), adjusted_price)
        self.assertEqual(float(et.market_price.average_price), average_price)

    @pook.on
    def test_should_remove_obsolete_prices(self):
        # given
        et_1 = EveTypeFactory()
        mp_1 = EveMarketPriceFactory(eve_type=et_1)
        et_2 = EveTypeFactory()
        EveMarketPriceFactory(eve_type=et_2)
        pook.get(
            make_esi_url("markets/prices"),
            reply=200,
            response_json=[
                {
                    "adjusted_price": 12,
                    "average_price": 42,
                    "type_id": et_1.id,
                }
            ],
        )

        # when
        result = EveMarketPrice.objects.update_from_esi()

        # then
        self.assertEqual(result, 0)
        self.assertEqual(EveMarketPrice.objects.count(), 1)
        et_1.refresh_from_db()
        self.assertEqual(float(et_1.market_price.adjusted_price), mp_1.adjusted_price)
        self.assertEqual(float(et_1.market_price.average_price), mp_1.average_price)


class TestEveMoon(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        moon_id = 40349468
        moon_name = "Enaluri I - Moon 1"
        planet = EvePlanetFactory()
        solar_system: EveSolarSystem = planet.eve_solar_system
        position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/moons/{moon_id}"),
            reply=200,
            response_json={
                "moon_id": moon_id,
                "name": moon_name,
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
                "planets": [{"moons": [moon_id], "planet_id": planet.id}],
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
        obj: EveMoon
        obj, created = EveMoon.objects.get_or_create_esi(id=moon_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, moon_id)
        self.assertEqual(obj.name, moon_name)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.eve_planet, planet)


class TestEvePlanet(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    @pook.on
    def test_create_from_esi(self):
        # given
        planet_id = 40349467
        planet_name = "Enaluri I"
        solar_system = EveSolarSystemFactory()
        et = EveTypeFactory()
        position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/planets/{planet_id}"),
            reply=200,
            response_json={
                "name": planet_name,
                "planet_id": planet_id,
                "position": position,
                "system_id": solar_system.id,
                "type_id": et.id,
            },
        )

        # when
        obj: EvePlanet
        obj, created = EvePlanet.objects.get_or_create_esi(id=planet_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, planet_id)
        self.assertEqual(obj.name, planet_name)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.eve_solar_system, solar_system)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    @pook.on
    def test_create_from_esi_with_children_1(self):
        # given
        planet_id = 40349467
        planet_name = "Enaluri I"
        solar_system = EveSolarSystemFactory()
        et = EveTypeFactory()
        planet_position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/planets/{planet_id}"),
            reply=200,
            response_json={
                "name": planet_name,
                "planet_id": planet_id,
                "position": planet_position,
                "system_id": solar_system.id,
                "type_id": et.id,
            },
        )
        moon_id = 40349468
        pook.get(
            make_esi_url(f"universe/moons/{moon_id}"),
            reply=200,
            response_json={
                "moon_id": moon_id,
                "name": "Enaluri I - Moon 1",
                "position": PositionFactory(),
                "system_id": solar_system.id,
            },
        )
        pook.get(
            make_esi_url(f"universe/systems/{solar_system.id}"),
            reply=200,
            response_json={
                "constellation_id": solar_system.eve_constellation.id,
                "name": "Enaluri",
                "planets": [{"moons": [moon_id], "planet_id": planet_id}],
                "position": {
                    "x": solar_system.position_x,
                    "y": solar_system.position_y,
                    "z": solar_system.position_z,
                },
                "security_status": solar_system.security_status,
                "system_id": solar_system.id,
            },
            persist=True,
        )

        # when
        obj: EvePlanet
        obj, created = EvePlanet.objects.get_or_create_esi(
            id=planet_id, include_children=True
        )

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, planet_id)
        self.assertEqual(obj.name, planet_name)
        self.assertEqual(obj.position_x, planet_position["x"])
        self.assertEqual(obj.position_y, planet_position["y"])
        self.assertEqual(obj.position_z, planet_position["z"])
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.eve_solar_system, solar_system)
        self.assertTrue(EveMoon.objects.filter(id=moon_id).exists())

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    @pook.on
    def test_create_from_esi_with_children_2(self):
        # given
        planet_id = 40349467
        planet_name = "Enaluri I"
        solar_system = EveSolarSystemFactory()
        et = EveTypeFactory()
        planet_position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/planets/{planet_id}"),
            reply=200,
            response_json={
                "name": planet_name,
                "planet_id": planet_id,
                "position": planet_position,
                "system_id": solar_system.id,
                "type_id": et.id,
            },
        )
        moon_id = 40349468
        moon_name = "Enaluri I - Moon 1"
        pook.get(
            make_esi_url(f"universe/moons/{moon_id}"),
            reply=200,
            response_json={
                "moon_id": moon_id,
                "name": moon_name,
                "position": PositionFactory(),
                "system_id": solar_system.id,
            },
        )
        belt_id = 40349487
        belt_name = "Enaluri III - Asteroid Belt 1"
        pook.get(
            make_esi_url(f"universe/asteroid_belts/{belt_id}"),
            reply=200,
            response_json={
                "name": belt_name,
                "position": PositionFactory(),
                "system_id": solar_system.id,
            },
        )
        pook.get(
            make_esi_url(f"universe/systems/{solar_system.id}"),
            reply=200,
            response_json={
                "constellation_id": solar_system.eve_constellation.id,
                "name": "Enaluri",
                "planets": [
                    {
                        "asteroid_belts": [belt_id],
                        "moons": [moon_id],
                        "planet_id": planet_id,
                    }
                ],
                "position": {
                    "x": solar_system.position_x,
                    "y": solar_system.position_y,
                    "z": solar_system.position_z,
                },
                "security_status": solar_system.security_status,
                "system_id": solar_system.id,
            },
            persist=True,
        )

        # when
        obj: EvePlanet
        obj, created = EvePlanet.objects.get_or_create_esi(
            id=planet_id, include_children=True
        )

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, planet_id)
        self.assertEqual(obj.name, planet_name)
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.eve_solar_system, solar_system)

        self.assertTrue(EveAsteroidBelt.objects.filter(id=belt_id).exists())
        self.assertTrue(EveMoon.objects.filter(id=moon_id).exists())

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", False)
    @pook.on
    def test_should_not_create_children_from_esi_when_disabled(self):
        # given
        planet_id = 40349467
        planet_name = "Enaluri I"
        solar_system = EveSolarSystemFactory()
        et = EveTypeFactory()
        position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/planets/{planet_id}"),
            reply=200,
            response_json={
                "name": planet_name,
                "planet_id": planet_id,
                "position": position,
                "system_id": solar_system.id,
                "type_id": et.id,
            },
        )
        belt_id = 40349487
        moon_id = 40349468
        pook.get(
            make_esi_url(f"universe/systems/{solar_system.id}"),
            reply=200,
            response_json={
                "constellation_id": solar_system.eve_constellation.id,
                "name": "Enaluri",
                "planets": [
                    {
                        "asteroid_belts": [belt_id],
                        "moons": [moon_id],
                        "planet_id": planet_id,
                    }
                ],
                "position": {
                    "x": solar_system.position_x,
                    "y": solar_system.position_y,
                    "z": solar_system.position_z,
                },
                "security_status": solar_system.security_status,
                "system_id": solar_system.id,
            },
            persist=True,
        )

        # when
        obj: EvePlanet
        obj, created = EvePlanet.objects.get_or_create_esi(
            id=planet_id, include_children=True
        )

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, planet_id)
        self.assertEqual(obj.name, planet_name)
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.eve_solar_system, solar_system)

        self.assertFalse(EveAsteroidBelt.objects.filter(id=belt_id).exists())
        self.assertFalse(EveMoon.objects.filter(id=moon_id).exists())

    # FIXME: Does not work as expected, why?
    # @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_ASTEROID_BELTS", False)
    # @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    # @pook.on
    # def test_does_not_update_children_on_get_by_default(self):
    #     # given
    #     planet = EvePlanetFactory()
    #     solar_system: EveSolarSystem = planet.eve_solar_system
    #     pook.get(
    #         make_esi_url(f"universe/planets/{planet.id}"),
    #         reply=200,
    #         response_json={
    #             "name": planet.name,
    #             "planet_id": planet.id,
    #             "position": PositionFactory(),
    #             "system_id": solar_system.id,
    #             "type_id": planet.eve_type.id,
    #         },
    #     )
    #     moon_name = "Alpha"
    #     moon = EveMoonFactory(eve_planet=planet, name=moon_name)
    #     pook.get(
    #         make_esi_url(f"universe/moons/{moon.id}"),
    #         reply=200,
    #         response_json={
    #             "moon_id": moon.id,
    #             "name": "other name",
    #             "position": PositionFactory(),
    #             "system_id": solar_system.id,
    #         },
    #     )
    #     pook.get(
    #         make_esi_url(f"universe/systems/{solar_system.id}"),
    #         reply=200,
    #         response_json={
    #             "constellation_id": solar_system.eve_constellation.id,
    #             "name": "Enaluri",
    #             "planets": [
    #                 {
    #                     "moons": [moon.id],
    #                     "planet_id": planet.id,
    #                 }
    #             ],
    #             "position": {
    #                 "x": solar_system.position_x,
    #                 "y": solar_system.position_y,
    #                 "z": solar_system.position_z,
    #             },
    #             "security_status": solar_system.security_status,
    #             "system_id": solar_system.id,
    #         },
    #         persist=True,
    #     )

    #     # when
    #     EvePlanet.objects.get_or_create_esi(id=planet.id, include_children=True)

    #     # then
    #     moon.refresh_from_db()
    #     self.assertEqual(moon.name, moon_name)

    # @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MOONS", True)
    # @pook.on
    # def test_does_not_update_children_on_update(self):
    #     # create scenario
    #     obj, created = EvePlanet.objects.update_or_create_esi(
    #         id=40349467,
    #         include_children=True,
    #     )
    #     self.assertTrue(created)
    #     self.assertEqual(obj.id, 40349467)
    #     self.assertEqual(obj.eve_type, EveType.objects.get(id=2016))
    #     self.assertEqual(obj.eve_solar_system, EveSolarSystem.objects.get(id=30045339))
    #     self.assertTrue(EveMoon.objects.filter(id=40349468).exists())
    #     moon = EveMoon.objects.get(id=40349468)
    #     moon.name = "Dummy"
    #     moon.save()

    #     # action
    #     EvePlanet.objects.update_or_create_esi(id=40349467, include_children=True)

    #     # validate
    #     moon.refresh_from_db()
    #     self.assertNotEqual(moon.name, "Dummy")

    @pook.on
    def test_can_return_planet_type_name(self):
        # given
        obj = EvePlanetFactory()

        # when/then
        self.assertEqual(obj.type_name(), "Barren")


class TestEveRace(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        race_id = 1
        alliance_id = 500001
        description = "Founded on the tenets of patriotism and ..."
        name = "Caldari"
        pook.get(
            make_esi_url("universe/races"),
            reply=200,
            response_json=[
                {
                    "alliance_id": alliance_id,
                    "description": description,
                    "name": name,
                    "race_id": race_id,
                },
                {
                    "alliance_id": 500004,
                    "description": "Champions of liberty and defenders of ...",
                    "name": "Gallente",
                    "race_id": 8,
                },
            ],
        )

        # when
        obj: EveRace
        obj, created = EveRace.objects.get_or_create_esi(id=race_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, race_id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.alliance_id, alliance_id)

    @pook.on
    def test_create_all_from_esi(self):
        # given
        race_1_id = 1
        race_2_id = 8
        pook.get(
            make_esi_url("universe/races"),
            reply=200,
            response_json=[
                {
                    "alliance_id": 500001,
                    "description": "Founded on the tenets of patriotism and ..",
                    "name": "Caldari",
                    "race_id": race_1_id,
                },
                {
                    "alliance_id": 500004,
                    "description": "Champions of liberty and defenders of ...",
                    "name": "Gallente",
                    "race_id": race_2_id,
                },
            ],
        )

        # when
        EveRace.objects.update_or_create_all_esi()

        # then
        self.assertEqual(EveRace.objects.count(), 2)
        self.assertTrue(EveRace.objects.filter(id=race_1_id).exists())
        self.assertTrue(EveRace.objects.filter(id=race_2_id).exists())


class TestEveRegion(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        id = 10000069
        description = "Black Rise description"
        name = "Black Rise"
        pook.get(
            make_esi_url(f"universe/regions/{id}"),
            reply=200,
            response_json={
                "constellations": [20000785],
                "description": description,
                "name": name,
                "region_id": id,
            },
        )

        # when
        obj: EveRegion
        obj, created = EveRegion.objects.update_or_create_esi(id=id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.description, description)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_REGION)

    @pook.on
    def test_create_all_from_esi(self):
        # given
        id_1 = 1
        id_2 = 2
        pook.get(
            make_esi_url("universe/regions"),
            reply=200,
            response_json=[id_1, id_2],
        )
        pook.get(
            make_esi_url(f"universe/regions/{id_1}"),
            reply=200,
            response_json={
                "constellations": [20000785],
                "description": "description-1",
                "name": "name-1",
                "region_id": id_1,
            },
        )
        pook.get(
            make_esi_url(f"universe/regions/{id_2}"),
            reply=200,
            response_json={
                "constellations": [42],
                "description": "description-2",
                "name": "name-2",
                "region_id": id_2,
            },
        )

        # when
        EveRegion.objects.update_or_create_all_esi()

        # then
        self.assertTrue(EveRegion.objects.filter(id=id_1).exists())
        self.assertTrue(EveRegion.objects.filter(id=id_2).exists())


class TestEveSolarSystem(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    def test_str(self):
        obj = EveSolarSystemFactory()
        self.assertEqual(str(obj), obj.name)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    @pook.on
    def test_create_from_esi_minimal(self):
        # given
        constellation = EveConstellationFactory()
        solar_system_id = 30045339
        name = "Enaluri"
        security_status = 0.3277980387210846
        position = PositionFactory()
        pook.get(
            make_esi_url(f"universe/systems/{solar_system_id}"),
            reply=200,
            response_json={
                "constellation_id": constellation.id,
                "name": name,
                "planets": [],
                "position": position,
                "security_status": security_status,
                "system_id": solar_system_id,
            },
        )

        # when
        obj: EveSolarSystem
        obj, created = EveSolarSystem.objects.get_or_create_esi(id=30045339)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, solar_system_id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.eve_constellation, constellation)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.security_status, security_status)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_SOLAR_SYSTEM)

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", True)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", False)
    @pook.on
    def test_create_from_esi_with_stars(self):
        # given
        constellation = EveConstellationFactory()
        solar_system_id = 30045339
        name = "Enaluri"
        security_status = 0.3277980387210846
        position = PositionFactory()
        star_id = 40349466
        pook.get(
            make_esi_url(f"universe/systems/{solar_system_id}"),
            reply=200,
            response_json={
                "constellation_id": constellation.id,
                "name": name,
                "planets": [],
                "position": position,
                "security_status": security_status,
                "system_id": solar_system_id,
                "star_id": star_id,
            },
        )
        et = EveTypeFactory()
        pook.get(
            make_esi_url(f"universe/stars/{star_id}"),
            reply=200,
            response_json={
                "age": 37075060962,
                "luminosity": 0.02542000077664852,
                "name": "Enaluri - Star",
                "radius": 590000000,
                "solar_system_id": solar_system_id,
                "spectral_class": "M6 V",
                "temperature": 2385,
                "type_id": et.id,
            },
        )

        # when
        obj: EveSolarSystem
        obj, created = EveSolarSystem.objects.get_or_create_esi(id=solar_system_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, solar_system_id)
        self.assertEqual(obj.eve_star, EveStar.objects.get(id=star_id))

    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_PLANETS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARS", False)
    @patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STATIONS", True)
    @pook.on
    def test_create_from_esi_with_stations(self):
        # given
        constellation = EveConstellationFactory()
        solar_system_id = 30045339
        station_id = 60015068
        pook.get(
            make_esi_url(f"universe/systems/{solar_system_id}"),
            reply=200,
            response_json={
                "constellation_id": constellation.id,
                "name": "Enaluri",
                "planets": [],
                "position": PositionFactory(),
                "security_status": 0.3277980387210846,
                "system_id": solar_system_id,
                "star_id": 40349466,
                "stations": [station_id],
            },
        )
        et = EveTypeFactory()
        er = EveRaceFactory()
        pook.get(
            make_esi_url(f"universe/stations/{station_id}"),
            reply=200,
            response_json={
                "max_dockable_ship_volume": 50000000,
                "name": "Enaluri V - State Protectorate Assembly Plant",
                "office_rental_cost": 118744,
                "owner": 1000180,
                "position": PositionFactory(),
                "race_id": er.id,
                "reprocessing_efficiency": 0.5,
                "reprocessing_stations_take": 0.025,
                "services": [
                    "bounty-missions",
                    "courier-missions",
                    "reprocessing-plant",
                    "market",
                    "repair-facilities",
                    "factory",
                    "fitting",
                    "news",
                    "insurance",
                    "docking",
                    "office-rental",
                    "loyalty-point-store",
                    "navy-offices",
                    "security-offices",
                ],
                "station_id": station_id,
                "system_id": solar_system_id,
                "type_id": et.id,
            },
        )

        # when
        obj: EveSolarSystem
        obj, created = EveSolarSystem.objects.get_or_create_esi(
            id=solar_system_id, include_children=True
        )

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, 30045339)
        self.assertTrue(EveStation.objects.filter(id=station_id).exists())


"""
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_STARGATES", True)
@patch(MODELS_PATH + ".cache")
def test_can_calculate_route(self, mock_cache, mock_esi):
    def my_get_or_set(key, func, timeout):
        return func()


    mock_cache.get.return_value = None
    mock_cache.get_or_set.side_effect = my_get_or_set

    enaluri, _ = EveSolarSystem.objects.get_or_create_esi(
        id=30045339, include_children=True
    )
    akidagi, _ = EveSolarSystem.objects.get_or_create_esi(
        id=30045342, include_children=True
    )
    self.assertEqual(enaluri.jumps_to(akidagi), 1)
"""


class TestEveSolarSystems_SpaceTypes(TestCase):
    def test_can_identify_highsec_system(self):
        obj = EveSolarSystemHighSecFactory()
        self.assertTrue(obj.is_high_sec)
        self.assertFalse(obj.is_low_sec)
        self.assertFalse(obj.is_null_sec)
        self.assertFalse(obj.is_w_space)
        self.assertFalse(obj.is_trig_space)
        self.assertFalse(obj.is_abyssal_deadspace)

    def test_can_identify_lowsec_system(self):
        obj = EveSolarSystemLowSecFactory()
        self.assertTrue(obj.is_low_sec)
        self.assertFalse(obj.is_high_sec)
        self.assertFalse(obj.is_null_sec)
        self.assertFalse(obj.is_w_space)
        self.assertFalse(obj.is_trig_space)
        self.assertFalse(obj.is_abyssal_deadspace)

    def test_can_identify_nullsec_system(self):
        obj = EveSolarSystemNullSecFactory()
        self.assertTrue(obj.is_null_sec)
        self.assertFalse(obj.is_low_sec)
        self.assertFalse(obj.is_high_sec)
        self.assertFalse(obj.is_w_space)
        self.assertFalse(obj.is_trig_space)
        self.assertFalse(obj.is_abyssal_deadspace)

    def test_can_identify_ws_system(self):
        obj = EveSolarSystemWSpaceFactory()
        self.assertTrue(obj.is_w_space)
        self.assertFalse(obj.is_null_sec)
        self.assertFalse(obj.is_low_sec)
        self.assertFalse(obj.is_high_sec)
        self.assertFalse(obj.is_trig_space)
        self.assertFalse(obj.is_abyssal_deadspace)

    def test_can_identify_trig_system(self):
        obj = EveSolarSystemTrigSpaceFactory()
        self.assertFalse(obj.is_w_space)
        self.assertFalse(obj.is_null_sec)
        self.assertFalse(obj.is_low_sec)
        self.assertFalse(obj.is_high_sec)
        self.assertTrue(obj.is_trig_space)
        self.assertFalse(obj.is_abyssal_deadspace)

    def test_can_identify_abyssal_deadspace(self):
        obj = EveSolarSystemAbyssalSpaceFactory()
        self.assertFalse(obj.is_w_space)
        self.assertFalse(obj.is_null_sec)
        self.assertFalse(obj.is_low_sec)
        self.assertFalse(obj.is_high_sec)
        self.assertFalse(obj.is_trig_space)
        self.assertTrue(obj.is_abyssal_deadspace)

    def test_all(self):
        class Case(NamedTuple):
            name: str
            security_status: float
            is_high_sec: bool
            is_low_sec: bool
            is_null_sec: bool

        cases = [
            Case("high sec normal", 1.0, True, False, False),
            Case("low sec normal", 0.3, False, True, False),
            Case("null sec normal", -0.3, False, False, True),
            Case("low sec lower border", 0.049993, False, True, False),
            Case("low sec upper border", 0.0449, False, True, False),
        ]
        for tc in cases:
            with self.subTest(name=tc.name):
                system = EveSolarSystemFactory(security_status=tc.security_status)
                self.assertIs(system.is_high_sec, tc.is_high_sec)
                self.assertIs(system.is_low_sec, tc.is_low_sec)
                self.assertIs(system.is_null_sec, tc.is_null_sec)
