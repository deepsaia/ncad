"""ncad structural FEA (S7 CAE): the analysis seam from a built solid to a CalculiX deck.

Namespace re-exports only; no logic lives here.
"""

from ncad.fea.analysis_error import AnalysisError
from ncad.fea.analysis_params import AnalysisParamError
from ncad.fea.analysis_spec import AnalysisSpec, AnalysisSpecError
from ncad.fea.face_group_mapper import FaceGroupError, FaceGroupMapper
from ncad.fea.gmsh_mesher import GmshMesher

__all__ = ["AnalysisError", "AnalysisParamError", "AnalysisSpec", "AnalysisSpecError",
           "FaceGroupError", "FaceGroupMapper", "GmshMesher"]
