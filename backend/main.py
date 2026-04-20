import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload, subqueryload
from contextlib import asynccontextmanager
import os

from backend.database import Base, engine, get_db
from backend.models import LayerNode, MasterTable, MasterColumn, MasterRecord, Project, ProcessNode, ProcessEdge
from backend.schemas import (
    LayerNodeCreate, LayerNodeUpdate, LayerNodeResponse,
    MasterTableCreate, MasterTableUpdate, MasterTableResponse,
    MasterColumnCreate, MasterColumnUpdate, MasterColumnResponse,
    MasterRecordCreate, MasterRecordUpdate, MasterRecordResponse,
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProcessNodeCreate, ProcessNodeUpdate, ProcessNodeResponse,
    ProcessEdgeCreate, ProcessEdgeUpdate, ProcessEdgeResponse,
    DashboardStats, AIAnalysisRequest, AIAnalysisResponse,
    CreateIntegratedTableRequest,
    DuplicateCheckRequest, DuplicateCheckResponse,
)
from backend.seed import seed_data
from backend.ai_analysis import analyze_column_mappings, detect_variations, suggest_integration, match_records_across_tables, check_duplicates_within_table


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    seed_data(db)
    db.close()
    yield


app = FastAPI(title="建設BPM+MDM v2", lifespan=lifespan)


# --- Dashboard ---

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    return DashboardStats(
        total_layer_nodes=db.query(LayerNode).count(),
        total_tables=db.query(MasterTable).count(),
        total_columns=db.query(MasterColumn).count(),
        total_projects=db.query(Project).count(),
        total_process_nodes=db.query(ProcessNode).count(),
        total_records=db.query(MasterRecord).count(),
        layer1_count=db.query(LayerNode).filter(LayerNode.layer_level == 1).count(),
        layer2_count=db.query(LayerNode).filter(LayerNode.layer_level == 2).count(),
        layer3_count=db.query(LayerNode).filter(LayerNode.layer_level == 3).count(),
    )


# --- Layer Nodes ---

@app.get("/api/layers", response_model=list[LayerNodeResponse])
def list_layers(db: Session = Depends(get_db)):
    roots = (
        db.query(LayerNode)
        .filter(LayerNode.parent_id == None)
        .options(
            subqueryload(LayerNode.children)
            .subqueryload(LayerNode.children)
            .subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.columns),
            subqueryload(LayerNode.children)
            .subqueryload(LayerNode.children)
            .subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.records),
            subqueryload(LayerNode.children)
            .subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.columns),
            subqueryload(LayerNode.children)
            .subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.records),
            subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.columns),
            subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.records),
        )
        .all()
    )
    return roots


@app.get("/api/layers/{layer_id}", response_model=LayerNodeResponse)
def get_layer(layer_id: int, db: Session = Depends(get_db)):
    layer = (
        db.query(LayerNode)
        .options(
            subqueryload(LayerNode.children)
            .subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.columns),
            subqueryload(LayerNode.children)
            .subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.records),
            subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.columns),
            subqueryload(LayerNode.master_tables)
            .subqueryload(MasterTable.records),
        )
        .filter(LayerNode.id == layer_id)
        .first()
    )
    if not layer:
        raise HTTPException(404, "Layer not found")
    return layer


@app.post("/api/layers", response_model=LayerNodeResponse)
def create_layer(data: LayerNodeCreate, db: Session = Depends(get_db)):
    layer = LayerNode(**data.model_dump())
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return layer


@app.put("/api/layers/{layer_id}", response_model=LayerNodeResponse)
def update_layer(layer_id: int, data: LayerNodeUpdate, db: Session = Depends(get_db)):
    layer = db.query(LayerNode).get(layer_id)
    if not layer:
        raise HTTPException(404, "Layer not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(layer, k, v)
    db.commit()
    db.refresh(layer)
    return layer


@app.delete("/api/layers/{layer_id}")
def delete_layer(layer_id: int, db: Session = Depends(get_db)):
    layer = db.query(LayerNode).get(layer_id)
    if not layer:
        raise HTTPException(404, "Layer not found")
    db.delete(layer)
    db.commit()
    return {"ok": True}


# --- Master Tables ---

@app.get("/api/tables", response_model=list[MasterTableResponse])
def list_tables(layer_node_id: int = None, db: Session = Depends(get_db)):
    q = db.query(MasterTable).options(joinedload(MasterTable.columns), joinedload(MasterTable.records))
    if layer_node_id:
        q = q.filter(MasterTable.layer_node_id == layer_node_id)
    return q.all()


@app.post("/api/tables", response_model=MasterTableResponse)
def create_table(data: MasterTableCreate, db: Session = Depends(get_db)):
    table = MasterTable(**data.model_dump())
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@app.put("/api/tables/{table_id}", response_model=MasterTableResponse)
def update_table(table_id: int, data: MasterTableUpdate, db: Session = Depends(get_db)):
    table = db.query(MasterTable).get(table_id)
    if not table:
        raise HTTPException(404, "Table not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(table, k, v)
    db.commit()
    db.refresh(table)
    return table


@app.delete("/api/tables/{table_id}")
def delete_table(table_id: int, db: Session = Depends(get_db)):
    table = db.query(MasterTable).get(table_id)
    if not table:
        raise HTTPException(404, "Table not found")
    db.delete(table)
    db.commit()
    return {"ok": True}


# --- Master Columns ---

@app.get("/api/columns", response_model=list[MasterColumnResponse])
def list_columns(table_id: int = None, db: Session = Depends(get_db)):
    q = db.query(MasterColumn)
    if table_id:
        q = q.filter(MasterColumn.master_table_id == table_id)
    return q.order_by(MasterColumn.display_order).all()


@app.post("/api/columns", response_model=MasterColumnResponse)
def create_column(data: MasterColumnCreate, db: Session = Depends(get_db)):
    col = MasterColumn(**data.model_dump())
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@app.put("/api/columns/{col_id}", response_model=MasterColumnResponse)
def update_column(col_id: int, data: MasterColumnUpdate, db: Session = Depends(get_db)):
    col = db.query(MasterColumn).get(col_id)
    if not col:
        raise HTTPException(404, "Column not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(col, k, v)
    db.commit()
    db.refresh(col)
    return col


@app.delete("/api/columns/{col_id}")
def delete_column(col_id: int, db: Session = Depends(get_db)):
    col = db.query(MasterColumn).get(col_id)
    if not col:
        raise HTTPException(404, "Column not found")
    db.delete(col)
    db.commit()
    return {"ok": True}


# --- Master Records ---

@app.get("/api/tables/{table_id}/records", response_model=list[MasterRecordResponse])
def list_records(table_id: int, db: Session = Depends(get_db)):
    return db.query(MasterRecord).filter(MasterRecord.master_table_id == table_id).order_by(MasterRecord.record_index).all()


@app.post("/api/records", response_model=MasterRecordResponse)
def create_record(data: MasterRecordCreate, db: Session = Depends(get_db)):
    max_idx = db.query(MasterRecord).filter(MasterRecord.master_table_id == data.master_table_id).count()
    record = MasterRecord(
        master_table_id=data.master_table_id,
        record_index=max_idx,
        data=json.dumps(data.data, ensure_ascii=False),
        source_node_id=data.source_node_id,
    )
    db.add(record)
    table = db.query(MasterTable).get(data.master_table_id)
    if table:
        table.record_count = max_idx + 1
    db.commit()
    db.refresh(record)
    return record


@app.put("/api/records/{record_id}", response_model=MasterRecordResponse)
def update_record(record_id: int, data: MasterRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, "Record not found")
    if data.data is not None:
        record.data = json.dumps(data.data, ensure_ascii=False)
    db.commit()
    db.refresh(record)
    return record


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(MasterRecord).get(record_id)
    if not record:
        raise HTTPException(404, "Record not found")
    db.delete(record)
    db.commit()
    return {"ok": True}


# --- AI Analysis ---

@app.post("/api/ai/analyze", response_model=AIAnalysisResponse)
def ai_analyze(req: AIAnalysisRequest, db: Session = Depends(get_db)):
    if len(req.table_ids) < 2:
        raise HTTPException(400, "2つ以上のテーブルを選択してください")
    tables = (
        db.query(MasterTable)
        .options(joinedload(MasterTable.columns), joinedload(MasterTable.records))
        .filter(MasterTable.id.in_(req.table_ids))
        .all()
    )
    if len(tables) < 2:
        raise HTTPException(404, "Tables not found")

    mappings = analyze_column_mappings(tables)
    variations = detect_variations(tables)
    suggestions = suggest_integration(tables, mappings, variations)
    record_matches = match_records_across_tables(tables, mappings)

    return AIAnalysisResponse(
        column_mappings=mappings,
        variations=variations,
        integration_suggestions=suggestions,
        record_matches=record_matches,
    )


@app.post("/api/ai/check-duplicates", response_model=DuplicateCheckResponse)
def ai_check_duplicates(req: DuplicateCheckRequest, db: Session = Depends(get_db)):
    table = (
        db.query(MasterTable)
        .options(joinedload(MasterTable.columns), joinedload(MasterTable.records))
        .filter(MasterTable.id == req.table_id)
        .first()
    )
    if not table:
        raise HTTPException(404, "Table not found")
    pairs = check_duplicates_within_table(table, req.threshold)
    return DuplicateCheckResponse(
        table_id=table.id,
        table_name=table.name,
        total_records=len(table.records),
        duplicate_pairs=pairs,
    )


@app.post("/api/ai/create-integrated-table", response_model=MasterTableResponse)
def create_integrated_table(req: CreateIntegratedTableRequest, db: Session = Depends(get_db)):
    if len(req.table_ids) < 2:
        raise HTTPException(400, "2つ以上のテーブルを選択してください")

    tables = (
        db.query(MasterTable)
        .options(joinedload(MasterTable.columns), joinedload(MasterTable.records))
        .filter(MasterTable.id.in_(req.table_ids))
        .all()
    )
    if len(tables) < 2:
        raise HTTPException(404, "Tables not found")

    mappings = analyze_column_mappings(tables)
    record_matches = match_records_across_tables(tables, mappings)

    table_name = req.name or f"統合: {' + '.join(t.name for t in tables)}"
    new_table = MasterTable(
        layer_node_id=req.layer_node_id,
        name=table_name,
        description=f"AIにより{len(tables)}テーブルを統合して生成",
        record_count=0,
    )
    db.add(new_table)
    db.flush()

    all_col_names = []
    col_name_set = set()
    col_type_map = {}
    for t in tables:
        for c in t.columns:
            canonical = c.name
            for m in mappings:
                if m.target_column == c.name and m.target_table == t.name:
                    canonical = m.source_column
                    break
            if canonical not in col_name_set:
                col_name_set.add(canonical)
                all_col_names.append(canonical)
                col_type_map[canonical] = c.column_type

    for i, col_name in enumerate(all_col_names):
        col = MasterColumn(
            master_table_id=new_table.id,
            name=col_name,
            column_type=col_type_map.get(col_name, "String"),
            display_order=i,
        )
        db.add(col)

    used_matches = set()
    record_idx = 0
    for rm in record_matches:
        if rm.similarity < 0.5:
            continue
        key = (rm.source_table, rm.source_record_index, rm.target_table, rm.target_record_index)
        if key in used_matches:
            continue
        used_matches.add(key)
        record = MasterRecord(
            master_table_id=new_table.id,
            record_index=record_idx,
            data=json.dumps(rm.merged_record, ensure_ascii=False),
        )
        db.add(record)
        record_idx += 1

    for t in tables:
        for r in t.records:
            already_merged = any(
                (rm.source_table == t.name and rm.source_record_index == r.record_index and rm.similarity >= 0.5) or
                (rm.target_table == t.name and rm.target_record_index == r.record_index and rm.similarity >= 0.5)
                for rm in record_matches
            )
            if not already_merged:
                r_data = json.loads(r.data) if isinstance(r.data, str) else r.data
                normalized = {}
                for k, v in r_data.items():
                    canonical = k
                    for m in mappings:
                        if m.target_column == k and m.target_table == t.name:
                            canonical = m.source_column
                            break
                    normalized[canonical] = v
                record = MasterRecord(
                    master_table_id=new_table.id,
                    record_index=record_idx,
                    data=json.dumps(normalized, ensure_ascii=False),
                )
                db.add(record)
                record_idx += 1

    new_table.record_count = record_idx
    db.commit()
    db.refresh(new_table)

    return (
        db.query(MasterTable)
        .options(joinedload(MasterTable.columns), joinedload(MasterTable.records))
        .filter(MasterTable.id == new_table.id)
        .first()
    )


# --- Projects ---

@app.get("/api/projects", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return (
        db.query(Project)
        .options(
            joinedload(Project.nodes).joinedload(ProcessNode.master_columns),
            joinedload(Project.nodes).joinedload(ProcessNode.master_table).joinedload(MasterTable.columns),
            joinedload(Project.edges),
        )
        .all()
    )


@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = (
        db.query(Project)
        .options(
            joinedload(Project.nodes).joinedload(ProcessNode.master_columns),
            joinedload(Project.nodes).joinedload(ProcessNode.master_table).joinedload(MasterTable.columns),
            joinedload(Project.edges),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.post("/api/projects", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project


# --- Process Nodes ---

@app.post("/api/nodes", response_model=ProcessNodeResponse)
def create_node(data: ProcessNodeCreate, db: Session = Depends(get_db)):
    node = ProcessNode(**data.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@app.put("/api/nodes/{node_id}", response_model=ProcessNodeResponse)
def update_node(node_id: int, data: ProcessNodeUpdate, db: Session = Depends(get_db)):
    node = db.query(ProcessNode).options(
        joinedload(ProcessNode.master_columns),
        joinedload(ProcessNode.master_table).joinedload(MasterTable.columns),
    ).get(node_id)
    if not node:
        raise HTTPException(404, "Node not found")
    update_data = data.model_dump(exclude_unset=True)
    master_column_ids = update_data.pop("master_column_ids", None)
    master_table_id = update_data.pop("master_table_id", None)
    for k, v in update_data.items():
        setattr(node, k, v)
    if master_column_ids is not None:
        cols = db.query(MasterColumn).filter(MasterColumn.id.in_(master_column_ids)).all()
        node.master_columns = cols
    if master_table_id is not None:
        if master_table_id == 0:
            node.master_table_id = None
        else:
            node.master_table_id = master_table_id
    db.commit()
    node = db.query(ProcessNode).options(
        joinedload(ProcessNode.master_columns),
        joinedload(ProcessNode.master_table).joinedload(MasterTable.columns),
    ).get(node_id)
    return node


@app.get("/api/nodes/{node_id}/records", response_model=list[MasterRecordResponse])
def list_node_records(node_id: int, db: Session = Depends(get_db)):
    return db.query(MasterRecord).filter(MasterRecord.source_node_id == node_id).order_by(MasterRecord.record_index).all()


@app.delete("/api/nodes/{node_id}")
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(ProcessNode).get(node_id)
    if not node:
        raise HTTPException(404, "Node not found")
    db.query(ProcessEdge).filter(
        (ProcessEdge.source_node_id == node_id) | (ProcessEdge.target_node_id == node_id)
    ).delete(synchronize_session=False)
    db.delete(node)
    db.commit()
    return {"ok": True}


# --- Process Edges ---

@app.post("/api/edges", response_model=ProcessEdgeResponse)
def create_edge(data: ProcessEdgeCreate, db: Session = Depends(get_db)):
    edge = ProcessEdge(**data.model_dump())
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return edge


@app.put("/api/edges/{edge_id}", response_model=ProcessEdgeResponse)
def update_edge(edge_id: int, data: ProcessEdgeUpdate, db: Session = Depends(get_db)):
    edge = db.query(ProcessEdge).get(edge_id)
    if not edge:
        raise HTTPException(404, "Edge not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(edge, k, v)
    db.commit()
    db.refresh(edge)
    return edge


@app.delete("/api/edges/{edge_id}")
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(ProcessEdge).get(edge_id)
    if not edge:
        raise HTTPException(404, "Edge not found")
    db.delete(edge)
    db.commit()
    return {"ok": True}


# --- Static files (frontend) ---
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.isdir(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
