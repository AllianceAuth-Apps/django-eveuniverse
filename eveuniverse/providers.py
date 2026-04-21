"""Shared ESI provider for Eve Universe."""

from pathlib import Path

from esi.clients import EsiClientProvider

from . import __version__

spec_file = Path(__file__).parent / "swagger_2025-04-02.json"
esi = EsiClientProvider(
    app_info_text=f"django-eveuniverse v{__version__}", spec_file=spec_file
)
