import { useEffect, useState, useCallback, useRef } from 'react'
import ReactFlow, {
  addEdge,
  updateEdge,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import {
  X, Link2, ChevronDown, ChevronRight, Database, Save, Plus,
  Trash2, GripVertical, ArrowRight, Table2, Layers, CheckCircle2,
} from 'lucide-react'

const STATUS_COLORS = {
  '未着手': { bg: 'bg-gray-100', border: 'border-gray-300', text: 'text-gray-700', flow: '#94a3b8' },
  '施工中': { bg: 'bg-blue-50', border: 'border-blue-400', text: 'text-blue-700', flow: '#3b82f6' },
  '完了': { bg: 'bg-green-50', border: 'border-green-400', text: 'text-green-700', flow: '#22c55e' },
}

function CustomNode({ data }) {
  const colors = STATUS_COLORS[data.status] || STATUS_COLORS['未着手']
  const isMilestone = data.nodeType === 'milestone'
  return (
    <>
      <Handle type="target" position={Position.Left}
        style={{ width: 10, height: 10, background: '#64748b', border: '2px solid #fff' }} />
      <div className={`px-4 py-3 rounded-lg border-2 shadow-sm min-w-[160px] ${colors.bg} ${colors.border} ${isMilestone ? 'border-dashed' : ''}`}>
        <div className="flex items-center gap-2 mb-1">
          {isMilestone && <span className="text-amber-500 text-xs">◆</span>}
          <span className={`font-semibold text-sm ${colors.text}`}>{data.label}</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{data.duration_days}日間</span>
          <span className={`px-1.5 py-0.5 rounded ${colors.bg} ${colors.text} font-medium`}>{data.status}</span>
        </div>
        {data.master_table && (
          <div className="mt-2">
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-100 rounded text-xs text-blue-700 border border-blue-200">
              <Database size={9} /> {data.master_table.name}
            </span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Right}
        style={{ width: 10, height: 10, background: '#3b82f6', border: '2px solid #fff' }} />
    </>
  )
}

const nodeTypes = { custom: CustomNode }

const SIDEBAR_ITEMS = [
  { type: 'task', label: 'タスク', icon: '□' },
  { type: 'milestone', label: 'マイルストーン', icon: '◆' },
]

export default function BPMPage() {
  const [projects, setProjects] = useState([])
  const [currentProject, setCurrentProject] = useState(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)
  const [masterData, setMasterData] = useState([])
  const [masterExpanded, setMasterExpanded] = useState({})
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const edgeUpdateSuccessful = useRef(true)
  const [masterFormData, setMasterFormData] = useState({})
  const [nodeRecords, setNodeRecords] = useState([])
  const [savingRecord, setSavingRecord] = useState(false)

  const loadProjects = useCallback(() => {
    fetch('/api/projects').then(r => r.json()).then(data => {
      setProjects(data)
      if (data.length > 0 && !currentProject) setCurrentProject(data[0])
    })
  }, [currentProject])

  useEffect(() => { loadProjects() }, [loadProjects])
  useEffect(() => { fetch('/api/layers').then(r => r.json()).then(setMasterData) }, [])

  const buildNodeData = (n) => ({
    label: n.label,
    nodeType: n.node_type,
    status: n.status,
    duration_days: n.duration_days,
    description: n.description,
    master_columns: n.master_columns || [],
    master_table: n.master_table || null,
    master_table_id: n.master_table_id || null,
  })

  useEffect(() => {
    if (!currentProject) return
    const flowNodes = currentProject.nodes.map(n => ({
      id: String(n.id),
      type: 'custom',
      position: { x: n.position_x, y: n.position_y },
      data: buildNodeData(n),
    }))
    const flowEdges = currentProject.edges.map(e => ({
      id: String(e.id),
      source: String(e.source_node_id),
      target: String(e.target_node_id),
      label: e.label || '',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#94a3b8', strokeWidth: 2 },
      animated: true,
      data: { dbId: e.id },
    }))
    setNodes(flowNodes)
    setEdges(flowEdges)
  }, [currentProject, setNodes, setEdges])

  const loadNodeRecords = async (nodeId) => {
    const resp = await fetch(`/api/nodes/${nodeId}/records`)
    if (resp.ok) {
      const data = await resp.json()
      setNodeRecords(data)
    }
  }

  const onConnect = useCallback(async (params) => {
    if (!currentProject) return
    const resp = await fetch('/api/edges', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: currentProject.id, source_node_id: parseInt(params.source), target_node_id: parseInt(params.target) }),
    })
    const newEdge = await resp.json()
    setEdges(eds => addEdge({
      ...params, id: String(newEdge.id),
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#94a3b8', strokeWidth: 2 },
      animated: true, data: { dbId: newEdge.id },
    }, eds))
  }, [currentProject, setEdges])

  const onEdgeUpdateStart = useCallback(() => { edgeUpdateSuccessful.current = false }, [])

  const onEdgeUpdate = useCallback(async (oldEdge, newConnection) => {
    edgeUpdateSuccessful.current = true
    const dbId = oldEdge.data?.dbId || parseInt(oldEdge.id)
    await fetch(`/api/edges/${dbId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_node_id: parseInt(newConnection.source), target_node_id: parseInt(newConnection.target) }),
    })
    setEdges(els => updateEdge(oldEdge, newConnection, els))
    setSelectedEdge(null)
  }, [setEdges])

  const onEdgeUpdateEnd = useCallback(async (_, edge) => {
    if (!edgeUpdateSuccessful.current) {
      // Edge drag cancelled
    }
    edgeUpdateSuccessful.current = true
  }, [])

  const onNodeDragStop = useCallback(async (_event, node) => {
    await fetch(`/api/nodes/${node.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ position_x: node.position.x, position_y: node.position.y }),
    })
  }, [])

  const onNodeClick = useCallback((_event, node) => {
    setSelectedNode(node)
    setSelectedEdge(null)
    setMasterFormData({})
    if (node.data.master_table_id) {
      loadNodeRecords(parseInt(node.id))
    } else {
      setNodeRecords([])
    }
  }, [])

  const onEdgeClick = useCallback((_event, edge) => {
    setSelectedEdge(edge)
    setSelectedNode(null)
    setEdges(eds => eds.map(e => ({
      ...e,
      style: e.id === edge.id
        ? { stroke: '#f59e0b', strokeWidth: 3 }
        : { stroke: '#94a3b8', strokeWidth: 2 },
    })))
  }, [setEdges])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
    setSelectedEdge(null)
    setEdges(eds => eds.map(e => ({ ...e, style: { stroke: '#94a3b8', strokeWidth: 2 } })))
  }, [setEdges])

  const deleteSelectedEdge = async () => {
    if (!selectedEdge) return
    const dbId = selectedEdge.data?.dbId || parseInt(selectedEdge.id)
    await fetch(`/api/edges/${dbId}`, { method: 'DELETE' })
    setEdges(eds => eds.filter(e => e.id !== selectedEdge.id))
    setSelectedEdge(null)
  }

  const onDragOver = useCallback((event) => { event.preventDefault(); event.dataTransfer.dropEffect = 'move' }, [])

  const onDrop = useCallback(async (event) => {
    event.preventDefault()
    if (!currentProject || !reactFlowInstance) return
    const type = event.dataTransfer.getData('application/reactflow-type')
    if (!type) return
    const position = reactFlowInstance.screenToFlowPosition({ x: event.clientX, y: event.clientY })
    const resp = await fetch('/api/nodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: currentProject.id, label: type === 'milestone' ? '新マイルストーン' : '新タスク', node_type: type, position_x: position.x, position_y: position.y, duration_days: type === 'milestone' ? 1 : 7 }),
    })
    const newNode = await resp.json()
    setNodes(nds => [...nds, { id: String(newNode.id), type: 'custom', position: { x: newNode.position_x, y: newNode.position_y }, data: buildNodeData(newNode) }])
  }, [currentProject, reactFlowInstance, setNodes])

  const updateSelectedNode = async (updates) => {
    if (!selectedNode) return
    const resp = await fetch(`/api/nodes/${selectedNode.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    })
    const updated = await resp.json()
    const newData = buildNodeData(updated)
    setNodes(nds => nds.map(n => n.id === String(updated.id) ? { ...n, data: newData } : n))
    setSelectedNode(prev => ({ ...prev, data: newData }))
  }

  const deleteSelectedNode = async () => {
    if (!selectedNode) return
    await fetch(`/api/nodes/${selectedNode.id}`, { method: 'DELETE' })
    setNodes(nds => nds.filter(n => n.id !== selectedNode.id))
    setEdges(eds => eds.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id))
    setSelectedNode(null)
  }

  const selectMasterTable = async (tableId) => {
    await updateSelectedNode({ master_table_id: tableId })
    setMasterFormData({})
    loadNodeRecords(parseInt(selectedNode.id))
  }

  const unlinkMasterTable = async () => {
    await updateSelectedNode({ master_table_id: 0 })
    setMasterFormData({})
    setNodeRecords([])
  }

  const saveRecordToMaster = async () => {
    if (!selectedNode?.data?.master_table) return
    setSavingRecord(true)
    try {
      const resp = await fetch('/api/records', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          master_table_id: selectedNode.data.master_table.id,
          data: masterFormData,
          source_node_id: parseInt(selectedNode.id),
        }),
      })
      if (resp.ok) {
        setMasterFormData({})
        loadNodeRecords(parseInt(selectedNode.id))
      }
    } finally {
      setSavingRecord(false)
    }
  }

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }

  const getNodeLabel = (nodeId) => {
    const n = nodes.find(n => n.id === nodeId)
    return n?.data?.label || nodeId
  }

  const renderMasterTableSelector = (layers) => {
    if (!layers || layers.length === 0) return null
    const linkedTableId = selectedNode?.data?.master_table_id
    return layers.map(layer => (
      <div key={layer.id}>
        <div className="flex items-center gap-1 cursor-pointer text-gray-600 hover:text-gray-800 py-0.5 font-medium"
          onClick={() => setMasterExpanded(p => ({ ...p, [`l${layer.id}`]: !p[`l${layer.id}`] }))}>
          {masterExpanded[`l${layer.id}`] ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          <Layers size={10} />
          <span className="text-xs">{layer.name}</span>
        </div>
        {masterExpanded[`l${layer.id}`] && (
          <div className="ml-3">
            {layer.master_tables?.map(table => {
              const isLinked = linkedTableId === table.id
              return (
                <div key={table.id}
                  className={`flex items-center gap-1.5 py-1 px-1.5 rounded cursor-pointer text-xs transition-colors ${isLinked ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-500 hover:bg-gray-50'}`}
                  onClick={() => !isLinked && selectMasterTable(table.id)}>
                  <Database size={10} />
                  <span className="truncate">{table.name}</span>
                  {isLinked && <CheckCircle2 size={10} className="text-blue-500 ml-auto flex-shrink-0" />}
                </div>
              )
            })}
            {renderMasterTableSelector(layer.children)}
          </div>
        )}
      </div>
    ))
  }

  const renderColumnInput = (col) => {
    const value = masterFormData[col.name] ?? ''
    const baseClass = "w-full border border-gray-300 rounded px-2 py-1 text-xs focus:border-blue-400 focus:ring-1 focus:ring-blue-200 outline-none"
    const onChange = (v) => setMasterFormData(p => ({ ...p, [col.name]: v }))

    if (col.column_type === 'Integer') {
      return <input type="number" value={value} onChange={e => onChange(e.target.value === '' ? '' : parseInt(e.target.value))} className={baseClass} />
    }
    if (col.column_type === 'Float') {
      return <input type="number" step="0.01" value={value} onChange={e => onChange(e.target.value === '' ? '' : parseFloat(e.target.value))} className={baseClass} />
    }
    if (col.column_type === 'Date') {
      return <input type="date" value={value} onChange={e => onChange(e.target.value)} className={baseClass} />
    }
    if (col.column_type === 'Boolean') {
      return (
        <label className="flex items-center gap-2 text-xs text-gray-600">
          <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} className="rounded text-blue-600" />
          {value ? 'はい' : 'いいえ'}
        </label>
      )
    }
    if (col.column_type === 'Picklist' && col.sample_values) {
      const options = col.sample_values.split(',').map(s => s.trim()).filter(Boolean)
      return (
        <select value={value} onChange={e => onChange(e.target.value)} className={baseClass}>
          <option value="">-- 選択 --</option>
          {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
      )
    }
    if (col.column_type === 'Text') {
      return <textarea value={value} onChange={e => onChange(e.target.value)} className={`${baseClass} min-h-[60px]`} />
    }
    return <input type="text" value={value} onChange={e => onChange(e.target.value)} className={baseClass} placeholder={col.sample_values ? col.sample_values.split(',')[0]?.trim() : ''} />
  }

  const renderMasterDataForm = () => {
    const table = selectedNode?.data?.master_table
    if (!table) return null
    const columns = table.columns || []

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Database size={12} className="text-blue-600" />
            <span className="text-xs font-medium text-blue-700">{table.name}</span>
          </div>
          <button onClick={unlinkMasterTable} className="text-[10px] text-gray-400 hover:text-red-500">リンク解除</button>
        </div>

        <div className="bg-blue-50/50 rounded-lg border border-blue-100 p-2.5 space-y-2">
          <p className="text-[10px] text-blue-600 font-medium flex items-center gap-1"><Plus size={10} /> 新規レコード登録</p>
          {columns.map(col => (
            <div key={col.id}>
              <label className="text-[10px] text-gray-500 mb-0.5 block">
                {col.name}
                {col.is_required && <span className="text-red-500 ml-0.5">*</span>}
                <span className="text-gray-300 ml-1">{col.column_type}</span>
              </label>
              {renderColumnInput(col)}
            </div>
          ))}
          <button
            onClick={saveRecordToMaster}
            disabled={savingRecord}
            className="flex items-center justify-center gap-1 w-full px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-xs font-medium">
            <Save size={12} /> {savingRecord ? '登録中...' : 'マスタに登録'}
          </button>
        </div>

        {nodeRecords.length > 0 && (
          <div>
            <p className="text-[10px] text-gray-500 mb-1">このノードから登録済み ({nodeRecords.length}件)</p>
            <div className="space-y-1 max-h-32 overflow-auto">
              {nodeRecords.map((rec, idx) => {
                const d = typeof rec.data === 'string' ? JSON.parse(rec.data) : rec.data
                const preview = Object.values(d).slice(0, 2).join(' / ')
                return (
                  <div key={rec.id || idx} className="text-[10px] bg-gray-50 rounded px-2 py-1 text-gray-600 border border-gray-100 truncate">
                    #{idx + 1} {preview}
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderSidebarContent = () => {
    if (selectedEdge) {
      return (
        <div className="flex-1 overflow-auto p-3">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-gray-700">接続の詳細</h3>
            <button onClick={() => { setSelectedEdge(null); onPaneClick() }} className="text-gray-400 hover:text-gray-600"><X size={14} /></button>
          </div>
          <div className="space-y-3 text-xs">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-center gap-2 text-amber-700">
                <ArrowRight size={14} />
                <span className="font-medium">接続情報</span>
              </div>
              <div className="mt-2 space-y-2">
                <div>
                  <span className="text-gray-500">接続元:</span>
                  <span className="ml-2 font-medium text-gray-800">{getNodeLabel(selectedEdge.source)}</span>
                </div>
                <div>
                  <span className="text-gray-500">接続先:</span>
                  <span className="ml-2 font-medium text-gray-800">{getNodeLabel(selectedEdge.target)}</span>
                </div>
              </div>
            </div>
            <p className="text-gray-500">接続線の端をドラッグして接続先を変更できます。</p>
            <button onClick={deleteSelectedEdge}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-xs w-full justify-center">
              <Trash2 size={12} /> 接続を削除
            </button>
          </div>
        </div>
      )
    }

    if (selectedNode) {
      return (
        <div className="flex-1 overflow-auto p-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-gray-700">ノード詳細</h3>
            <button onClick={() => setSelectedNode(null)} className="text-gray-400 hover:text-gray-600"><X size={14} /></button>
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-gray-500 mb-1">名前</label>
              <input value={selectedNode.data.label}
                onChange={e => { const v = e.target.value; setSelectedNode(p => ({ ...p, data: { ...p.data, label: v } })); setNodes(nds => nds.map(n => n.id === selectedNode.id ? { ...n, data: { ...n.data, label: v } } : n)) }}
                onBlur={e => updateSelectedNode({ label: e.target.value })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">日数</label>
              <input type="number" value={selectedNode.data.duration_days}
                onChange={e => { const v = parseInt(e.target.value) || 1; setSelectedNode(p => ({ ...p, data: { ...p.data, duration_days: v } })) }}
                onBlur={e => updateSelectedNode({ duration_days: parseInt(e.target.value) || 1 })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm" min={1} />
            </div>
            <div>
              <label className="block text-gray-500 mb-1">ステータス</label>
              <select value={selectedNode.data.status} onChange={e => updateSelectedNode({ status: e.target.value })}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm">
                <option value="未着手">未着手</option>
                <option value="施工中">施工中</option>
                <option value="完了">完了</option>
              </select>
            </div>

            {selectedNode.data.master_table ? (
              <div>
                <label className="block text-gray-500 mb-2 flex items-center gap-1"><Link2 size={12} /> マスタデータ入力</label>
                {renderMasterDataForm()}
              </div>
            ) : (
              <div>
                <label className="block text-gray-500 mb-2 flex items-center gap-1"><Link2 size={12} /> マスタテーブル選択</label>
                <p className="text-gray-400 mb-1">紐付けるマスタテーブルを選択</p>
                <div className="space-y-1 max-h-64 overflow-auto border border-gray-200 rounded p-2">
                  {renderMasterTableSelector(masterData)}
                </div>
              </div>
            )}

            <button onClick={deleteSelectedNode}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-xs w-full justify-center">
              <Trash2 size={12} /> ノードを削除
            </button>
          </div>
        </div>
      )
    }

    return null
  }

  return (
    <div className="flex h-full">
      <div className="w-56 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-3 border-b border-gray-200">
          <h3 className="text-sm font-bold text-gray-700 mb-2">プロジェクト</h3>
          <select className="w-full text-sm border border-gray-300 rounded-lg px-2 py-1.5"
            value={currentProject?.id || ''}
            onChange={e => { const p = projects.find(p => p.id === parseInt(e.target.value)); setCurrentProject(p); setSelectedNode(null); setSelectedEdge(null) }}>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        <div className="p-3 border-b border-gray-200">
          <h3 className="text-sm font-bold text-gray-700 mb-2">ノードを追加</h3>
          <p className="text-xs text-gray-400 mb-2">ドラッグ＆ドロップ</p>
          <div className="space-y-2">
            {SIDEBAR_ITEMS.map(item => (
              <div key={item.type}
                className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 cursor-grab hover:bg-gray-100 text-sm"
                onDragStart={e => onDragStart(e, item.type)} draggable>
                <GripVertical size={14} className="text-gray-400" />
                <span>{item.icon}</span>
                <span className="text-gray-700">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        {renderSidebarContent()}

        {!selectedNode && !selectedEdge && (
          <div className="flex-1 p-3 text-xs text-gray-400">
            <p>ノードをクリックで選択</p>
            <p className="mt-1">接続線をクリックで選択・編集</p>
            <p className="mt-1">接続線の端をドラッグで再接続</p>
          </div>
        )}
      </div>

      <div className="flex-1">
        <ReactFlow
          nodes={nodes} edges={edges}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onEdgeUpdate={onEdgeUpdate}
          onEdgeUpdateStart={onEdgeUpdateStart}
          onEdgeUpdateEnd={onEdgeUpdateEnd}
          onNodeDragStop={onNodeDragStop}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          onInit={setReactFlowInstance}
          onDrop={onDrop} onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          className="bg-slate-50"
        >
          <Background color="#e2e8f0" gap={20} />
          <Controls />
          <MiniMap nodeColor={n => STATUS_COLORS[n.data?.status]?.flow || '#94a3b8'} />
        </ReactFlow>
      </div>
    </div>
  )
}
