import { useEffect, useState, useCallback } from 'react'
import {
  ChevronRight, ChevronDown, ChevronLeft, Plus, Trash2, Edit2, Check, X, Save,
  Search, Clock, Database, Table2, Layers, Brain, ArrowRightLeft,
  AlertTriangle, Lightbulb, Loader2, Eye, BarChart3, ListChecks,
  Merge, CheckCircle2, XCircle, MinusCircle, GitMerge,
} from 'lucide-react'

const LAYER_COLORS = {
  1: { bg: 'bg-blue-600', light: 'bg-blue-50', border: 'border-blue-300', text: 'text-blue-700', label: 'L1' },
  2: { bg: 'bg-orange-500', light: 'bg-orange-50', border: 'border-orange-300', text: 'text-orange-700', label: 'L2' },
  3: { bg: 'bg-red-500', light: 'bg-red-50', border: 'border-red-300', text: 'text-red-700', label: 'L3' },
}

const COLUMN_TYPES = ['String', 'Integer', 'Float', 'Date', 'Boolean', 'Picklist', 'Text']

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function LayerBadge({ level }) {
  const c = LAYER_COLORS[level] || LAYER_COLORS[1]
  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-bold ${c.bg} text-white`}>
      {c.label}
    </span>
  )
}

function ConfidenceBadge({ value }) {
  const color = value >= 0.8 ? 'bg-green-100 text-green-700' : value >= 0.6 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>{(value * 100).toFixed(0)}%</span>
}

function SimilarityBar({ value }) {
  const pct = Math.round(value * 100)
  const color = value >= 0.8 ? 'bg-green-500' : value >= 0.6 ? 'bg-yellow-500' : value >= 0.4 ? 'bg-orange-500' : 'bg-red-400'
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-8">{pct}%</span>
    </div>
  )
}

function StatusIcon({ status }) {
  if (status === '一致') return <CheckCircle2 size={13} className="text-green-500" />
  if (status === '近似') return <MinusCircle size={13} className="text-yellow-500" />
  if (status === '類似') return <MinusCircle size={13} className="text-orange-400" />
  return <XCircle size={13} className="text-red-400" />
}

export default function MasterDataPage() {
  const [layers, setLayers] = useState([])
  const [selectedLayer, setSelectedLayer] = useState(null)
  const [selectedTable, setSelectedTable] = useState(null)
  const [selectedTables, setSelectedTables] = useState([])
  const [expanded, setExpanded] = useState({})
  const [search, setSearch] = useState('')
  const [editingCol, setEditingCol] = useState(null)
  const [editData, setEditData] = useState({})
  const [showAddCol, setShowAddCol] = useState(false)
  const [newCol, setNewCol] = useState({ name: '', column_type: 'String', description: '', is_required: false, source_object: '', source_field: '' })
  const [showAddModal, setShowAddModal] = useState(null)
  const [newItem, setNewItem] = useState({ name: '', description: '' })
  const [aiResult, setAiResult] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [activeAiTab, setActiveAiTab] = useState('mapping')
  const [rightTab, setRightTab] = useState('data')
  const [expandedMatch, setExpandedMatch] = useState(null)
  const [integrating, setIntegrating] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [dupLoading, setDupLoading] = useState(false)
  const [dupResult, setDupResult] = useState(null)
  const [dupModalOpen, setDupModalOpen] = useState(false)
  const [dupCurrentIdx, setDupCurrentIdx] = useState(0)
  const [dupEditA, setDupEditA] = useState({})
  const [dupEditB, setDupEditB] = useState({})
  const [dupResolving, setDupResolving] = useState(false)

  const loadLayers = useCallback(() => {
    fetch('/api/layers').then(r => r.json()).then(data => {
      setLayers(data)
      setExpanded(prev => {
        if (Object.keys(prev).length > 0) return prev
        const init = {}
        const autoExpand = (nodes) => {
          for (const n of nodes) {
            init[`layer-${n.id}`] = true
            if (n.children) autoExpand(n.children)
          }
        }
        autoExpand(data)
        return init
      })
    }).catch(() => setLayers([]))
  }, [])

  useEffect(() => { loadLayers() }, [loadLayers])

  const toggle = (key) => setExpanded(prev => ({ ...prev, [key]: !prev[key] }))

  const handleSelectTable = (table, layerNode) => {
    setSelectedTable(table)
    setSelectedLayer(layerNode)
    setEditingCol(null)
    setShowAddCol(false)
    setRightTab('data')
    setDupResult(null)
    setDupModalOpen(false)
  }

  const handleSelectLayer = (layerNode) => {
    setSelectedLayer(layerNode)
    setSelectedTable(null)
  }

  const toggleTableSelection = (table) => {
    setSelectedTables(prev => {
      const exists = prev.find(t => t.id === table.id)
      if (exists) return prev.filter(t => t.id !== table.id)
      return [...prev, table]
    })
  }

  const runAiAnalysis = async () => {
    if (selectedTables.length < 2) return
    setAiLoading(true)
    setAiResult(null)
    try {
      const resp = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table_ids: selectedTables.map(t => t.id) }),
      })
      const data = await resp.json()
      setAiResult(data)
      setActiveAiTab('mapping')
    } catch (e) {
      console.error(e)
    } finally {
      setAiLoading(false)
    }
  }

  const createIntegratedTable = async () => {
    if (selectedTables.length < 2 || !selectedLayer) return
    setIntegrating(true)
    try {
      const resp = await fetch('/api/ai/create-integrated-table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          table_ids: selectedTables.map(t => t.id),
          layer_node_id: selectedLayer.id,
        }),
      })
      if (resp.ok) {
        const newTable = await resp.json()
        loadLayers()
        setSelectedTable(newTable)
        setSelectedTables([])
        setAiResult(null)
        setRightTab('data')
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIntegrating(false)
    }
  }

  const handleDeleteCol = async (colId) => {
    await fetch(`/api/columns/${colId}`, { method: 'DELETE' })
    loadLayers()
    if (selectedTable) {
      setSelectedTable(prev => ({ ...prev, columns: prev.columns?.filter(c => c.id !== colId) }))
    }
  }

  const startEditCol = (col) => {
    setEditingCol(col.id)
    setEditData({ ...col })
  }

  const saveCol = async () => {
    if (!editingCol) return
    await fetch(`/api/columns/${editingCol}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editData),
    })
    setEditingCol(null)
    loadLayers()
    const colsResp = await fetch(`/api/columns?table_id=${selectedTable.id}`)
    const updated = await colsResp.json()
    setSelectedTable(prev => ({ ...prev, columns: updated }))
  }

  const addCol = async () => {
    if (!selectedTable) return
    await fetch('/api/columns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newCol, master_table_id: selectedTable.id, display_order: (selectedTable.columns?.length || 0) }),
    })
    setShowAddCol(false)
    setNewCol({ name: '', column_type: 'String', description: '', is_required: false, source_object: '', source_field: '' })
    loadLayers()
    const colsResp = await fetch(`/api/columns?table_id=${selectedTable.id}`)
    const updated = await colsResp.json()
    setSelectedTable(prev => ({ ...prev, columns: updated }))
  }

  const confirmDeleteTable = (table, e) => {
    if (e) e.stopPropagation()
    setDeleteConfirm({ type: 'table', items: [table] })
  }

  const confirmDeleteSelected = () => {
    if (selectedTables.length === 0) return
    setDeleteConfirm({ type: 'bulk', items: [...selectedTables] })
  }

  const executeDelete = async () => {
    if (!deleteConfirm) return
    for (const item of deleteConfirm.items) {
      await fetch(`/api/tables/${item.id}`, { method: 'DELETE' })
      if (selectedTable?.id === item.id) setSelectedTable(null)
    }
    setSelectedTables(prev => prev.filter(t => !deleteConfirm.items.some(d => d.id === t.id)))
    setDeleteConfirm(null)
    setAiResult(null)
    loadLayers()
  }

  const handleAdd = async () => {
    if (!showAddModal) return
    if (showAddModal.type === 'table') {
      await fetch('/api/tables', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newItem.name, description: newItem.description, layer_node_id: showAddModal.layerNodeId }),
      })
    }
    setShowAddModal(null)
    setNewItem({ name: '', description: '' })
    loadLayers()
  }

  const runDuplicateCheck = async () => {
    if (!selectedTable) return
    setDupLoading(true)
    setDupResult(null)
    try {
      const resp = await fetch('/api/ai/check-duplicates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table_id: selectedTable.id }),
      })
      const data = await resp.json()
      setDupResult(data)
      if (data.duplicate_pairs?.length > 0) {
        setDupCurrentIdx(0)
        setDupEditA({ ...data.duplicate_pairs[0].record_a_data })
        setDupEditB({ ...data.duplicate_pairs[0].record_b_data })
      }
      setDupModalOpen(true)
    } catch (e) {
      console.error(e)
    } finally {
      setDupLoading(false)
    }
  }

  const resolveDuplicate = async (action) => {
    if (!dupResult || dupCurrentIdx >= dupResult.duplicate_pairs.length) return
    const pair = dupResult.duplicate_pairs[dupCurrentIdx]
    setDupResolving(true)
    try {
      if (action === 'keep_a') {
        await fetch(`/api/records/${pair.record_a_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: dupEditA }),
        })
        await fetch(`/api/records/${pair.record_b_id}`, { method: 'DELETE' })
      } else if (action === 'keep_b') {
        await fetch(`/api/records/${pair.record_b_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: dupEditB }),
        })
        await fetch(`/api/records/${pair.record_a_id}`, { method: 'DELETE' })
      } else if (action === 'merge') {
        const merged = { ...dupEditA }
        for (const [k, v] of Object.entries(dupEditB)) {
          if (!merged[k] && v) merged[k] = v
        }
        await fetch(`/api/records/${pair.record_a_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ data: merged }),
        })
        await fetch(`/api/records/${pair.record_b_id}`, { method: 'DELETE' })
      }

      const newPairs = dupResult.duplicate_pairs.filter((_, i) => i !== dupCurrentIdx)
      setDupResult({ ...dupResult, duplicate_pairs: newPairs })

      if (newPairs.length === 0) {
        setDupModalOpen(false)
        loadLayers()
        const tablesResp = await fetch('/api/tables')
        const tables = await tablesResp.json()
        const updated = tables.find(t => t.id === selectedTable.id)
        if (updated) setSelectedTable(updated)
      } else {
        const nextIdx = Math.min(dupCurrentIdx, newPairs.length - 1)
        setDupCurrentIdx(nextIdx)
        setDupEditA({ ...newPairs[nextIdx].record_a_data })
        setDupEditB({ ...newPairs[nextIdx].record_b_data })
      }
    } catch (e) {
      console.error(e)
    } finally {
      setDupResolving(false)
    }
  }

  const goToDupPair = (idx) => {
    if (!dupResult || idx < 0 || idx >= dupResult.duplicate_pairs.length) return
    setDupCurrentIdx(idx)
    setDupEditA({ ...dupResult.duplicate_pairs[idx].record_a_data })
    setDupEditB({ ...dupResult.duplicate_pairs[idx].record_b_data })
  }

  const getAllLayerNodes = (roots) => {
    const result = []
    const collect = (nodes) => {
      for (const n of nodes) {
        result.push(n)
        if (n.children) collect(n.children)
      }
    }
    collect(roots)
    return result
  }

  const allNodes = getAllLayerNodes(layers)
  const filteredNodes = search
    ? allNodes.filter(n =>
        n.name.toLowerCase().includes(search.toLowerCase()) ||
        n.master_tables?.some(t => t.name.toLowerCase().includes(search.toLowerCase()))
      )
    : null

  const getRecords = (table) => {
    if (!table?.records) return []
    return table.records.map(r => {
      const d = typeof r.data === 'string' ? JSON.parse(r.data) : r.data
      return { ...r, parsedData: d }
    }).sort((a, b) => a.record_index - b.record_index)
  }

  const renderTree = (nodes, depth = 0) => {
    if (!nodes || nodes.length === 0) return null
    return nodes.map(node => {
      const key = `layer-${node.id}`
      const isExpanded = expanded[key]
      const color = LAYER_COLORS[node.layer_level] || LAYER_COLORS[1]
      const hasChildren = (node.children && node.children.length > 0) || (node.master_tables && node.master_tables.length > 0)
      const isSelectedLayer = selectedLayer?.id === node.id && !selectedTable

      return (
        <div key={node.id} style={{ paddingLeft: depth > 0 ? 12 : 0 }}>
          <div
            className={`flex items-center gap-1 py-1 px-1.5 rounded cursor-pointer text-xs transition-colors ${
              isSelectedLayer ? `${color.light} ${color.border} border` : 'hover:bg-gray-50'
            }`}
          >
            <button
              onClick={(e) => { e.stopPropagation(); toggle(key) }}
              className="p-0.5 text-gray-400 hover:text-gray-600 flex-shrink-0"
            >
              {hasChildren ? (isExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />) : <span className="w-3" />}
            </button>
            <LayerBadge level={node.layer_level} />
            <span
              className={`font-medium truncate flex-1 ${isSelectedLayer ? color.text : 'text-gray-700'}`}
              onClick={() => { handleSelectLayer(node); if (!isExpanded) toggle(key) }}
            >
              {node.name}
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); setShowAddModal({ type: 'table', layerNodeId: node.id }) }}
              className="p-0.5 text-gray-300 hover:text-blue-600 flex-shrink-0"
              title="テーブル追加"
            >
              <Plus size={11} />
            </button>
          </div>

          {isExpanded && (
            <div style={{ paddingLeft: 16 }}>
              {node.master_tables?.map(table => {
                const isSelected = selectedTable?.id === table.id
                const isChecked = selectedTables.some(t => t.id === table.id)
                return (
                  <div
                    key={table.id}
                    className={`flex items-center gap-1 py-0.5 px-1.5 rounded text-xs cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50 border border-blue-300' : 'hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleTableSelection(table)}
                      className="rounded text-blue-600 flex-shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    />
                    <Table2 size={11} className="text-gray-400 flex-shrink-0" />
                    <span
                      className="truncate flex-1 text-gray-700"
                      onClick={() => handleSelectTable(table, node)}
                    >
                      {table.name}
                    </span>
                    <span className="text-gray-400 text-[10px] flex-shrink-0 whitespace-nowrap">
                      {table.columns?.length || 0}列
                    </span>
                    <button
                      onClick={(e) => confirmDeleteTable(table, e)}
                      className="p-0.5 text-gray-300 hover:text-red-500 flex-shrink-0"
                      title="削除"
                    >
                      <Trash2 size={10} />
                    </button>
                  </div>
                )
              })}
              {renderTree(node.children, depth + 1)}
            </div>
          )}
        </div>
      )
    })
  }

  const renderSearchResults = () => {
    if (!filteredNodes) return null
    return (
      <div className="mt-2 px-1">
        <div className="text-xs text-gray-500 mb-1 px-1">{filteredNodes.length}件のレイヤーが一致</div>
        {filteredNodes.map(node => (
          <div key={node.id} className="mb-2">
            <div
              className="flex items-center gap-1.5 px-2 py-1 cursor-pointer hover:bg-gray-50 rounded text-xs"
              onClick={() => handleSelectLayer(node)}
            >
              <LayerBadge level={node.layer_level} />
              <span className="font-medium text-gray-700">{node.name}</span>
            </div>
            {node.master_tables?.filter(t => t.name.toLowerCase().includes(search.toLowerCase())).map(t => (
              <div
                key={t.id}
                className="ml-4 flex items-center gap-1 px-2 py-0.5 cursor-pointer hover:bg-blue-50 rounded text-xs text-gray-600"
                onClick={() => handleSelectTable(t, node)}
              >
                <Table2 size={10} /> {t.name}
              </div>
            ))}
          </div>
        ))}
      </div>
    )
  }

  const renderPivotedDataView = () => {
    if (!selectedTable) return null
    const columns = selectedTable.columns || []
    const records = getRecords(selectedTable)

    if (records.length === 0) {
      return (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
          <Database size={32} className="mx-auto mb-2 opacity-30" />
          <p className="text-sm">レコードがありません</p>
        </div>
      )
    }

    return (
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-auto max-h-[500px]">
          <table className="w-full text-sm border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-center px-3 py-2.5 font-semibold text-gray-500 bg-gray-50 sticky left-0 z-20 w-[50px] border-r border-gray-200">
                  #
                </th>
                {columns.map(col => (
                  <th key={col.id} className="text-left px-3 py-2.5 font-semibold text-gray-600 bg-gray-50 min-w-[120px] border-r border-gray-100 whitespace-nowrap">
                    <div className="flex items-center gap-1.5">
                      <span>{col.name}</span>
                      <span className="px-1 py-0.5 bg-slate-100 text-slate-500 rounded text-[10px]">{col.column_type}</span>
                      {col.is_required && <span className="text-red-500 text-[10px] font-bold">*</span>}
                    </div>
                  </th>
                ))}
                <th className="text-center px-3 py-2.5 font-semibold text-gray-600 bg-gray-50 min-w-[80px] whitespace-nowrap">
                  登録元
                </th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, idx) => (
                  <tr key={r.id || idx} className={`border-b border-gray-100 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/30'} hover:bg-blue-50/30`}>
                    <td className="px-3 py-2 text-center text-gray-400 font-mono text-xs bg-white sticky left-0 border-r border-gray-200">
                      {idx + 1}
                    </td>
                    {columns.map(col => {
                      const val = r.parsedData[col.name]
                      return (
                        <td key={col.id} className="px-3 py-2 text-gray-700 text-xs border-r border-gray-100">
                          {val !== undefined && val !== null && val !== '' ? String(val) : <span className="text-gray-300">—</span>}
                        </td>
                      )
                    })}
                    <td className="px-3 py-2 text-center">
                      {r.source_node_id ? (
                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded-full text-[10px] font-medium border border-purple-200">
                          BPM
                        </span>
                      ) : (
                        <span className="text-gray-300 text-[10px]">—</span>
                      )}
                    </td>
                  </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const renderColumnTable = () => {
    if (!selectedTable) return null
    const columns = selectedTable.columns || []

    return (
      <div>
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-[180px]">カラム名</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-[90px]">型</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-[160px]">ソースオブジェクト</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-[200px]">ソースフィールド</th>
                <th className="text-left px-4 py-3 font-semibold text-gray-600 w-[140px]">サンプル値</th>
                <th className="text-center px-4 py-3 font-semibold text-gray-600 w-[50px]">必須</th>
                <th className="text-right px-4 py-3 font-semibold text-gray-600 w-[80px]">操作</th>
              </tr>
            </thead>
            <tbody>
              {columns.map((col, idx) => (
                <tr key={col.id} className={`border-b border-gray-100 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} hover:bg-blue-50/30`}>
                  {editingCol === col.id ? (
                    <>
                      <td className="px-4 py-2">
                        <input value={editData.name} onChange={e => setEditData(p => ({ ...p, name: e.target.value }))}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
                      </td>
                      <td className="px-4 py-2">
                        <select value={editData.column_type} onChange={e => setEditData(p => ({ ...p, column_type: e.target.value }))}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm">
                          {COLUMN_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <input value={editData.source_object} onChange={e => setEditData(p => ({ ...p, source_object: e.target.value }))}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
                      </td>
                      <td className="px-4 py-2">
                        <input value={editData.source_field} onChange={e => setEditData(p => ({ ...p, source_field: e.target.value }))}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
                      </td>
                      <td className="px-4 py-2">
                        <input value={editData.sample_values || ''} onChange={e => setEditData(p => ({ ...p, sample_values: e.target.value }))}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm" />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <input type="checkbox" checked={editData.is_required} onChange={e => setEditData(p => ({ ...p, is_required: e.target.checked }))} />
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button onClick={saveCol} className="p-1 text-green-600 hover:bg-green-50 rounded"><Check size={16} /></button>
                        <button onClick={() => setEditingCol(null)} className="p-1 text-gray-400 hover:bg-gray-100 rounded"><X size={16} /></button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="px-4 py-2.5 font-medium text-gray-800">{col.name}</td>
                      <td className="px-4 py-2.5">
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{col.column_type}</span>
                      </td>
                      <td className="px-4 py-2.5 text-gray-600 font-mono text-xs">{col.source_object || '—'}</td>
                      <td className="px-4 py-2.5 text-gray-600 font-mono text-xs">{col.source_field || '—'}</td>
                      <td className="px-4 py-2.5 text-gray-500 text-xs">{col.sample_values || '—'}</td>
                      <td className="px-4 py-2.5 text-center">
                        {col.is_required && <span className="text-red-500 font-bold">*</span>}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        <button onClick={() => startEditCol(col)} className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"><Edit2 size={14} /></button>
                        <button onClick={() => handleDeleteCol(col.id)} className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"><Trash2 size={14} /></button>
                      </td>
                    </>
                  )}
                </tr>
              ))}
              {columns.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">カラムがありません。「カラム追加」から列を定義してください。</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {showAddCol && (
          <div className="mt-4 bg-white rounded-xl border border-blue-200 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">新規カラム追加</h4>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">カラム名 *</label>
                <input value={newCol.name} onChange={e => setNewCol(p => ({ ...p, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">型</label>
                <select value={newCol.column_type} onChange={e => setNewCol(p => ({ ...p, column_type: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                  {COLUMN_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">必須</label>
                <label className="flex items-center gap-2 mt-1">
                  <input type="checkbox" checked={newCol.is_required} onChange={e => setNewCol(p => ({ ...p, is_required: e.target.checked }))} />
                  <span className="text-sm text-gray-600">必須カラム</span>
                </label>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">ソースオブジェクト</label>
                <input value={newCol.source_object} onChange={e => setNewCol(p => ({ ...p, source_object: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">ソースフィールド</label>
                <input value={newCol.source_field} onChange={e => setNewCol(p => ({ ...p, source_field: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
              </div>
              <div className="flex items-end gap-2">
                <button onClick={addCol} disabled={!newCol.name}
                  className="flex items-center gap-1 px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  <Save size={14} /> 保存
                </button>
                <button onClick={() => setShowAddCol(false)}
                  className="px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">キャンセル</button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderTableContent = () => {
    if (!selectedTable) return null

    return (
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-xl font-bold text-gray-800">{selectedTable.name}</h2>
              <LayerBadge level={selectedLayer?.layer_level} />
            </div>
            <p className="text-sm text-gray-500">{selectedTable.description || ''}</p>
            <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
              <span className="flex items-center gap-1"><Database size={11} />{(selectedTable.records?.length || selectedTable.record_count || 0)} レコード</span>
              <span className="flex items-center gap-1"><Clock size={11} />更新: {formatDate(selectedTable.updated_at)}</span>
              <span className="text-gray-400">所属: {selectedLayer?.name}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {rightTab === 'data' && (
              <button
                onClick={runDuplicateCheck}
                disabled={dupLoading || !selectedTable?.records?.length}
                className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                {dupLoading ? <Loader2 size={14} className="animate-spin" /> : <Brain size={14} />}
                {dupLoading ? '解析中...' : 'AI重複チェック'}
              </button>
            )}
            {rightTab === 'columns' && (
              <button
                onClick={() => setShowAddCol(true)}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700"
              >
                <Plus size={14} /> カラム追加
              </button>
            )}
            <button
              onClick={() => confirmDeleteTable(selectedTable)}
              className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 text-xs rounded-lg hover:bg-red-100 border border-red-200"
            >
              <Trash2 size={14} /> このマスタを削除
            </button>
          </div>
        </div>

        <div className="flex gap-1 mb-4 border-b border-gray-200">
          <button
            onClick={() => setRightTab('data')}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
              rightTab === 'data'
                ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <BarChart3 size={13} /> データ一覧
            {selectedTable.records?.length > 0 && (
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                rightTab === 'data' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
              }`}>{selectedTable.records.length}</span>
            )}
          </button>
          <button
            onClick={() => setRightTab('columns')}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium border-b-2 transition-colors ${
              rightTab === 'columns'
                ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <ListChecks size={13} /> カラム定義
            {selectedTable.columns?.length > 0 && (
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                rightTab === 'columns' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-500'
              }`}>{selectedTable.columns.length}</span>
            )}
          </button>
        </div>

        {rightTab === 'data' && renderPivotedDataView()}
        {rightTab === 'columns' && renderColumnTable()}
      </div>
    )
  }

  const renderLayerDetail = () => {
    if (!selectedLayer || selectedTable) return null
    const color = LAYER_COLORS[selectedLayer.layer_level] || LAYER_COLORS[1]
    const tables = selectedLayer.master_tables || []
    const totalCols = tables.reduce((sum, t) => sum + (t.columns?.length || 0), 0)
    const totalRecords = tables.reduce((sum, t) => sum + (t.records?.length || t.record_count || 0), 0)

    return (
      <div>
        <div className="flex items-center gap-3 mb-4">
          <h2 className="text-xl font-bold text-gray-800">{selectedLayer.name}</h2>
          <LayerBadge level={selectedLayer.layer_level} />
        </div>
        <p className="text-sm text-gray-500 mb-4">{selectedLayer.description || ''}</p>

        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className={`${color.light} ${color.border} border rounded-lg p-4`}>
            <p className="text-xs text-gray-500">テーブル数</p>
            <p className={`text-2xl font-bold ${color.text}`}>{tables.length}</p>
          </div>
          <div className={`${color.light} ${color.border} border rounded-lg p-4`}>
            <p className="text-xs text-gray-500">総カラム数</p>
            <p className={`text-2xl font-bold ${color.text}`}>{totalCols}</p>
          </div>
          <div className={`${color.light} ${color.border} border rounded-lg p-4`}>
            <p className="text-xs text-gray-500">総レコード数</p>
            <p className={`text-2xl font-bold ${color.text}`}>{totalRecords.toLocaleString()}</p>
          </div>
        </div>

        {tables.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">テーブル名</th>
                  <th className="text-left px-4 py-3 font-semibold text-gray-600">説明</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600 w-[80px]">カラム数</th>
                  <th className="text-center px-4 py-3 font-semibold text-gray-600 w-[100px]">レコード数</th>
                  <th className="text-right px-4 py-3 font-semibold text-gray-600 w-[80px]">操作</th>
                </tr>
              </thead>
              <tbody>
                {tables.map((table, idx) => (
                  <tr
                    key={table.id}
                    className={`border-b border-gray-100 cursor-pointer ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} hover:bg-blue-50/30`}
                    onClick={() => handleSelectTable(table, selectedLayer)}
                  >
                    <td className="px-4 py-2.5 font-medium text-gray-800">
                      <div className="flex items-center gap-2">
                        <Table2 size={14} className="text-gray-400" />
                        {table.name}
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-gray-500">{table.description || '—'}</td>
                    <td className="px-4 py-2.5 text-center text-gray-600">{table.columns?.length || 0}</td>
                    <td className="px-4 py-2.5 text-center text-gray-600">{(table.records?.length || table.record_count || 0)}</td>
                    <td className="px-4 py-2.5 text-right">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleSelectTable(table, selectedLayer) }}
                        className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Eye size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {selectedLayer.children?.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">子レイヤー</h3>
            <div className="grid grid-cols-2 gap-3">
              {selectedLayer.children.map(child => {
                const cc = LAYER_COLORS[child.layer_level] || LAYER_COLORS[1]
                return (
                  <div
                    key={child.id}
                    className={`${cc.light} ${cc.border} border rounded-lg p-3 cursor-pointer hover:shadow-sm transition-shadow`}
                    onClick={() => handleSelectLayer(child)}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <LayerBadge level={child.layer_level} />
                      <span className="font-medium text-gray-800 text-sm">{child.name}</span>
                    </div>
                    <p className="text-xs text-gray-500">{child.description}</p>
                    <p className="text-xs text-gray-400 mt-1">{child.master_tables?.length || 0} テーブル</p>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderRecordMatchResults = () => {
    const matches = aiResult?.record_matches || []
    if (matches.length === 0) return <p className="text-gray-400 text-sm text-center py-4">レコード照合結果はありません</p>

    return (
      <div className="space-y-2">
        {matches.map((m, i) => {
          const isExpanded = expandedMatch === i
          return (
            <div key={i} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div
                className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpandedMatch(isExpanded ? null : i)}
              >
                <button className="text-gray-400">
                  {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                </button>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="font-medium text-gray-700">{m.source_table}</span>
                    <span className="text-gray-400">#{m.source_record_index + 1}</span>
                    <ArrowRightLeft size={12} className="text-gray-300" />
                    <span className="font-medium text-gray-700">{m.target_table}</span>
                    <span className="text-gray-400">#{m.target_record_index + 1}</span>
                  </div>
                </div>
                <SimilarityBar value={m.similarity} />
              </div>

              {isExpanded && (
                <div className="border-t border-gray-100 px-4 py-3">
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div className="bg-blue-50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-blue-700 mb-2">{m.source_table} #{m.source_record_index + 1}</p>
                      {Object.entries(m.source_data || {}).map(([k, v]) => (
                        <div key={k} className="flex gap-2 text-xs py-0.5">
                          <span className="text-gray-500 min-w-[80px]">{k}:</span>
                          <span className="text-gray-800">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                    <div className="bg-purple-50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-purple-700 mb-2">{m.target_table} #{m.target_record_index + 1}</p>
                      {Object.entries(m.target_data || {}).map(([k, v]) => (
                        <div key={k} className="flex gap-2 text-xs py-0.5">
                          <span className="text-gray-500 min-w-[80px]">{k}:</span>
                          <span className="text-gray-800">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {m.field_comparisons?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-600 mb-2">フィールド比較</p>
                      <div className="space-y-1">
                        {m.field_comparisons.map((fc, fi) => (
                          <div key={fi} className="flex items-center gap-2 text-xs bg-gray-50 rounded px-3 py-1.5">
                            <StatusIcon status={fc.status} />
                            <span className="text-gray-500 min-w-[70px]">{fc.source_column}</span>
                            <span className="text-gray-800 flex-1 truncate">{fc.source_value || '—'}</span>
                            <ArrowRightLeft size={10} className="text-gray-300" />
                            <span className="text-gray-800 flex-1 truncate">{fc.target_value || '—'}</span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                              fc.status === '一致' ? 'bg-green-100 text-green-700' :
                              fc.status === '近似' ? 'bg-yellow-100 text-yellow-700' :
                              fc.status === '類似' ? 'bg-orange-100 text-orange-700' :
                              'bg-red-100 text-red-700'
                            }`}>{fc.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {m.merged_record && Object.keys(m.merged_record).length > 0 && (
                    <div className="mt-3 bg-green-50 rounded-lg p-3">
                      <p className="text-xs font-semibold text-green-700 mb-2">統合レコード（プレビュー）</p>
                      {Object.entries(m.merged_record).map(([k, v]) => (
                        <div key={k} className="flex gap-2 text-xs py-0.5">
                          <span className="text-gray-500 min-w-[80px]">{k}:</span>
                          <span className="text-green-800 font-medium">{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  const renderDuplicateModal = () => {
    const pairs = dupResult?.duplicate_pairs || []
    const pair = pairs[dupCurrentIdx]
    const columns = selectedTable?.columns || []

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50 rounded-t-2xl">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Brain size={18} className="text-purple-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-800">AI重複チェック結果</h3>
                <p className="text-xs text-gray-500">{dupResult?.table_name} ({dupResult?.total_records}件中)</p>
              </div>
            </div>
            {pairs.length > 0 && (
              <div className="flex items-center gap-2">
                <button onClick={() => goToDupPair(dupCurrentIdx - 1)} disabled={dupCurrentIdx <= 0}
                  className="p-1.5 rounded-lg hover:bg-white/80 disabled:opacity-30 text-gray-600"><ChevronLeft size={16} /></button>
                <span className="text-sm font-medium text-gray-700 min-w-[60px] text-center">{dupCurrentIdx + 1} / {pairs.length} 件</span>
                <button onClick={() => goToDupPair(dupCurrentIdx + 1)} disabled={dupCurrentIdx >= pairs.length - 1}
                  className="p-1.5 rounded-lg hover:bg-white/80 disabled:opacity-30 text-gray-600"><ChevronRight size={16} /></button>
              </div>
            )}
            <button onClick={() => setDupModalOpen(false)} className="p-2 hover:bg-white/80 rounded-lg text-gray-500">
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6">
            {pairs.length === 0 ? (
              <div className="text-center py-16">
                <CheckCircle2 size={48} className="mx-auto mb-4 text-green-400" />
                <p className="text-lg font-semibold text-gray-700">重複レコードは検出されませんでした</p>
                <p className="text-sm text-gray-500 mt-1">このテーブルの全レコードはユニークです</p>
              </div>
            ) : pair && (
              <div>
                <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-600">全体類似度:</span>
                  <div className="flex items-center gap-2 flex-1">
                    <div className="flex-1 h-2.5 bg-gray-200 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${pair.overall_similarity >= 0.8 ? 'bg-red-500' : pair.overall_similarity >= 0.6 ? 'bg-yellow-500' : 'bg-orange-500'}`}
                        style={{ width: `${Math.round(pair.overall_similarity * 100)}%` }} />
                    </div>
                    <span className="text-sm font-bold text-gray-700 min-w-[45px]">{Math.round(pair.overall_similarity * 100)}%</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="border border-blue-200 rounded-xl overflow-hidden">
                    <div className="bg-blue-50 px-4 py-2.5 border-b border-blue-200">
                      <span className="text-sm font-bold text-blue-700">レコード A</span>
                      <span className="text-xs text-blue-500 ml-2">#{pair.record_a_index + 1}</span>
                    </div>
                    <div className="p-3 space-y-2">
                      {columns.map(col => {
                        const fc = pair.field_comparisons?.find(f => f.source_column === col.name)
                        const bgColor = fc ? (fc.similarity >= 0.95 ? 'bg-green-50' : fc.similarity >= 0.7 ? 'bg-yellow-50' : fc.similarity >= 0.4 ? 'bg-orange-50' : 'bg-red-50') : ''
                        return (
                          <div key={col.id} className={`rounded-lg px-3 py-2 ${bgColor}`}>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] font-medium text-gray-500">{col.name}</span>
                              {fc && <StatusIcon status={fc.status} />}
                              {fc && <span className="text-[10px] text-gray-400">{Math.round(fc.similarity * 100)}%</span>}
                            </div>
                            <input
                              value={dupEditA[col.name] ?? ''}
                              onChange={e => setDupEditA(p => ({ ...p, [col.name]: e.target.value }))}
                              className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white"
                            />
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="border border-purple-200 rounded-xl overflow-hidden">
                    <div className="bg-purple-50 px-4 py-2.5 border-b border-purple-200">
                      <span className="text-sm font-bold text-purple-700">レコード B</span>
                      <span className="text-xs text-purple-500 ml-2">#{pair.record_b_index + 1}</span>
                    </div>
                    <div className="p-3 space-y-2">
                      {columns.map(col => {
                        const fc = pair.field_comparisons?.find(f => f.source_column === col.name)
                        const bgColor = fc ? (fc.similarity >= 0.95 ? 'bg-green-50' : fc.similarity >= 0.7 ? 'bg-yellow-50' : fc.similarity >= 0.4 ? 'bg-orange-50' : 'bg-red-50') : ''
                        return (
                          <div key={col.id} className={`rounded-lg px-3 py-2 ${bgColor}`}>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] font-medium text-gray-500">{col.name}</span>
                              {fc && <StatusIcon status={fc.status} />}
                              {fc && <span className="text-[10px] text-gray-400">{Math.round(fc.similarity * 100)}%</span>}
                            </div>
                            <input
                              value={dupEditB[col.name] ?? ''}
                              onChange={e => setDupEditB(p => ({ ...p, [col.name]: e.target.value }))}
                              className="w-full border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
                            />
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 pt-2 border-t border-gray-200">
                  <button onClick={() => resolveDuplicate('keep_a')} disabled={dupResolving}
                    className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
                    {dupResolving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Aを残す
                  </button>
                  <button onClick={() => resolveDuplicate('merge')} disabled={dupResolving}
                    className="flex items-center gap-1.5 px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50">
                    {dupResolving ? <Loader2 size={14} className="animate-spin" /> : <GitMerge size={14} />} マージして残す
                  </button>
                  <button onClick={() => resolveDuplicate('keep_both')} disabled={dupResolving}
                    className="flex items-center gap-1.5 px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 border border-gray-300 disabled:opacity-50">
                    両方残す
                  </button>
                  <button onClick={() => resolveDuplicate('keep_b')} disabled={dupResolving}
                    className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50">
                    {dupResolving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Bを残す
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderAiPanel = () => {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-blue-50">
          <div className="flex items-center gap-2">
            <Brain size={18} className="text-purple-600" />
            <h3 className="font-bold text-gray-800 text-sm">AI マスタデータ分析</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">{selectedTables.length}テーブル選択中</span>
            <button
              onClick={runAiAnalysis}
              disabled={selectedTables.length < 2 || aiLoading}
              className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {aiLoading ? <Loader2 size={12} className="animate-spin" /> : <Brain size={12} />}
              {aiLoading ? '分析中...' : 'AI分析実行'}
            </button>
            {aiResult && selectedTables.length >= 2 && selectedLayer && (
              <button
                onClick={createIntegratedTable}
                disabled={integrating}
                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {integrating ? <Loader2 size={12} className="animate-spin" /> : <Merge size={12} />}
                {integrating ? '統合中...' : '統合マスタ作成'}
              </button>
            )}
          </div>
        </div>

        {selectedTables.length > 0 && (
          <div className="px-4 py-2 border-b border-gray-100 bg-gray-50">
            <div className="flex items-center gap-2">
              <div className="flex flex-wrap gap-1 flex-1">
              {selectedTables.map(t => (
                <span
                  key={t.id}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-white border border-gray-200 rounded-full text-xs text-gray-700"
                >
                  <Table2 size={10} /> {t.name}
                  <button onClick={() => toggleTableSelection(t)} className="text-gray-400 hover:text-red-500">
                    <X size={10} />
                  </button>
                </span>
              ))}
              </div>
              <button
                onClick={confirmDeleteSelected}
                className="flex items-center gap-1 px-2.5 py-1 bg-red-50 text-red-600 text-xs rounded-lg hover:bg-red-100 border border-red-200 flex-shrink-0"
                title="選択したテーブルを削除"
              >
                <Trash2 size={12} /> 選択削除
              </button>
            </div>
          </div>
        )}

        {selectedTables.length < 2 && !aiResult && (
          <div className="p-8 text-center text-gray-400 text-sm">
            <Brain size={32} className="mx-auto mb-2 opacity-30" />
            <p>2つ以上のマスタテーブルを選択してAI分析を実行</p>
            <p className="text-xs mt-1">左パネルのチェックボックスでテーブルを選択 → AI分析実行 → 統合マスタ作成</p>
          </div>
        )}

        {aiResult && (
          <div>
            <div className="flex border-b border-gray-200">
              {[
                { key: 'mapping', label: '列マッピング', icon: ArrowRightLeft, count: aiResult.column_mappings?.length },
                { key: 'records', label: 'レコード照合', icon: Database, count: aiResult.record_matches?.length },
                { key: 'variation', label: '表記揺れ', icon: AlertTriangle, count: aiResult.variations?.length },
                { key: 'suggestion', label: '統合サジェスト', icon: Lightbulb, count: aiResult.integration_suggestions?.length },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveAiTab(tab.key)}
                  className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${
                    activeAiTab === tab.key
                      ? 'border-purple-600 text-purple-700 bg-purple-50/50'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <tab.icon size={13} />
                  {tab.label}
                  {tab.count > 0 && (
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                      activeAiTab === tab.key ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            <div className="p-4 max-h-[400px] overflow-auto">
              {activeAiTab === 'mapping' && renderMappingResults()}
              {activeAiTab === 'records' && renderRecordMatchResults()}
              {activeAiTab === 'variation' && renderVariationResults()}
              {activeAiTab === 'suggestion' && renderSuggestionResults()}
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderMappingResults = () => {
    const mappings = aiResult?.column_mappings || []
    if (mappings.length === 0) return <p className="text-gray-400 text-sm text-center py-4">マッピング候補はありません</p>

    return (
      <div className="space-y-2">
        {mappings.map((m, i) => (
          <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium text-gray-800">{m.source_table}</span>
                <span className="text-gray-400">.</span>
                <span className="text-blue-600 font-mono">{m.source_column}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ConfidenceBadge value={m.confidence} />
              <ArrowRightLeft size={14} className="text-gray-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 text-sm">
                <span className="font-medium text-gray-800">{m.target_table}</span>
                <span className="text-gray-400">.</span>
                <span className="text-purple-600 font-mono">{m.target_column}</span>
              </div>
            </div>
            <div className="text-xs text-gray-500 max-w-[200px] truncate" title={m.reason}>{m.reason}</div>
          </div>
        ))}
      </div>
    )
  }

  const renderVariationResults = () => {
    const variations = aiResult?.variations || []
    if (variations.length === 0) return <p className="text-gray-400 text-sm text-center py-4">表記揺れは検出されませんでした</p>

    return (
      <div className="space-y-2">
        {variations.map((v, i) => (
          <div key={i} className="p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={14} className="text-amber-600" />
              <span className="text-xs font-medium text-amber-700 px-1.5 py-0.5 bg-amber-100 rounded">{v.variation_type}</span>
            </div>
            <div className="flex items-center gap-2 text-sm mt-2">
              <span className="font-mono text-amber-800">{v.table_name}.{v.column_name}</span>
              <ArrowRightLeft size={12} className="text-amber-400" />
              <span className="font-mono text-amber-800">{v.similar_table}.{v.similar_column}</span>
            </div>
            <p className="text-xs text-amber-700 mt-1">{v.suggestion}</p>
          </div>
        ))}
      </div>
    )
  }

  const renderSuggestionResults = () => {
    const suggestions = aiResult?.integration_suggestions || []
    if (suggestions.length === 0) return <p className="text-gray-400 text-sm text-center py-4">統合サジェストはありません</p>

    const priorityColors = {
      '高': 'bg-red-100 text-red-700 border-red-200',
      '中': 'bg-yellow-100 text-yellow-700 border-yellow-200',
      '低': 'bg-green-100 text-green-700 border-green-200',
    }

    return (
      <div className="space-y-3">
        {suggestions.map((s, i) => (
          <div key={i} className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb size={16} className="text-blue-500" />
              <span className="font-semibold text-gray-800 text-sm">{s.suggestion_type}</span>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${priorityColors[s.priority] || priorityColors['中']}`}>
                優先度: {s.priority}
              </span>
            </div>
            <p className="text-sm text-gray-700 mb-2">{s.description}</p>
            <div className="flex items-center gap-1 mb-2">
              {s.tables_involved?.map((t, j) => (
                <span key={j} className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">{t}</span>
              ))}
            </div>
            <p className="text-xs text-gray-500">{s.details}</p>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-full">
      {/* Left Panel — Tree */}
      <div className="w-72 border-r border-gray-200 bg-white flex flex-col min-w-[288px]">
        <div className="p-3 border-b border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-bold text-gray-800 flex items-center gap-1.5">
              <Layers size={14} /> マスタデータ階層
            </h2>
          </div>
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="検索..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 border border-gray-200 rounded text-xs focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-auto py-2 px-1">
          {search ? renderSearchResults() : renderTree(layers)}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-gray-50 flex flex-col">
        <div className="flex-1 p-6 overflow-auto">
          {!selectedLayer && !selectedTable ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <Layers size={48} className="mx-auto mb-4 opacity-30" />
                <p>左パネルからレイヤーまたはテーブルを選択してください</p>
                <p className="text-sm mt-1">テーブルを選択するとデータの縦横ピボット表示が確認できます</p>
              </div>
            </div>
          ) : selectedTable ? renderTableContent() : renderLayerDetail()}
        </div>

        {/* AI Panel */}
        <div className="border-t border-gray-200 bg-white">
          {renderAiPanel()}
        </div>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-bold mb-4">テーブルを追加</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">テーブル名</label>
                <input
                  value={newItem.name}
                  onChange={e => setNewItem(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">説明</label>
                <textarea
                  value={newItem.description}
                  onChange={e => setNewItem(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => { setShowAddModal(null); setNewItem({ name: '', description: '' }) }}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                キャンセル
              </button>
              <button
                onClick={handleAdd}
                disabled={!newItem.name}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                追加
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-red-100 rounded-full">
                <AlertTriangle size={20} className="text-red-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-800">マスタデータの削除</h3>
            </div>
            <p className="text-sm text-gray-600 mb-3">
              以下のマスタテーブルを削除しますか？この操作は取り消せません。
            </p>
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 max-h-[200px] overflow-auto">
              {deleteConfirm.items.map(t => (
                <div key={t.id} className="flex items-center gap-2 py-1 text-sm">
                  <Table2 size={14} className="text-red-400 flex-shrink-0" />
                  <span className="font-medium text-gray-800">{t.name}</span>
                  <span className="text-xs text-gray-400">
                    ({t.columns?.length || 0}列 / {t.records?.length || t.record_count || 0}件)
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mb-4">
              テーブル内のすべてのカラム定義とレコードデータも同時に削除されます。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                キャンセル
              </button>
              <button
                onClick={executeDelete}
                className="flex items-center gap-1 px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                <Trash2 size={14} /> 削除する
              </button>
            </div>
          </div>
        </div>
      )}

      {dupModalOpen && renderDuplicateModal()}
    </div>
  )
}
