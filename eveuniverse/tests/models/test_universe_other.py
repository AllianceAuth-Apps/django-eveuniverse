import pook
from django.core.cache import cache
from django.test import TestCase
from esi.exceptions import HTTPClientError

from eveuniverse.models import EveAncestry, EveEntity, EveFaction
from eveuniverse.tests.testdata.factories_2 import (
    EveBloodlineFactory,
    EveSolarSystemFactory,
    make_esi_url,
)


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
        self.assertEqual(obj.size_factor, 5)
        self.assertEqual(obj.station_count, 1503)
        self.assertEqual(obj.station_system_count, 503)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_FACTION)
