from typing import NamedTuple
from unittest.mock import patch

import pook
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings

from eveuniverse.constants import EveCategoryId
from eveuniverse.models import (
    EveAncestry,
    EveBloodline,
    EveCategory,
    EveConstellation,
    EveDogmaEffect,
    EveEntity,
    EveRegion,
    EveType,
    EveTypeDogmaAttribute,
    EveTypeDogmaEffect,
    EveUnit,
)
from eveuniverse.models.base import _EsiFieldMapping, determine_effective_sections
from eveuniverse.tests.testdata.factories_2 import (
    BlueprintTypeFactory,
    EveDogmaAttributeFactory,
    EveDogmaEffectFactory,
    EveGraphicFactory,
    EveGroupFactory,
    EveMarketGroupFactory,
    EveTypeFactory,
    SKINTypeFactory,
    make_esi_url,
)

MODELS_PATH = "eveuniverse.models"


class TestEveType(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()

    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @pook.on
    def test_can_create_type_from_esi_without_sections(self):
        # given
        capacity = 150
        description = "The Merlin is the most powerful combat frigate of ..."
        graphic = EveGraphicFactory()
        eg = EveGroupFactory()
        mass = 997000
        mg = EveMarketGroupFactory()
        name = "Merlin"
        packaged_volume = 2500
        portion_size = 1
        radius = 39
        type_id = 603
        volume = 16500
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
        da_value = 5
        de_is_default = True
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": capacity,
                "description": description,
                "dogma_attributes": [
                    {"attribute_id": da.id, "value": da_value},
                ],
                "dogma_effects": [
                    {"effect_id": de.id, "is_default": de_is_default},
                ],
                "graphic_id": graphic.id,
                "group_id": eg.id,
                "market_group_id": mg.id,
                "mass": mass,
                "name": name,
                "packaged_volume": packaged_volume,
                "portion_size": portion_size,
                "published": True,
                "radius": radius,
                "type_id": type_id,
                "volume": volume,
            },
        )

        # when
        obj: EveType
        obj, created = EveType.objects.get_or_create_esi(id=type_id)

        # then
        self.assertTrue(created)
        self.assertEqual(obj.capacity, capacity)
        self.assertEqual(obj.description, description)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_INVENTORY_TYPE)
        self.assertEqual(obj.eve_group, eg)
        self.assertEqual(obj.id, type_id)
        self.assertEqual(obj.mass, mass)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.packaged_volume, packaged_volume)
        self.assertEqual(obj.portion_size, portion_size)
        self.assertEqual(obj.radius, radius)
        self.assertEqual(obj.volume, volume)
        self.assertFalse(obj.dogma_attributes.exists())
        self.assertFalse(obj.dogma_effects.exists())
        self.assertIsNone(obj.eve_graphic)
        self.assertIsNone(obj.eve_market_group)
        self.assertTrue(obj.published)

    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", True)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", True)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @pook.on
    def test_can_create_type_from_esi_with_all_sections(self):
        # given
        capacity = 150
        description = "The Merlin is the most powerful combat frigate of ..."
        graphic = EveGraphicFactory()
        eg = EveGroupFactory()
        mass = 997000
        mg = EveMarketGroupFactory()
        name = "Merlin"
        packaged_volume = 2500
        portion_size = 1
        radius = 39
        type_id = 603
        volume = 16500
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
        da_value = 5
        de_is_default = True
        pook.get(
            make_esi_url(f"universe/types/{type_id}"),
            reply=200,
            response_json={
                "capacity": capacity,
                "description": description,
                "dogma_attributes": [
                    {"attribute_id": da.id, "value": da_value},
                ],
                "dogma_effects": [
                    {"effect_id": de.id, "is_default": de_is_default},
                ],
                "graphic_id": graphic.id,
                "group_id": eg.id,
                "market_group_id": mg.id,
                "mass": mass,
                "name": name,
                "packaged_volume": packaged_volume,
                "portion_size": portion_size,
                "published": True,
                "radius": radius,
                "type_id": type_id,
                "volume": volume,
            },
        )

        # when
        obj: EveType
        obj, created = EveType.objects.get_or_create_esi(id=type_id)

        # then
        self.assertEqual(obj.capacity, capacity)
        self.assertEqual(obj.description, description)
        self.assertEqual(obj.eve_entity_category(), EveEntity.CATEGORY_INVENTORY_TYPE)
        self.assertEqual(obj.eve_graphic, graphic)
        self.assertEqual(obj.eve_group, eg)
        self.assertEqual(obj.eve_market_group, mg)
        self.assertEqual(obj.id, type_id)
        self.assertEqual(obj.mass, mass)
        self.assertEqual(obj.name, name)
        self.assertEqual(obj.packaged_volume, packaged_volume)
        self.assertEqual(obj.portion_size, portion_size)
        self.assertEqual(obj.radius, radius)
        self.assertEqual(obj.volume, volume)
        self.assertTrue(created)
        self.assertTrue(obj.published)

        etda: EveTypeDogmaAttribute = obj.dogma_attributes.first()
        self.assertEqual(etda.eve_dogma_attribute, da)
        self.assertEqual(etda.value, da_value)

        etde: EveTypeDogmaEffect = obj.dogma_effects.first()
        self.assertEqual(etde.eve_dogma_effect, de)
        self.assertIs(etde.is_default, de_is_default)

    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", True)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @pook.on
    def test_can_create_type_from_esi_with_market_groups(self):
        # given
        graphic = EveGraphicFactory()
        eg = EveGroupFactory()
        mg = EveMarketGroupFactory()
        type_id = 603
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
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
                "graphic_id": graphic.id,
                "group_id": eg.id,
                "market_group_id": mg.id,
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
        obj: EveType
        obj, created = EveType.objects.get_or_create_esi(id=type_id)

        # then
        self.assertTrue(created)
        self.assertIsNone(obj.eve_graphic)
        self.assertEqual(obj.eve_group, eg)
        self.assertIsNone(obj.eve_market_group)
        self.assertEqual(obj.id, type_id)
        self.assertTrue(
            obj.dogma_attributes.filter(eve_dogma_attribute_id=da.id).exists()
        )
        self.assertTrue(obj.dogma_effects.filter(eve_dogma_effect_id=de.id).exists())

    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @pook.on
    def test_when_disabled_can_create_type_from_esi_excluding_dogmas(self):
        # given
        graphic = EveGraphicFactory()
        eg = EveGroupFactory()
        mg = EveMarketGroupFactory()
        type_id = 603
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
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
                "graphic_id": graphic.id,
                "group_id": eg.id,
                "market_group_id": mg.id,
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
        obj: EveType
        obj, created = EveType.objects.get_or_create_esi(id=type_id)

        # then
        self.assertTrue(created)
        self.assertIsNone(obj.eve_graphic)
        self.assertEqual(obj.eve_group, eg)
        self.assertEqual(obj.eve_market_group, mg)
        self.assertEqual(obj.id, type_id)
        self.assertFalse(obj.dogma_attributes.exists())
        self.assertFalse(obj.dogma_effects.exists())

    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @pook.on
    def test_can_create_type_from_esi_including_dogmas_when_disabled_1(self):
        # given
        graphic = EveGraphicFactory()
        eg = EveGroupFactory()
        mg = EveMarketGroupFactory()
        type_id = 603
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
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
                "graphic_id": graphic.id,
                "group_id": eg.id,
                "market_group_id": mg.id,
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
        obj: EveType
        obj, created = EveType.objects.get_or_create_esi(
            id=type_id, enabled_sections=[EveType.LOAD_DOGMAS]
        )

        # then
        self.assertTrue(created)
        self.assertIsNone(obj.eve_graphic)
        self.assertEqual(obj.eve_group, eg)
        self.assertIsNone(obj.eve_market_group)
        self.assertEqual(obj.id, type_id)
        self.assertTrue(
            obj.dogma_attributes.filter(eve_dogma_attribute_id=da.id).exists()
        )
        self.assertTrue(obj.dogma_effects.filter(eve_dogma_effect_id=de.id).exists())

    @override_settings(
        CELERY_ALWAYS_EAGER=True, CELERY_EAGER_PROPAGATES_EXCEPTIONS=True
    )
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
    @pook.on
    def test_can_create_type_from_esi_including_children_as_task(self):
        # given
        graphic = EveGraphicFactory()
        eg = EveGroupFactory()
        mg = EveMarketGroupFactory()
        type_id = 603
        da = EveDogmaAttributeFactory()
        de = EveDogmaEffectFactory()
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
                "graphic_id": graphic.id,
                "group_id": eg.id,
                "market_group_id": mg.id,
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
        obj: EveType
        obj, created = EveType.objects.get_or_create_esi(
            id=type_id, wait_for_children=False, enabled_sections=[EveType.LOAD_DOGMAS]
        )

        # then
        self.assertTrue(created)
        self.assertIsNone(obj.eve_graphic)
        self.assertEqual(obj.eve_group, eg)
        self.assertIsNone(obj.eve_market_group)
        self.assertEqual(obj.id, type_id)
        self.assertTrue(
            obj.dogma_attributes.filter(eve_dogma_attribute_id=da.id).exists()
        )
        self.assertTrue(obj.dogma_effects.filter(eve_dogma_effect_id=de.id).exists())


@patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False)
@patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False)
class TestEveTypeURLs(TestCase):
    def test_can_create_render_url(self):
        eve_type = EveTypeFactory(id=603)
        got = eve_type.render_url(256)
        self.assertEqual(got, "https://images.evetech.net/types/603/render?size=256")

    def test_can_create_profile_url(self):
        eve_type = EveTypeFactory(id=603)
        got = eve_type.profile_url
        self.assertEqual(got, "https://www.kalkoken.org/apps/eveitems/?typeId=603")

    def test_can_create_icon_url_1(self):
        """icon from regular type, automatically detected"""

        eve_type = EveTypeFactory(id=603)
        got = eve_type.icon_url(256)
        self.assertEqual(got, "https://images.evetech.net/types/603/icon?size=256")

    def test_can_create_icon_url_2(self):
        """icon from blueprint type, automatically detected"""

        eve_type = BlueprintTypeFactory(id=950)
        got = eve_type.icon_url(256)
        self.assertEqual(got, "https://images.evetech.net/types/950/bp?size=256")

    def test_can_create_icon_url_3(self):
        """icon from regular type, preset as blueprint"""

        eve_type = EveTypeFactory(id=603)
        got = eve_type.icon_url(size=256, is_blueprint=True)
        self.assertEqual(got, "https://images.evetech.net/types/603/bp?size=256")

    def test_can_create_icon_url_3a(self):
        """icon from regular type, preset as blueprint"""

        eve_type = EveTypeFactory(id=603)
        got = eve_type.icon_url(size=256, category_id=EveCategoryId.BLUEPRINT)
        self.assertEqual(got, "https://images.evetech.net/types/603/bp?size=256")

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5(self):
        """when called for SKIN type, will return dummy SKIN URL with requested size"""

        eve_type = SKINTypeFactory(id=34599)
        got = eve_type.icon_url(size=64)
        self.assertIn("skin_generic_64.png", got)

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5a(self):
        """when called for SKIN type, will return dummy SKIN URL with requested size"""

        eve_type = SKINTypeFactory(id=34599)
        got = eve_type.icon_url(size=32)
        self.assertIn("skin_generic_32.png", got)

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5b(self):
        """when called for SKIN type, will return dummy SKIN URL with requested size"""

        eve_type = SKINTypeFactory(id=34599)
        got = eve_type.icon_url(size=128)
        self.assertIn("skin_generic_128.png", got)

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_5c(self):
        """when called for SKIN type and size is invalid, then raise exception"""

        eve_type = SKINTypeFactory(id=34599)

        with self.assertRaises(ValueError):
            eve_type.icon_url(size=512)

        with self.assertRaises(ValueError):
            eve_type.icon_url(size=1024)

        with self.assertRaises(ValueError):
            eve_type.icon_url(size=31)

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_6(self):
        """when called for non SKIN type and SKIN is forced, then return SKIN URL"""

        eve_type = BlueprintTypeFactory(id=950)
        got = eve_type.icon_url(size=128, category_id=EveCategoryId.SKIN)
        self.assertIn("skin_generic_128.png", got)

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", False)
    def test_can_create_icon_url_7(self):
        """when called for SKIN type and regular is forced, then return regular URL"""

        eve_type, _ = EveType.objects.get_or_create_esi(id=34599)

        self.assertEqual(
            eve_type.icon_url(size=256, category_id=EveCategoryId.STRUCTURE),
            "https://images.evetech.net/types/34599/icon?size=256",
        )

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", True)
    def test_can_create_icon_url_8(self):
        """
        when called for SKIN type and eveskinserver is enabled,
        then return corresponding eveskinserver URL
        """

        eve_type = SKINTypeFactory(id=34599)
        got = eve_type.icon_url(size=256)
        self.assertEqual(
            got, "https://eveskinserver.kalkoken.net/skin/34599/icon?size=256"
        )

    @patch(MODELS_PATH + ".universe_1.EVEUNIVERSE_USE_EVESKINSERVER", True)
    def test_can_create_icon_url_9(self):
        """can use variants"""

        class Case(NamedTuple):
            name: str
            variant: EveType.IconVariant
            want: str

        cases = [
            Case(
                "regular",
                EveType.IconVariant.REGULAR,
                "https://images.evetech.net/types/603/icon?size=256",
            ),
            Case(
                "regular",
                EveType.IconVariant.BPO,
                "https://images.evetech.net/types/603/bp?size=256",
            ),
            Case(
                "regular",
                EveType.IconVariant.BPC,
                "https://images.evetech.net/types/603/bpc?size=256",
            ),
        ]

        for tc in cases:
            with self.subTest(name=tc.name):
                eve_type = EveTypeFactory(id=603)
                got = eve_type.icon_url(size=256, variant=tc.variant)
                self.assertEqual(got, tc.want)


class TestEveUnit(TestCase):
    def test_get_object(self):
        obj = EveUnit.objects.get(id=10)
        self.assertEqual(obj.id, 10)
        self.assertEqual(obj.name, "Speed")


class TestEsiMapping(TestCase):
    maxDiff = None

    def test_single_pk(self):
        mapping = EveCategory._esi_field_mappings()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["id"],
            _EsiFieldMapping(
                esi_name="category_id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["name"],
            _EsiFieldMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["published"],
            _EsiFieldMapping(
                esi_name="published",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )

    def test_with_fk(self):
        mapping = EveConstellation._esi_field_mappings()
        self.assertEqual(len(mapping.keys()), 6)
        self.assertEqual(
            mapping["id"],
            _EsiFieldMapping(
                esi_name="constellation_id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["name"],
            _EsiFieldMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["eve_region"],
            _EsiFieldMapping(
                esi_name="region_id",
                is_optional=False,
                is_pk=False,
                is_fk=True,
                related_model=EveRegion,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_x"],
            _EsiFieldMapping(
                esi_name=("position", "x"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_y"],
            _EsiFieldMapping(
                esi_name=("position", "y"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["position_z"],
            _EsiFieldMapping(
                esi_name=("position", "z"),
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )

    def test_optional_fields(self):
        mapping = EveAncestry._esi_field_mappings()
        self.assertEqual(len(mapping.keys()), 6)
        self.assertEqual(
            mapping["id"],
            _EsiFieldMapping(
                esi_name="id",
                is_optional=False,
                is_pk=True,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["name"],
            _EsiFieldMapping(
                esi_name="name",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["eve_bloodline"],
            _EsiFieldMapping(
                esi_name="bloodline_id",
                is_optional=False,
                is_pk=False,
                is_fk=True,
                related_model=EveBloodline,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["description"],
            _EsiFieldMapping(
                esi_name="description",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["icon_id"],
            _EsiFieldMapping(
                esi_name="icon_id",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["short_description"],
            _EsiFieldMapping(
                esi_name="short_description",
                is_optional=True,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=True,
                create_related=True,
            ),
        )

    def test_inline_model(self):
        mapping = EveTypeDogmaEffect._esi_field_mappings()
        self.assertEqual(len(mapping.keys()), 3)
        self.assertEqual(
            mapping["eve_type"],
            _EsiFieldMapping(
                esi_name="eve_type",
                is_optional=False,
                is_pk=True,
                is_fk=True,
                related_model=EveType,
                is_parent_fk=True,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["eve_dogma_effect"],
            _EsiFieldMapping(
                esi_name="effect_id",
                is_optional=False,
                is_pk=True,
                is_fk=True,
                related_model=EveDogmaEffect,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )
        self.assertEqual(
            mapping["is_default"],
            _EsiFieldMapping(
                esi_name="is_default",
                is_optional=False,
                is_pk=False,
                is_fk=False,
                related_model=None,
                is_parent_fk=False,
                is_charfield=False,
                create_related=True,
            ),
        )

    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", True)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", True)
    @patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", True)
    def test_EveType_mapping(self):
        mapping = EveType._esi_field_mappings()
        self.assertSetEqual(
            set(mapping.keys()),
            {
                "id",
                "name",
                "description",
                "capacity",
                "eve_group",
                "eve_graphic",
                "icon_id",
                "eve_market_group",
                "mass",
                "packaged_volume",
                "portion_size",
                "radius",
                "published",
                "volume",
            },
        )


class TestDetermineEnabledSections(TestCase):
    def test_should_return_empty_1(self):
        # when
        with patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False
        ), patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = determine_effective_sections()
        # then
        self.assertSetEqual(result, set())

    def test_should_return_empty_2(self):
        # when
        with patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", False
        ), patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = determine_effective_sections(None)
        # then
        self.assertSetEqual(result, set())

    def test_should_return_global_section(self):
        # when
        with patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", True
        ), patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = determine_effective_sections()
        # then
        self.assertSetEqual(result, {EveType.Section.DOGMAS})

    def test_should_combine_global_and_local_sections(self):
        # when
        with patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_ASTEROID_BELTS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_DOGMAS", True
        ), patch(MODELS_PATH + ".base.EVEUNIVERSE_LOAD_GRAPHICS", False), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MARKET_GROUPS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_MOONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_PLANETS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARGATES", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STARS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_STATIONS", False
        ), patch(
            MODELS_PATH + ".base.EVEUNIVERSE_LOAD_TYPE_MATERIALS", False
        ):
            result = determine_effective_sections(["type_materials"])
        # then
        self.assertSetEqual(
            result, {EveType.Section.DOGMAS, EveType.Section.TYPE_MATERIALS}
        )


# --
# --
