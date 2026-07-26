import sys
import types

from django.apps import AppConfig
from django.db import models

from . import __version__


class BitFieldStub(models.BigIntegerField):
    """Stub used to satisfy legacy migration imports for uninstalled packages."""

    def __init__(self, *args, **kwargs):
        # Strip out django-bitfield specific kwargs so standard Django fields don't raise TypeErrors
        kwargs.pop("flags", None)
        kwargs.pop("default", None)
        super().__init__(*args, **kwargs)


class EveuniverseConfig(AppConfig):
    name = "eveuniverse"
    label = "eveuniverse"
    verbose_name = f"Eve Universe v{__version__}"
    default_auto_field = "django.db.models.AutoField"

    # Create stub for BitField to satisfy older migrations
    if "bitfield" not in sys.modules:
        bitfield_pkg = types.ModuleType("bitfield")
        sys.modules["bitfield"] = bitfield_pkg
        bitfield_models = types.ModuleType("bitfield.models")
        bitfield_models.BitField = BitFieldStub
        sys.modules["bitfield.models"] = bitfield_models
        bitfield_pkg.models = bitfield_models
