"""Tools for dealing with eve data in XML."""

import re
import unicodedata

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from eveuniverse.constants import EveCategoryId, EveGroupId
from eveuniverse.models import EveEntity, EveType

from . import zkillboard


def eve_link_to_url(link: str) -> str:
    """Convert an eve style link into a normal URL.

    Example: ``showinfo:5//30004984`` => ``"https://evemaps.dotlan.net/system/Abune"``

    Supported variants:
        Alliance, Character, Corporation, Inventory Type, Killmail, Solar System, Station and normal URLs

    Returns:
        Converted URL or an empty string if the link was invalid or not supported
    """
    if is_url(link):
        return link
    showinfo_match = re.match(
        r"showinfo:(?P<type_id>\d+)(\/\/(?P<entity_id>\d+))?", link
    )
    if showinfo_match:
        return _convert_type_link(showinfo_match)
    killreport_match = re.match(
        r"killReport:(?P<killmail_id>\d+):(?P<killmail_hash>\w+)", link
    )
    if killreport_match:
        return _convert_killmail_link(killreport_match)
    return ""


def _convert_type_link(showinfo_match: re.Match) -> str:
    if showinfo_match:
        type_id = int(showinfo_match.group("type_id"))
        eve_type, _ = EveType.objects.get_or_create_esi(id=type_id)
        if eve_type.eve_group.eve_category_id == EveCategoryId.STRUCTURE:
            return ""
        if eve_type.eve_group_id in {
            EveGroupId.ALLIANCE.value,
            EveGroupId.CHARACTER.value,
            EveGroupId.CORPORATION.value,
            EveGroupId.SOLAR_SYSTEM.value,
            EveGroupId.STATION.value,
        }:
            entity_id = showinfo_match.group("entity_id")
            eve_entity, _ = EveEntity.objects.get_or_create_esi(id=entity_id)
            if eve_entity:
                return eve_entity.profile_url
        else:
            return eve_type.profile_url
    return ""


def _convert_killmail_link(killreport_match: re.Match) -> str:
    if killreport_match:
        killmail_id = int(killreport_match.group("killmail_id"))
        return zkillboard.killmail_url(killmail_id)
    return ""


def is_url(url_string: str) -> bool:
    """True if given string is an URL, else False"""
    validate_url = URLValidator()
    try:
        validate_url(url_string)
    except ValidationError:
        return False
    return True


def remove_loc_tag(xml: str) -> str:
    """Remove all ``loc`` XML tags."""
    xml = xml.replace("<loc>", "")
    return xml.replace("</loc>", "")


def unicode_to_utf8(xml_doc: str) -> str:
    """Convert unicode encodings into UTF-8 characters."""
    try:
        xml_doc = xml_doc.encode("utf-8").decode("unicode-escape")
        xml_doc = unicodedata.normalize("NFKC", xml_doc)
    except ValueError:
        xml_doc = ""
    return xml_doc
