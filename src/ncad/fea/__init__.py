"""ncad structural FEA (S7 CAE): the analysis seam from a built solid to a CalculiX deck.

Namespace re-exports only; no logic lives here.
"""

from ncad.fea.analysis_document import AnalysisDocument
from ncad.fea.analysis_error import AnalysisError
from ncad.fea.analysis_params import AnalysisParamError
from ncad.fea.analysis_spec import AnalysisSpec, AnalysisSpecError
from ncad.fea.ccx_locator import CcxLocator
from ncad.fea.ccx_runner import CcxRunner
from ncad.fea.deck_writer import DeckWriter
from ncad.fea.face_group_mapper import FaceGroupError, FaceGroupMapper
from ncad.fea.frd_reader import FrdReader
from ncad.fea.gmsh_mesher import GmshMesher

__all__ = ["AnalysisDocument", "AnalysisError", "AnalysisParamError", "AnalysisSpec",
           "AnalysisSpecError", "CcxLocator", "CcxRunner", "DeckWriter", "FaceGroupError",
           "FaceGroupMapper", "FrdReader", "GmshMesher"]
