from pydantic import BaseModel
from typing import List, Dict

class BaseNode(BaseModel):
    id: str
    label: str = "Base"

class INSTANCE:
    BoPhapDien = "BoPhapDien"
    ChuDePhapdien = "ChuDePhapdien"
    DeMucPhapdien = "DeMucPhapdien"
    ChuongPhapDien = "ChuongPhapDien"
    MucPhapDien = "MucPhapDien"
    SourceDieuPhapDien = "SourceDieuPhapDien"
    DieuPhapDien = "DieuPhapDien"
    TaiLieuPhapLuatGoc = "TaiLieuPhapLuatGoc"

class BoPhapDienNode(BaseNode):
    id: str  = "00000000000000000000"
    title: str = "Bộ Pháp Điển"
    label: str = "BoPhapDien"

class ChuDePhapdienNode(BaseNode):
    id: str
    title: str
    parent: str = "00000000000000000000"
    parent_type: str = INSTANCE.BoPhapDien
    label: str = "ChuDePhapdien"

class DeMucPhapdienNode(BaseNode):
    id: str
    title: str
    parent: str
    parent_type: str = INSTANCE.ChuDePhapdien
    label: str = "DeMucPhapdien"

class ChuongPhapDienNode(BaseNode):
    id: str
    title: str
    parent: str
    parent_type: str = INSTANCE.DeMucPhapdien
    references: List[str]
    label: str = "ChuongPhapDien"

class MucPhapDienNode(BaseNode):
    id: str
    title: str
    parent: str
    parent_type: str = INSTANCE.ChuongPhapDien
    label: str = "MucPhapDien"

class SourceDieuPhapDien(BaseModel):
    id: str
    url: str
    location: str
    label: str = "SourceDieuPhapDien"

class DieuPhapDienNode(BaseNode):
    id: str
    title: str
    content: str
    parent: str
    parent_type: str
    references: List[str]
    source: str
    label: str = "DieuPhapDien"

class TaiLieuPhapLuatGocNode(BaseNode):
    id: str
    title: str
    label: str = "TaiLieuPhapLuatGoc"

class Relationship:
    HAS_SECTION = "HAS_SECTION"
    BELONGS_TO = "BELONG_TO"
    RELATE_TO = "RELATE_TO"
    SOURCE_OF = "SOURCE_OF"
    DERIVED_FROM = "DERIVED_FROM"