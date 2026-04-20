from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

node_master_columns = Table(
    "node_master_columns",
    Base.metadata,
    Column("node_id", Integer, ForeignKey("process_nodes.id", ondelete="CASCADE"), primary_key=True),
    Column("column_id", Integer, ForeignKey("master_columns.id", ondelete="CASCADE"), primary_key=True),
)


class LayerNode(Base):
    __tablename__ = "layer_nodes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    layer_level = Column(Integer, nullable=False)
    parent_id = Column(Integer, ForeignKey("layer_nodes.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    parent = relationship("LayerNode", remote_side=[id], back_populates="children")
    children = relationship("LayerNode", back_populates="parent", cascade="all, delete-orphan")
    master_tables = relationship("MasterTable", back_populates="layer_node", cascade="all, delete-orphan")


class MasterTable(Base):
    __tablename__ = "master_tables"
    id = Column(Integer, primary_key=True, index=True)
    layer_node_id = Column(Integer, ForeignKey("layer_nodes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    layer_node = relationship("LayerNode", back_populates="master_tables")
    columns = relationship("MasterColumn", back_populates="master_table", cascade="all, delete-orphan", order_by="MasterColumn.display_order")
    records = relationship("MasterRecord", back_populates="master_table", cascade="all, delete-orphan", order_by="MasterRecord.record_index")


class MasterColumn(Base):
    __tablename__ = "master_columns"
    id = Column(Integer, primary_key=True, index=True)
    master_table_id = Column(Integer, ForeignKey("master_tables.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False)
    column_type = Column(String(50), default="String")
    description = Column(Text, default="")
    is_required = Column(Boolean, default=False)
    source_object = Column(String(200), default="")
    source_field = Column(String(200), default="")
    sample_values = Column(Text, default="")
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    master_table = relationship("MasterTable", back_populates="columns")
    nodes = relationship("ProcessNode", secondary=node_master_columns, back_populates="master_columns")


class MasterRecord(Base):
    __tablename__ = "master_records"
    id = Column(Integer, primary_key=True, index=True)
    master_table_id = Column(Integer, ForeignKey("master_tables.id", ondelete="CASCADE"), nullable=False)
    record_index = Column(Integer, default=0)
    data = Column(Text, default="{}")
    source_node_id = Column(Integer, ForeignKey("process_nodes.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    master_table = relationship("MasterTable", back_populates="records")
    source_node = relationship("ProcessNode", foreign_keys=[source_node_id])


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="計画中")
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    nodes = relationship("ProcessNode", back_populates="project", cascade="all, delete-orphan")
    edges = relationship("ProcessEdge", back_populates="project", cascade="all, delete-orphan")


class ProcessNode(Base):
    __tablename__ = "process_nodes"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(200), nullable=False)
    node_type = Column(String(50), default="task")
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    duration_days = Column(Integer, default=1)
    status = Column(String(50), default="未着手")
    description = Column(Text, default="")
    master_table_id = Column(Integer, ForeignKey("master_tables.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    project = relationship("Project", back_populates="nodes")
    master_columns = relationship("MasterColumn", secondary=node_master_columns, back_populates="nodes")
    master_table = relationship("MasterTable", foreign_keys=[master_table_id])


class ProcessEdge(Base):
    __tablename__ = "process_edges"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(Integer, ForeignKey("process_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("process_nodes.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(200), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    project = relationship("Project", back_populates="edges")
    source_node = relationship("ProcessNode", foreign_keys=[source_node_id])
    target_node = relationship("ProcessNode", foreign_keys=[target_node_id])
