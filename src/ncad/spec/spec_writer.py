"""Serialize a spec dict back to a JSON or HOCON file.

Mirrors SpecLoader: dispatches on file extension and wraps leaf-common's easy
persistence. Used to persist generator output and golden specs.
"""

import logging

from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
from leaf_common.persistence.easy.easy_json_persistence import EasyJsonPersistence

logger = logging.getLogger(__name__)

_JSON_EXTENSIONS = (".json",)
_HOCON_EXTENSIONS = (".hocon", ".conf")


class SpecWriter:
    """Writes a spec dict to disk, dispatching on file extension."""

    def dump(self, spec: dict, path: str) -> None:
        """Write ``spec`` to ``path``.

        :param spec: The spec dict to serialize.
        :param path: Destination ``.json`` or ``.hocon``/``.conf`` path.
        :raises ValueError: If the file extension is not a supported format.
        """
        lowered = path.lower()
        if lowered.endswith(_JSON_EXTENSIONS):
            persistence = EasyJsonPersistence()
        elif lowered.endswith(_HOCON_EXTENSIONS):
            persistence = EasyHoconPersistence()
        else:
            raise ValueError(
                f"unsupported spec file extension for {path!r}; "
                f"expected one of {_JSON_EXTENSIONS + _HOCON_EXTENSIONS}"
            )

        logger.debug("writing spec to %s", path)
        persistence.persist(spec, file_reference=path)
