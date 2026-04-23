from unittest.mock import patch

import pook
from django.core.cache import cache
from django.test import TestCase

from eveuniverse.models import EveEntity, EveStar, EveStargate, EveStation
from eveuniverse.tests.testdata.factories_2 import (
    EveRaceFactory,
    EveSolarSystemFactory,
    EveStargateFactory,
    EveTypeFactory,
    PositionFactory,
    make_esi_url,
)

MODELS_PATH = "eveuniverse.models.base"


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
