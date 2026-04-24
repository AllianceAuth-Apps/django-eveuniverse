"""Eve Entity tests."""

from typing import NamedTuple

import pook
from django.core.cache import cache
from django.db.models import QuerySet
from django.test import TestCase

from eveuniverse.managers.entities import EveEntityNameResolver
from eveuniverse.models import EveEntity
from eveuniverse.tests.helpers import queryset_pks
from eveuniverse.tests.testdata.factories_2 import (
    EveEntityAllianceFactory,
    EveEntityCharacterFactory,
    EveEntityCorporationFactory,
    EveEntityFactory,
    EveEntityUnresolvedFactory,
    make_esi_url,
)


class TestEveEntityQuerySet(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_update_entities_from_esi(self):
        # given
        character = EveEntityCharacterFactory()
        corporation = EveEntityCorporationFactory()
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": "character", "id": character.id, "name": "Alpha"},
                {"category": "corporation", "id": corporation.id, "name": "Bravo"},
            ],
        )

        # when
        got = EveEntity.objects.all().update_from_esi()

        # then
        self.assertEqual(got, 2)
        character.refresh_from_db()
        self.assertEqual(character.name, "Alpha")
        self.assertEqual(character.category, EveEntity.CATEGORY_CHARACTER)
        corporation.refresh_from_db()
        self.assertEqual(corporation.name, "Bravo")
        self.assertEqual(corporation.category, EveEntity.CATEGORY_CORPORATION)

    @pook.on
    def test_can_divide_and_conquer(self):
        # given
        character = EveEntityCharacterFactory()
        invalid = EveEntityFactory(id=666, name="", category="")
        pook.post(
            make_esi_url("universe/names"),
            reply=404,
            json=[character.id, invalid.id],
            response_json={"error": "invalid"},
        )
        pook.post(
            make_esi_url("universe/names"),
            reply=404,
            json=[invalid.id, character.id],
            response_json={"error": "invalid"},
        )
        pook.post(
            make_esi_url("universe/names"),
            reply=404,
            json=[invalid.id],
            response_json={"error": "invalid"},
        )
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            json=[character.id],
            response_json=[
                {"category": "character", "id": character.id, "name": "Alpha"},
            ],
        )

        # when
        got = EveEntity.objects.all().update_from_esi()

        # then
        self.assertEqual(got, 1)
        character.refresh_from_db()
        self.assertEqual(character.name, "Alpha")
        self.assertEqual(character.category, EveEntity.CATEGORY_CHARACTER)

    @pook.on
    def test_can_ignore_invalid_ids(self):
        # given
        character = EveEntityCharacterFactory()
        EveEntityFactory(id=1, name="", category="")
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": "character", "id": character.id, "name": "Alpha"},
            ],
        )

        # when
        got = EveEntity.objects.all().update_from_esi()

        # then
        self.assertEqual(got, 1)
        character.refresh_from_db()
        self.assertEqual(character.name, "Alpha")
        self.assertEqual(character.category, EveEntity.CATEGORY_CHARACTER)


class TestEveEntityModel(TestCase):
    def test_is_npc_1(self):
        """when entity is NPC character, then return True"""
        obj = EveEntity(id=3019583, category=EveEntity.CATEGORY_CHARACTER)
        self.assertTrue(obj.is_npc)

    def test_is_npc_2(self):
        """when entity is NPC corporation, then return True"""
        obj = EveEntity(id=1000274, category=EveEntity.CATEGORY_CORPORATION)
        self.assertTrue(obj.is_npc)

    def test_is_npc_3(self):
        """when entity is normal character, then return False"""
        obj = EveEntity(id=93330670, category=EveEntity.CATEGORY_CHARACTER)
        self.assertFalse(obj.is_npc)

    def test_is_npc_4(self):
        """when entity is normal corporation, then return False"""
        obj = EveEntity(id=98394960, category=EveEntity.CATEGORY_CORPORATION)
        self.assertFalse(obj.is_npc)

    def test_is_npc_5(self):
        """when entity is normal alliance, then return False"""
        obj = EveEntity(id=99008435, category=EveEntity.CATEGORY_ALLIANCE)
        self.assertFalse(obj.is_npc)

    def test_is_npc_starter_corporation_1(self):
        obj = EveEntity(id=1000165, category=EveEntity.CATEGORY_CORPORATION)
        self.assertTrue(obj.is_npc_starter_corporation)

    def test_is_npc_starter_corporation_2(self):
        obj = EveEntity(id=98394960, category=EveEntity.CATEGORY_CORPORATION)
        self.assertFalse(obj.is_npc_starter_corporation)

    def test_is_npc_starter_corporation_3(self):
        obj = EveEntity(id=1000274, category=EveEntity.CATEGORY_CORPORATION)
        self.assertFalse(obj.is_npc_starter_corporation)

    def test_repr(self):
        # given
        obj = EveEntity(
            id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
        )
        # when/then
        self.assertEqual(
            repr(obj), "EveEntity(category='character', id=1001, name='Bruce Wayne')"
        )

    def test_can_create_icon_urls_alliance(self):
        obj = EveEntity(id=3001, category=EveEntity.CATEGORY_ALLIANCE)
        expected = "https://images.evetech.net/alliances/3001/logo?size=128"
        self.assertEqual(obj.icon_url(128), expected)

    def test_can_create_icon_urls_character(self):
        obj = EveEntity(id=1001, category=EveEntity.CATEGORY_CHARACTER)
        expected = "https://images.evetech.net/characters/1001/portrait?size=128"
        self.assertEqual(obj.icon_url(128), expected)

    def test_can_create_icon_urls_corporation(self):
        obj = EveEntity(id=2001, category=EveEntity.CATEGORY_CORPORATION)
        expected = "https://images.evetech.net/corporations/2001/logo?size=128"
        self.assertEqual(obj.icon_url(128), expected)

    def test_can_create_icon_urls_type(self):
        obj = EveEntity(id=603, category=EveEntity.CATEGORY_INVENTORY_TYPE)
        expected = "https://images.evetech.net/types/603/icon?size=128"
        self.assertEqual(obj.icon_url(128), expected)


class TestEveEntityManagerESI(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_can_create_new_from_esi_when_not_exists(self):
        # given
        entity_id = 1001
        name = "Alpha"
        category = EveEntity.CATEGORY_CHARACTER
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category, "id": entity_id, "name": name},
            ],
        )

        # when
        obj: EveEntity
        obj, created = EveEntity.objects.get_or_create_esi(id=1001)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.id, entity_id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.category, category)

    @pook.on
    def test_should_return_existing_object_when_exists(self):
        # given
        obj = EveEntityCharacterFactory()

        # when
        obj_2: EveEntity
        obj_2, created = EveEntity.objects.get_or_create_esi(id=obj.id)

        # then
        self.assertFalse(created)
        self.assertEqual(obj, obj_2)

    @pook.on
    def test_should_return_empty_when_object_not_found_by_esi(self):
        # given
        pook.post(
            make_esi_url("universe/names"),
            reply=404,
            response_json={"errors": "not found"},
        )

        # when
        obj: EveEntity
        obj, created = EveEntity.objects.get_or_create_esi(id=666)

        # then
        self.assertIsNone(obj)
        self.assertFalse(created)

    @pook.on
    def test_should_update_from_esi_when_unresolved(self):
        # given
        obj = EveEntityUnresolvedFactory()
        name = "Alpha"
        category = EveEntity.CATEGORY_CHARACTER
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category, "id": obj.id, "name": name},
            ],
        )

        # when
        obj: EveEntity
        obj, created = EveEntity.objects.get_or_create_esi(id=obj.id)

        # then
        self.assertFalse(created)
        self.assertEqual(obj.id, obj.id)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.category, category)

    @pook.on
    def test_can_update_existing_from_esi(self):
        # given
        obj_1 = EveEntityCharacterFactory()
        name = "Alpha"
        category = EveEntity.CATEGORY_CHARACTER
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {
                    "category": category,
                    "id": obj_1.id,
                    "name": name,
                },
            ],
        )

        # when
        obj_2: EveEntity
        obj_2, created = EveEntity.objects.update_or_create_esi(id=obj_1.id)

        # then
        self.assertFalse(created)
        self.assertEqual(obj_2.id, obj_1.id)
        self.assertEqual(obj_2.name, name)
        self.assertEqual(obj_2.category, category)

    @pook.on
    def test_should_return_none_when_trying_to_create_from_invalid_id(self):
        # when
        obj, created = EveEntity.objects.update_or_create_esi(id=1)

        # then
        self.assertFalse(created)
        self.assertIsNone(obj)

    @pook.on
    def test_update_or_create_all_esi_raises_exception(self):
        with self.assertRaises(NotImplementedError):
            EveEntity.objects.update_or_create_all_esi()

    @pook.on
    def test_can_bulk_update_new_from_esi(self):
        # given
        obj_1 = EveEntityUnresolvedFactory()
        name_1 = "Alpha"
        category_1 = EveEntity.CATEGORY_CHARACTER
        obj_2 = EveEntityUnresolvedFactory()
        name_2 = "Bravo"
        category_2 = EveEntity.CATEGORY_ALLIANCE
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category_1, "id": obj_1.id, "name": name_1},
                {"category": category_2, "id": obj_2.id, "name": name_2},
            ],
        )

        # when
        got = EveEntity.objects.bulk_update_new_esi()

        # then
        self.assertEqual(got, 2)

        obj_1.refresh_from_db()
        self.assertEqual(obj_1.name, name_1)
        self.assertEqual(obj_1.category, category_1)

        obj_2.refresh_from_db()
        self.assertEqual(obj_2.name, name_2)
        self.assertEqual(obj_2.category, category_2)

    @pook.on
    def test_can_bulk_update_all(self):
        # given
        obj_1 = EveEntityCharacterFactory()
        name_1 = "Alpha"
        obj_2 = EveEntityAllianceFactory()
        name_2 = "Bravo"
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": obj_1.category, "id": obj_1.id, "name": name_1},
                {"category": obj_2.category, "id": obj_2.id, "name": name_2},
            ],
        )

        # when
        got = EveEntity.objects.bulk_update_all_esi()

        # then
        self.assertEqual(got, 2)

        obj_1.refresh_from_db()
        self.assertEqual(obj_1.name, name_1)

        obj_2.refresh_from_db()
        self.assertEqual(obj_2.name, name_2)

    @pook.on
    def test_can_resolve_name_when_exists(self):
        # given
        entity_id = 1001
        name = "Alpha"
        category = EveEntity.CATEGORY_CHARACTER
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[{"category": category, "id": entity_id, "name": name}],
        )

        # when
        got = EveEntity.objects.resolve_name(1001)
        self.assertEqual(got, "Alpha")

    @pook.on
    def test_can_resolve_name_when_not_exists(self):
        # given
        entity_id = 1001
        pook.post(
            make_esi_url("universe/names"),
            reply=404,
            response_json={"error": "error"},
        )

        # when
        self.assertEqual(EveEntity.objects.resolve_name(entity_id), "")
        self.assertEqual(EveEntity.objects.resolve_name(None), "")

    @pook.on
    def test_can_bulk_resolve_names(self):
        # given
        obj_1_id = 1001
        name_1 = "Alpha"
        category_1 = EveEntity.CATEGORY_CHARACTER
        obj_2_id = 1002
        name_2 = "Bravo"
        category_2 = EveEntity.CATEGORY_ALLIANCE
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category_1, "id": obj_1_id, "name": name_1},
                {"category": category_2, "id": obj_2_id, "name": name_2},
            ],
        )

        # when
        resolver: EveEntityNameResolver = EveEntity.objects.bulk_resolve_names(
            [obj_1_id, obj_2_id]
        )

        # then
        self.assertEqual(resolver.to_name(obj_1_id), "Alpha")
        self.assertEqual(resolver.to_name(obj_2_id), "Bravo")


class TestEveEntity_CategoryChecks(TestCase):
    def test_all(self):
        alliance = EveEntityAllianceFactory()
        character = EveEntityCharacterFactory()
        constellation = EveEntity(category=EveEntity.CATEGORY_CONSTELLATION)
        corporation = EveEntityCorporationFactory()
        faction = EveEntity(category=EveEntity.CATEGORY_FACTION)
        inventory_type = EveEntity(category=EveEntity.CATEGORY_INVENTORY_TYPE)
        region = EveEntity(category=EveEntity.CATEGORY_REGION)
        solar_system = EveEntity(category=EveEntity.CATEGORY_SOLAR_SYSTEM)
        station = EveEntity(category=EveEntity.CATEGORY_STATION)
        unresolved = EveEntityUnresolvedFactory()
        all_entities = [
            alliance,
            character,
            constellation,
            corporation,
            faction,
            inventory_type,
            region,
            solar_system,
            station,
            unresolved,
        ]

        class Case(NamedTuple):
            name: str
            obj: object
            prop_name: str = ""

        cases = [
            Case("alliance", alliance),
            Case("character", character),
            Case("constellation", constellation),
            Case("corporation", corporation),
            Case("faction", faction),
            Case("inventory_type", inventory_type, "is_type"),
            Case("region", region),
            Case("solar_system", solar_system),
            Case("station", station),
        ]

        for tc in cases:
            with self.subTest(name=tc.name):
                prop_name = tc.prop_name if tc.prop_name else f"is_{tc.name}"
                self.assertTrue(getattr(tc.obj, prop_name))
                for obj in [o for o in all_entities if o != tc.obj]:
                    self.assertFalse(getattr(obj, prop_name))


class TestEveEntityManagerFetchEntitiesByName(TestCase):
    @pook.on
    def test_can_entities_by_name_from_esi(self):
        # given
        character_id = 1001
        character_name = "Alpha"
        alliance_id = 1002
        alliance_name = "Bravo"
        pook.post(
            make_esi_url("universe/ids"),
            reply=200,
            response_json={
                "agents": [],
                "alliances": [{"id": alliance_id, "name": alliance_name}],
                "characters": [{"id": character_id, "name": character_name}],
                "constellations": [],
                "corporations": [],
                "factions": [],
                "inventory_types": [],
                "regions": [],
                "stations": [],
                "systems": [],
            },
        )
        # when
        result: QuerySet[EveEntity] = EveEntity.objects.fetch_by_names_esi(
            [character_name, alliance_name]
        )

        # then
        self.assertSetEqual(
            queryset_pks(result),
            queryset_pks(EveEntity.objects.filter(id__in=[character_id, alliance_id])),
        )

    # FIXME: Temporary commented out
    # def test_should_make_multiple_esi_request_when_fetching_large_number_of_entities(
    #     self,
    # ):
    #     # given
    #     def my_endpoint(names):
    #         characters = [
    #             {"id": int(name.split("_")[1]), "name": name} for name in names
    #         ]
    #         data = {"characters": characters}
    #         return BravadoOperationStub(data)

    #     mock_esi.client.Universe.post_universe_ids.side_effect = my_endpoint
    #     names = [f"dummy_{num + 1001}" for num in range(600)]
    #     # when
    #     result = EveEntity.objects.fetch_by_names_esi(names)
    #     # then
    #     self.assertEqual(mock_esi.client.Universe.post_universe_ids.call_count, 2)
    #     self.assertEqual(len(result), 600)

    # def test_should_fetch_unknown_entities_from_esi_only(self):
    #     # given
    #     mock_esi.client.Universe.post_universe_ids.return_value = BravadoOperationStub(
    #         {
    #             "characters": [
    #                 {"id": 9991, "name": "alpha"},
    #                 {"id": 9992, "name": "bravo"},
    #             ],
    #             "corporations": [
    #                 {"id": 9993, "name": "charlie"},
    #             ],
    #         }
    #     )
    #     EveEntityFactory(
    #         id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
    #     )
    #     # when
    #     result_qs = EveEntity.objects.fetch_by_names_esi(
    #         ["Bruce Wayne", "alpha", "bravo", "charlie"]
    #     )
    #     # then
    #     self.assertTrue(mock_esi.client.Universe.post_universe_ids.called)
    #     _, kwargs = mock_esi.client.Universe.post_universe_ids.call_args
    #     self.assertSetEqual(set(kwargs["names"]), {"alpha", "bravo", "charlie"})
    #     objs: Dict[int, EveEntity] = {obj.id: obj for obj in result_qs}
    #     self.assertSetEqual(set(objs.keys()), {1001, 9991, 9992, 9993})
    #     self.assertEqual(objs[1001].name, "Bruce Wayne")
    #     self.assertTrue(objs[1001].is_character)
    #     self.assertEqual(objs[9991].name, "alpha")
    #     self.assertTrue(objs[9991].is_character)
    #     self.assertEqual(objs[9992].name, "bravo")
    #     self.assertTrue(objs[9992].is_character)
    #     self.assertEqual(objs[9993].name, "charlie")
    #     self.assertTrue(objs[9993].is_corporation)

    # def test_should_fetch_all_names_when_requested(self):
    #     # given
    #     mock_esi.client.Universe.post_universe_ids.return_value = BravadoOperationStub(
    #         {
    #             "characters": [
    #                 {"id": 9991, "name": "alpha"},
    #                 {"id": 1001, "name": "Bruce Wayne"},
    #             ],
    #         }
    #     )
    #     EveEntityFactory(
    #         id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_FACTION
    #     )
    #     # when
    #     result_qs = EveEntity.objects.fetch_by_names_esi(
    #         ["Bruce Wayne", "alpha"], update=True
    #     )
    #     # then
    #     self.assertTrue(mock_esi.client.Universe.post_universe_ids.called)
    #     _, kwargs = mock_esi.client.Universe.post_universe_ids.call_args
    #     self.assertSetEqual(set(kwargs["names"]), {"Bruce Wayne", "alpha"})
    #     objs: Dict[int, EveEntity] = {obj.id: obj for obj in result_qs}
    #     self.assertSetEqual(set(objs.keys()), {1001, 9991})
    #     self.assertEqual(objs[1001].name, "Bruce Wayne")
    #     self.assertTrue(objs[1001].is_character)
    #     self.assertEqual(objs[9991].name, "alpha")
    #     self.assertTrue(objs[9991].is_character)


class TestEveEntity_ProfileUrl(TestCase):
    def test_should_handle_alliance(self):
        # given
        obj = EveEntityFactory(
            id=3001, name="Wayne Enterprises", category=EveEntity.CATEGORY_ALLIANCE
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://evemaps.dotlan.net/alliance/Wayne_Enterprises"
        )

    def test_should_handle_character(self):
        # given
        obj = EveEntityFactory(
            id=1001, name="Bruce Wayne", category=EveEntity.CATEGORY_CHARACTER
        )
        # when/then
        self.assertEqual(obj.profile_url, "https://evewho.com/character/1001")

    def test_should_handle_corporation(self):
        # given
        obj = EveEntityFactory(
            id=2001, name="Wayne Technologies", category=EveEntity.CATEGORY_CORPORATION
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://evemaps.dotlan.net/corp/Wayne_Technologies"
        )

    def test_should_handle_faction(self):
        # given
        obj = EveEntityFactory(
            id=99, name="Amarr Empire", category=EveEntity.CATEGORY_FACTION
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://evemaps.dotlan.net/factionwarfare/Amarr_Empire"
        )

    def test_should_handle_inventory_type(self):
        # given
        obj = EveEntityFactory(
            id=603, name="Merlin", category=EveEntity.CATEGORY_INVENTORY_TYPE
        )
        # when/then
        self.assertEqual(
            obj.profile_url, "https://www.kalkoken.org/apps/eveitems/?typeId=603"
        )

    def test_should_handle_solar_system(self):
        # given
        obj = EveEntityFactory(
            id=30004984, name="Abune", category=EveEntity.CATEGORY_SOLAR_SYSTEM
        )
        # when/then
        self.assertEqual(obj.profile_url, "https://evemaps.dotlan.net/system/Abune")

    def test_should_handle_station(self):
        # given
        obj = EveEntityFactory(
            id=60003760,
            name="Jita IV - Moon 4 - Caldari Navy Assembly Plant",
            category=EveEntity.CATEGORY_STATION,
        )
        # when/then
        self.assertEqual(
            obj.profile_url,
            "https://evemaps.dotlan.net/station/Jita_IV_-_Moon_4_-_Caldari_Navy_Assembly_Plant",
        )

    def test_should_return_empty_string_for_undefined_category(self):
        # given
        obj = EveEntityFactory(
            id=99, name="Wayne Technologies", category=EveEntity.CATEGORY_CONSTELLATION
        )
        self.assertEqual(obj.profile_url, "")


class TestEveEntity_BulkResolveIDs(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_should_resolve_and_create_new_objs(self):
        # given
        obj_1_id = 1001
        name_1 = "Alpha"
        category_1 = EveEntity.CATEGORY_CHARACTER
        obj_2_id = 1002
        name_2 = "Bravo"
        category_2 = EveEntity.CATEGORY_ALLIANCE
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category_1, "id": obj_1_id, "name": name_1},
                {"category": category_2, "id": obj_2_id, "name": name_2},
            ],
        )
        # when
        got = EveEntity.objects.bulk_resolve_ids(ids=[obj_1_id, obj_2_id])
        self.assertEqual(got, 2)

        obj = EveEntity.objects.get(id=obj_1_id)
        self.assertEqual(obj.name, name_1)
        self.assertEqual(obj.category, category_1)

        obj = EveEntity.objects.get(id=obj_2_id)
        self.assertEqual(obj.name, name_2)
        self.assertEqual(obj.category, category_2)

    @pook.on
    def test_should_return_zero_when_nothing_to_do(self):
        # when
        got = EveEntity.objects.bulk_resolve_ids(ids=[])
        # then
        self.assertEqual(got, 0)

    @pook.on
    def test_should_create_only_non_existing_entities(self):
        # given
        obj_1 = EveEntityCharacterFactory()
        obj_2_id = 1002
        name_2 = "Bravo"
        category_2 = EveEntity.CATEGORY_ALLIANCE
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category_2, "id": obj_2_id, "name": name_2},
            ],
        )

        # when
        got = EveEntity.objects.bulk_resolve_ids(ids=[obj_1.id, obj_2_id])

        # then
        self.assertEqual(got, 1)

        obj = EveEntity.objects.get(id=obj_1.id)
        self.assertEqual(obj.name, obj_1.name)
        self.assertEqual(obj.category, obj_1.category)

        obj = EveEntity.objects.get(id=obj_2_id)
        self.assertEqual(obj.name, name_2)
        self.assertEqual(obj.category, category_2)

    @pook.on
    def test_entities_without_name_will_be_refetched(self):
        # given
        obj = EveEntityFactory(
            id=1001, category=EveEntity.CATEGORY_CORPORATION, name=""
        )
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": obj.category, "id": obj.id, "name": "Alpha"},
            ],
        )

        # when
        result = EveEntity.objects.bulk_resolve_ids(ids=[obj.id])

        # then
        self.assertEqual(result, 1)

        obj.refresh_from_db()
        self.assertEqual(obj.name, "Alpha")

    @pook.on
    def test_should_resolve_and_create_new_objs_with_old_api(self):
        # given
        obj_1_id = 1001
        name_1 = "Alpha"
        category_1 = EveEntity.CATEGORY_CHARACTER
        obj_2_id = 1002
        name_2 = "Bravo"
        category_2 = EveEntity.CATEGORY_ALLIANCE
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": category_1, "id": obj_1_id, "name": name_1},
                {"category": category_2, "id": obj_2_id, "name": name_2},
            ],
        )
        # when
        got = EveEntity.objects.bulk_create_esi(ids=[obj_1_id, obj_2_id])
        self.assertEqual(got, 2)

        obj = EveEntity.objects.get(id=obj_1_id)
        self.assertEqual(obj.name, name_1)
        self.assertEqual(obj.category, category_1)

        obj = EveEntity.objects.get(id=obj_2_id)
        self.assertEqual(obj.name, name_2)
        self.assertEqual(obj.category, category_2)


class TestEveEntityUpdateFromESIByID(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @pook.on
    def test_should_update_entity(self):
        # given
        obj = EveEntityCharacterFactory()
        name = "Alpha"
        pook.post(
            make_esi_url("universe/names"),
            reply=200,
            response_json=[
                {"category": obj.category, "id": obj.id, "name": name},
            ],
        )
        # when
        got = EveEntity.objects.update_from_esi_by_id(ids=[obj.id])

        # then
        self.assertEqual(got, 1)
        obj.refresh_from_db()
        self.assertEqual(obj.name, name)

    @pook.on
    def test_should_return_0_when_no_id_given(self):
        # when
        got = EveEntity.objects.update_from_esi_by_id(ids=[])

        # then
        self.assertEqual(got, 0)

    @pook.on
    def test_should_ignore_invalid_ids(self):
        # when
        got = EveEntity.objects.update_from_esi_by_id(ids=[1])

        # then
        self.assertEqual(got, 0)

    @pook.on
    def test_should_handle_none(self):
        # when
        result = EveEntity.objects.update_from_esi_by_id(ids=None)

        # then
        self.assertEqual(result, 0)


# -----
