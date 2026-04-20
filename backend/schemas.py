from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MasterColumnBase(BaseModel):
    name: str
    column_type: str = "String"
    description: str = ""
    is_required: bool = False
    source_object: str = ""
    source_field: str = ""
    sample_values: str = ""
    display_order: int = 0


class MasterColumnCreate(MasterColumnBase):
    master_table_id: int


class MasterColumnUpdate(BaseModel):
    name: Optional[str] = None
    column_type: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    source_object: Optional[str] = None
    source_field: Optional[str] = None
    sample_values: Optional[str] = None
    display_order: Optional[int] = None


class MasterColumnResponse(MasterColumnBase):
    id: int
    master_table_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MasterRecordBase(BaseModel):
    record_index: int = 0
    data: str = "{}"


class MasterRecordCreate(BaseModel):
    master_table_id: int
    data: dict = {}
    source_node_id: Optional[int] = None


class MasterRecordUpdate(BaseModel):
    data: Optional[dict] = None


class MasterRecordResponse(MasterRecordBase):
    id: int
    master_table_id: int
    source_node_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MasterTableBase(BaseModel):
    name: str
    description: str = ""
    record_count: int = 0


class MasterTableCreate(MasterTableBase):
    layer_node_id: int


class MasterTableUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    record_count: Optional[int] = None


class MasterTableResponse(MasterTableBase):
    id: int
    layer_node_id: int
    created_at: datetime
    updated_at: datetime
    columns: list[MasterColumnResponse] = []
    records: list[MasterRecordResponse] = []

    class Config:
        from_attributes = True


class LayerNodeBase(BaseModel):
    name: str
    description: str = ""
    layer_level: int


class LayerNodeCreate(LayerNodeBase):
    parent_id: Optional[int] = None


class LayerNodeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class LayerNodeResponse(LayerNodeBase):
    id: int
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    master_tables: list[MasterTableResponse] = []
    children: list["LayerNodeResponse"] = []

    class Config:
        from_attributes = True


class ProcessNodeBase(BaseModel):
    label: str
    node_type: str = "task"
    position_x: float = 0
    position_y: float = 0
    duration_days: int = 1
    status: str = "未着手"
    description: str = ""


class ProcessNodeCreate(ProcessNodeBase):
    project_id: int
    master_table_id: Optional[int] = None


class ProcessNodeUpdate(BaseModel):
    label: Optional[str] = None
    node_type: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    duration_days: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    master_column_ids: Optional[list[int]] = None
    master_table_id: Optional[int] = None


class MasterTableBrief(BaseModel):
    id: int
    name: str
    description: str = ""
    layer_node_id: int
    columns: list[MasterColumnResponse] = []

    class Config:
        from_attributes = True


class ProcessNodeResponse(ProcessNodeBase):
    id: int
    project_id: int
    master_table_id: Optional[int] = None
    master_table: Optional[MasterTableBrief] = None
    created_at: datetime
    updated_at: datetime
    master_columns: list[MasterColumnResponse] = []

    class Config:
        from_attributes = True


class ProcessEdgeBase(BaseModel):
    source_node_id: int
    target_node_id: int
    label: str = ""


class ProcessEdgeCreate(ProcessEdgeBase):
    project_id: int


class ProcessEdgeUpdate(BaseModel):
    source_node_id: Optional[int] = None
    target_node_id: Optional[int] = None
    label: Optional[str] = None


class ProcessEdgeResponse(ProcessEdgeBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str
    description: str = ""
    status: str = "計画中"
    created_by: str = "system"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    nodes: list[ProcessNodeResponse] = []
    edges: list[ProcessEdgeResponse] = []

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_layer_nodes: int
    total_tables: int
    total_columns: int
    total_projects: int
    total_process_nodes: int
    total_records: int
    layer1_count: int
    layer2_count: int
    layer3_count: int


class AIColumnMapping(BaseModel):
    source_column: str
    source_table: str
    target_column: str
    target_table: str
    confidence: float
    reason: str


class AIVariation(BaseModel):
    column_name: str
    table_name: str
    similar_column: str
    similar_table: str
    variation_type: str
    suggestion: str


class AIIntegrationSuggestion(BaseModel):
    suggestion_type: str
    description: str
    tables_involved: list[str]
    priority: str
    details: str


class AIAnalysisRequest(BaseModel):
    table_ids: list[int]


class RecordFieldComparison(BaseModel):
    source_column: str
    target_column: str
    source_value: str
    target_value: str
    similarity: float
    status: str


class RecordMatch(BaseModel):
    source_table: str
    target_table: str
    source_record_index: int
    target_record_index: int
    source_data: dict
    target_data: dict
    similarity: float
    field_comparisons: list[RecordFieldComparison]
    merged_record: dict = {}


class AIAnalysisResponse(BaseModel):
    column_mappings: list[AIColumnMapping] = []
    variations: list[AIVariation] = []
    integration_suggestions: list[AIIntegrationSuggestion] = []
    record_matches: list[RecordMatch] = []


class CreateIntegratedTableRequest(BaseModel):
    table_ids: list[int]
    layer_node_id: int
    name: str = ""


class DuplicateCheckRequest(BaseModel):
    table_id: int
    threshold: float = 0.6


class DuplicatePair(BaseModel):
    record_a_id: int
    record_b_id: int
    record_a_index: int
    record_b_index: int
    record_a_data: dict
    record_b_data: dict
    overall_similarity: float
    field_comparisons: list[RecordFieldComparison]


class DuplicateCheckResponse(BaseModel):
    table_id: int
    table_name: str
    total_records: int
    duplicate_pairs: list[DuplicatePair]
