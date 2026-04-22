from unittest.mock import patch

import pook
from django.core.cache import cache
from django.test import TestCase

from eveuniverse.helpers import meters_to_ly
from eveuniverse.models import EveEntity, EveStar, EveStargate, EveStation
from eveuniverse.tests.testdata.factories_2 import (
    EveRaceFactory,
    EveSolarSystemFactory,
    EveSolarSystemLowSecFactory,
    EveSolarSystemTrigSpaceFactory,
    EveSolarSystemWSpaceFactory,
    EveStargateFactory,
    EveTypeFactory,
    PositionFactory,
    make_esi_url,
)

MODELS_PATH = "eveuniverse.models.base"


class TestEveSolarSystem_DistanceTo(TestCase):
    def test_should_calculate_distance_between_normal_systems(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )
        b = EveSolarSystemLowSecFactory(
            position_x=-211265901041153470,
            position_y=55806528490315120,
            position_z=81416396747037220,
        )

        # when
        result = a.distance_to(b)

        # then
        self.assertEqual(round(meters_to_ly(result), 3), 6.831)

    def test_should_return_none_when_one_system_in_wh_space_1(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )
        b = EveSolarSystemWSpaceFactory(
            position_x=-211265901041153470,
            position_y=55806528490315120,
            position_z=81416396747037220,
        )

        # when
        result = a.distance_to(b)
        # then
        self.assertIsNone(result)

    def test_should_return_none_when_one_system_in_wh_space_2(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )
        b = EveSolarSystemWSpaceFactory(
            position_x=-211265901041153470,
            position_y=55806528490315120,
            position_z=81416396747037220,
        )

        # when
        result = b.distance_to(a)
        # then
        self.assertIsNone(result)

    def test_should_return_none_when_no_destination(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )

        # when
        result = a.distance_to(None)

        # then
        self.assertIsNone(result)

    def test_should_return_none_when_origin_has_not_coordinates(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=None,
            position_y=None,
            position_z=None,
        )
        b = EveSolarSystemLowSecFactory(
            position_x=-211265901041153470,
            position_y=55806528490315120,
            position_z=81416396747037220,
        )

        # when
        result = a.distance_to(b)

        # then
        self.assertIsNone(result)

    def test_should_return_none_when_destination_has_not_coordinates(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )
        b = EveSolarSystemLowSecFactory(
            position_x=None,
            position_y=None,
            position_z=None,
        )

        # when
        result = a.distance_to(b)

        # then
        self.assertIsNone(result)

    def test_should_return_none_when_one_system_is_in_trig_space_1(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )
        b = EveSolarSystemTrigSpaceFactory(
            position_x=-211265901041153470,
            position_y=55806528490315120,
            position_z=81416396747037220,
        )

        # when
        result = a.distance_to(b)

        # then
        self.assertIsNone(result)

    def test_should_return_none_when_one_system_is_in_trig_space_2(self):
        # given
        a = EveSolarSystemLowSecFactory(
            position_x=-227875173313944580,
            position_y=104688385699531790,
            position_z=120279417692650270,
        )
        b = EveSolarSystemTrigSpaceFactory(
            position_x=-211265901041153470,
            position_y=55806528490315120,
            position_z=81416396747037220,
        )

        # when
        result = b.distance_to(a)

        # then
        self.assertIsNone(result)


class TestEveSolarSystemJumpsTo(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_calculate_jumps(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemLowSecFactory()
        c = EveSolarSystemLowSecFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{c.id}"),
            reply=200,
            response_json=[a.id, b.id, c.id],
        )

        # when/then
        self.assertEqual(a.jumps_to(c), 2)

    @pook.on
    def test_route_calc_returns_none_if_no_route_found(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemLowSecFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{b.id}"),
            reply=404,
            response_json={"error": "not found"},
        )

        # when/then
        self.assertIsNone(a.jumps_to(b))

    @pook.on
    def test_should_return_none_if_any_system_is_in_wh_space(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemWSpaceFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{b.id}"),
            reply=500,
            response_json=[],
        )

        # when/then
        self.assertIsNone(a.jumps_to(b))
        self.assertIsNone(b.jumps_to(a))

    @pook.on
    def test_should_return_none_if_any_system_is_in_trig_space(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemTrigSpaceFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{b.id}"),
            reply=500,
            response_json=[],
        )

        # when/then
        self.assertIsNone(a.jumps_to(b))
        self.assertIsNone(b.jumps_to(a))


class TestEveSolarSystemRouteTo(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_should_return_valid_route(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemLowSecFactory()
        c = EveSolarSystemLowSecFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{c.id}"),
            reply=200,
            response_json=[a.id, b.id, c.id],
        )

        # when
        result = a.route_to(c)

        # then
        self.assertListEqual(result, [(a, False), (b, False), (c, False)])

    @pook.on
    def test_should_return_none_when_no_route_found(self):
        # given
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemLowSecFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{b.id}"),
            reply=404,
            response_json={"error": "not found"},
        )

        # when
        result = a.route_to(b)

        # then
        self.assertIsNone(result)

    @pook.on
    def test_should_return_none_if_any_system_is_in_wh_space(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemWSpaceFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{b.id}"),
            reply=500,
            response_json=[],
        )

        # when/then
        self.assertIsNone(a.route_to(b))
        self.assertIsNone(b.route_to(a))

    @pook.on
    def test_should_return_none_if_any_system_is_in_trig_space(self):
        # given
        a = EveSolarSystemLowSecFactory()
        b = EveSolarSystemTrigSpaceFactory()
        pook.get(
            make_esi_url(f"route/{a.id}/{b.id}"),
            reply=500,
            response_json=[],
        )

        # when/then
        self.assertIsNone(a.route_to(b))
        self.assertIsNone(b.route_to(a))


@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_DOGMAS", False)
@patch(MODELS_PATH + ".EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
class TestEveStar(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        star_id = 40349466
        age = 37075060962
        et = EveTypeFactory()
        luminosity = 0.02542000077664852
        name = "Enaluri - Star"
        radius = 590000000
        solar_system = EveSolarSystemFactory()
        spectral_class = "M6 V"
        temperature = 2385
        pook.get(
            make_esi_url(f"universe/stars/{star_id}"),
            reply=200,
            response_json={
                "age": age,
                "luminosity": luminosity,
                "name": name,
                "radius": radius,
                "solar_system_id": solar_system.id,
                "spectral_class": spectral_class,
                "temperature": temperature,
                "type_id": et.id,
            },
        )

        # when
        obj: EveStar
        obj, created = EveStar.objects.update_or_create_esi(id=star_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.age, age)
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.id, star_id)
        self.assertEqual(obj.luminosity, luminosity)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.radius, radius)
        self.assertEqual(obj.spectral_class, spectral_class)
        self.assertEqual(obj.temperature, temperature)


class TestEveStargate(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_should_create_stargate_from_esi(self):
        # given
        stargate_id = 50016284
        destination = EveStargateFactory()
        et = EveTypeFactory()
        name = "Stargate (Akidagi)"
        position = PositionFactory()
        solar_system = EveSolarSystemFactory()
        pook.get(
            make_esi_url(f"universe/stargates/{stargate_id}"),
            reply=200,
            response_json={
                "destination": {
                    "stargate_id": destination.id,
                    "system_id": destination.eve_solar_system.id,
                },
                "name": name,
                "position": position,
                "stargate_id": stargate_id,
                "system_id": solar_system.id,
                "type_id": et.id,
            },
        )

        # when
        obj: EveStargate
        obj, created = EveStargate.objects.get_or_create_esi(id=stargate_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, stargate_id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.eve_solar_system, solar_system)
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.destination_eve_stargate, destination)
        self.assertEqual(obj.destination_eve_solar_system, destination.eve_solar_system)
        self.assertEqual(obj.eve_entity_category(), "")

    @pook.on
    def test_should_create_stargate_from_esi_without_destination(self):
        # given
        stargate_id = 50016284
        et = EveTypeFactory()
        name = "Stargate (Akidagi)"
        position = PositionFactory()
        solar_system = EveSolarSystemFactory()
        pook.get(
            make_esi_url(f"universe/stargates/{stargate_id}"),
            reply=200,
            response_json={
                "destination": {
                    "stargate_id": 42,
                    "system_id": 666,
                },
                "name": name,
                "position": position,
                "stargate_id": stargate_id,
                "system_id": solar_system.id,
                "type_id": et.id,
            },
        )

        # when
        obj: EveStargate
        obj, created = EveStargate.objects.get_or_create_esi(id=stargate_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, stargate_id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.eve_solar_system, solar_system)
        self.assertEqual(obj.eve_type, et)
        self.assertIsNone(obj.destination_eve_stargate)
        self.assertIsNone(obj.destination_eve_solar_system)
        self.assertEqual(obj.eve_entity_category(), "")


class TestEveStation(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_create_from_esi(self):
        # given
        station_id = 60015068
        et = EveTypeFactory()
        er = EveRaceFactory()
        es = EveSolarSystemFactory()
        position = PositionFactory()
        owner_id = 1000180
        volume = 50000000
        cost = 118744
        reprocessing_efficiency = 0.5
        reprocessing_stations_take = 0.025
        name = "Enaluri V - State Protectorate Assembly Plant"
        pook.get(
            make_esi_url(f"universe/stations/{station_id}"),
            reply=200,
            response_json={
                "max_dockable_ship_volume": volume,
                "name": name,
                "office_rental_cost": cost,
                "owner": owner_id,
                "position": position,
                "race_id": er.id,
                "reprocessing_efficiency": reprocessing_efficiency,
                "reprocessing_stations_take": reprocessing_stations_take,
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
                "system_id": es.id,
                "type_id": et.id,
            },
        )

        # when
        obj: EveStation
        obj, created = EveStation.objects.update_or_create_esi(id=station_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, station_id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.max_dockable_ship_volume, volume)
        self.assertEqual(obj.office_rental_cost, cost)
        self.assertEqual(obj.owner_id, owner_id)
        self.assertEqual(obj.position_x, position["x"])
        self.assertEqual(obj.position_y, position["y"])
        self.assertEqual(obj.position_z, position["z"])
        self.assertEqual(obj.reprocessing_efficiency, reprocessing_efficiency)
        self.assertEqual(obj.reprocessing_stations_take, reprocessing_stations_take)
        self.assertEqual(obj.eve_race, er)
        self.assertEqual(obj.eve_type, et)
        self.assertEqual(obj.eve_solar_system, es)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_STATION)

        self.assertSetEqual(
            set(obj.services.values_list("name", flat=True)),
            {
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
            },
        )
