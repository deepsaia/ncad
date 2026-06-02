"""Load a building spec from a JSON or HOCON file into a plain dict.

Wraps leaf-common's easy persistence (which returns plain dicts), so the spec layer
stays consistent with the agent layer's ecosystem. HOCON is the intended authoring
format for architecture specs; both formats land on the same dict shape.
"""

import logging

from leaf_common.persistence.easy.easy_hocon_persistence import EasyHoconPersistence
from leaf_common.persistence.easy.easy_json_persistence import EasyJsonPersistence

logger = logging.getLogger(__name__)

_JSON_EXTENSIONS = (".json",)
_HOCON_EXTENSIONS = (".hocon", ".conf")


class SpecLoader:
    """Loads a spec file into a plain dict, dispatching on file extension."""

    def load(self, path: str) -> dict:
        """Load the spec at ``path``.

        :param path: Filesystem path to a ``.json`` or ``.hocon``/``.conf`` file.
        :return: The spec as a plain dict.
        :raises ValueError: If the file extension is not a supported format.
        :raises FileNotFoundError: If the file does not exist.
        """
        lowered = path.lower()
        if lowered.endswith(_JSON_EXTENSIONS):
            persistence = EasyJsonPersistence(must_exist=True)
        elif lowered.endswith(_HOCON_EXTENSIONS):
            persistence = EasyHoconPersistence(must_exist=True)
        else:
            raise ValueError(
                f"unsupported spec file extension for {path!r}; "
                f"expected one of {_JSON_EXTENSIONS + _HOCON_EXTENSIONS}"
            )

        logger.debug("loading spec from %s", path)
        return persistence.restore(file_reference=path)
