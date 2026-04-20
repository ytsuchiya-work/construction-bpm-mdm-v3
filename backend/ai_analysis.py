import difflib
import itertools
import json
import re
from backend.models import MasterTable, MasterColumn
from backend.schemas import (
    AIColumnMapping, AIVariation, AIIntegrationSuggestion,
    RecordMatch, RecordFieldComparison,
)

NORMALIZE_MAP = {
    "氏名": ["名前", "名称", "担当者名", "社員名", "作業員名"],
    "名前": ["氏名", "名称", "担当者名"],
    "名称": ["名前", "氏名", "品名", "品目名"],
    "品名": ["名称", "品目名", "資材名", "材料名"],
    "単価": ["価格", "金額", "コスト", "費用", "日額単価", "標準単価"],
    "日額単価": ["単価", "日額", "日当"],
    "連絡先": ["電話番号", "TEL", "電話", "携帯"],
    "住所": ["所在地", "アドレス"],
    "規格": ["仕様", "スペック", "型式", "型番"],
    "型式": ["規格", "型番", "モデル"],
    "数量": ["個数", "在庫数量", "在庫数", "数"],
    "在庫数量": ["数量", "在庫数", "残数"],
    "メーカー": ["製造元", "製造者", "ブランド", "メーカ"],
    "会社名": ["企業名", "社名", "取引先名"],
    "所属": ["部署", "組織", "部門"],
    "経験年数": ["経験", "年数", "キャリア"],
    "評価": ["ランク", "格付", "レーティング"],
}

TYPE_COMPAT = {
    "String": {"String", "Text"},
    "Text": {"String", "Text"},
    "Integer": {"Integer", "Float"},
    "Float": {"Integer", "Float"},
    "Date": {"Date", "DateTime"},
    "DateTime": {"Date", "DateTime"},
    "Boolean": {"Boolean"},
    "Picklist": {"Picklist", "String"},
}

KATAKANA_VARIATIONS = [
    ("メーカー", "メーカ"),
    ("コンピューター", "コンピュータ"),
    ("サーバー", "サーバ"),
    ("マネージャー", "マネージャ"),
    ("エンジニア", "エンジニヤ"),
]

KANJI_VARIATIONS = [
    ("品目", "品名"),
    ("取引先", "協力会社"),
    ("作業員", "人員"),
    ("機材", "資材"),
    ("設備", "重機"),
]


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r'[（）\(\)\s　]', '', s)
    return s


def _similarity(a: str, b: str) -> float:
    na, nb = _normalize(a), _normalize(b)
    if na == nb:
        return 1.0
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    for key, synonyms in NORMALIZE_MAP.items():
        key_n = _normalize(key)
        if (na == key_n and nb in [_normalize(s) for s in synonyms]) or \
           (nb == key_n and na in [_normalize(s) for s in synonyms]):
            return max(ratio, 0.85)
    return ratio


def _value_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a_s, b_s = str(a).strip(), str(b).strip()
    if a_s == b_s:
        return 1.0
    try:
        a_n = float(a_s.replace(",", ""))
        b_n = float(b_s.replace(",", ""))
        if a_n == 0 and b_n == 0:
            return 1.0
        mx = max(abs(a_n), abs(b_n))
        return 1.0 - abs(a_n - b_n) / mx if mx > 0 else 0.0
    except ValueError:
        pass
    return difflib.SequenceMatcher(None, a_s.lower(), b_s.lower()).ratio()


def analyze_column_mappings(tables: list[MasterTable]) -> list[AIColumnMapping]:
    mappings = []
    for i, t1 in enumerate(tables):
        for t2 in tables[i + 1:]:
            for c1 in t1.columns:
                best_score = 0
                best_col = None
                for c2 in t2.columns:
                    score = _similarity(c1.name, c2.name)
                    type_ok = c2.column_type in TYPE_COMPAT.get(c1.column_type, {c1.column_type})
                    if not type_ok:
                        score *= 0.7
                    if score > best_score:
                        best_score = score
                        best_col = c2
                if best_col and best_score >= 0.5:
                    if best_score >= 0.9:
                        reason = "列名が一致または非常に類似しています"
                    elif best_score >= 0.7:
                        reason = "列名が類似しており、同一データを指す可能性があります"
                    else:
                        reason = "列名に部分的な類似性があります"
                    type_match = best_col.column_type in TYPE_COMPAT.get(c1.column_type, {c1.column_type})
                    if not type_match:
                        reason += "（型が異なるため変換が必要）"
                    mappings.append(AIColumnMapping(
                        source_column=c1.name,
                        source_table=t1.name,
                        target_column=best_col.name,
                        target_table=t2.name,
                        confidence=round(best_score, 2),
                        reason=reason,
                    ))
    mappings.sort(key=lambda m: -m.confidence)
    return mappings


def detect_variations(tables: list[MasterTable]) -> list[AIVariation]:
    variations = []
    all_cols = []
    for t in tables:
        for c in t.columns:
            all_cols.append((c.name, t.name, c))

    for i, (name1, tname1, c1) in enumerate(all_cols):
        for name2, tname2, c2 in all_cols[i + 1:]:
            if tname1 == tname2:
                continue
            n1, n2 = _normalize(name1), _normalize(name2)
            if n1 == n2:
                continue

            for long_form, short_form in KATAKANA_VARIATIONS:
                ln, sn = _normalize(long_form), _normalize(short_form)
                if (n1 == ln and n2 == sn) or (n1 == sn and n2 == ln):
                    variations.append(AIVariation(
                        column_name=name1, table_name=tname1,
                        similar_column=name2, similar_table=tname2,
                        variation_type="カタカナ表記揺れ",
                        suggestion=f"「{name1}」と「{name2}」は同じ意味です。統一を推奨します。",
                    ))
                    break

            for v1, v2 in KANJI_VARIATIONS:
                vn1, vn2 = _normalize(v1), _normalize(v2)
                if (n1 == vn1 and n2 == vn2) or (n1 == vn2 and n2 == vn1):
                    variations.append(AIVariation(
                        column_name=name1, table_name=tname1,
                        similar_column=name2, similar_table=tname2,
                        variation_type="同義語",
                        suggestion=f"「{name1}」と「{name2}」は同じ概念を指す可能性があります。",
                    ))
                    break

            sim = _similarity(name1, name2)
            if 0.6 <= sim < 0.95:
                already = any(
                    (v.column_name == name1 and v.similar_column == name2) or
                    (v.column_name == name2 and v.similar_column == name1)
                    for v in variations
                )
                if not already:
                    variations.append(AIVariation(
                        column_name=name1, table_name=tname1,
                        similar_column=name2, similar_table=tname2,
                        variation_type="類似表現",
                        suggestion=f"「{name1}」と「{name2}」は類似した名称です（類似度: {sim:.0%}）。統合の検討を推奨します。",
                    ))

    return variations


def match_records_across_tables(
    tables: list[MasterTable],
    column_mappings: list[AIColumnMapping],
) -> list[RecordMatch]:
    results = []
    for i, ta in enumerate(tables):
        for tb in tables[i + 1:]:
            pair_mappings = []
            for m in column_mappings:
                if m.source_table == ta.name and m.target_table == tb.name:
                    pair_mappings.append((m.source_column, m.target_column))
                elif m.source_table == tb.name and m.target_table == ta.name:
                    pair_mappings.append((m.target_column, m.source_column))
            if not pair_mappings:
                continue

            for ra in ta.records:
                ra_data = json.loads(ra.data) if isinstance(ra.data, str) else ra.data
                for rb in tb.records:
                    rb_data = json.loads(rb.data) if isinstance(rb.data, str) else rb.data
                    comparisons = []
                    sims = []
                    for src_col, tgt_col in pair_mappings:
                        va = str(ra_data.get(src_col, ""))
                        vb = str(rb_data.get(tgt_col, ""))
                        sim = _value_similarity(va, vb)
                        sims.append(sim)
                        if sim >= 0.95:
                            status = "一致"
                        elif sim >= 0.7:
                            status = "近似"
                        elif sim >= 0.4:
                            status = "類似"
                        else:
                            status = "不一致"
                        comparisons.append(RecordFieldComparison(
                            source_column=src_col, target_column=tgt_col,
                            source_value=va, target_value=vb,
                            similarity=round(sim, 2), status=status,
                        ))

                    avg_sim = sum(sims) / len(sims) if sims else 0
                    if avg_sim >= 0.3:
                        merged = {}
                        all_keys = set(ra_data.keys()) | set(rb_data.keys())
                        mapped_tgt = {tgt for _, tgt in pair_mappings}
                        for k in all_keys:
                            if k in ra_data and k not in mapped_tgt:
                                merged[k] = ra_data[k]
                        for src_col, tgt_col in pair_mappings:
                            va = ra_data.get(src_col, "")
                            vb = rb_data.get(tgt_col, "")
                            merged[src_col] = va if va else vb
                        for k in rb_data:
                            if k not in mapped_tgt and k not in merged:
                                merged[k] = rb_data[k]

                        results.append(RecordMatch(
                            source_table=ta.name, target_table=tb.name,
                            source_record_index=ra.record_index,
                            target_record_index=rb.record_index,
                            source_data=ra_data, target_data=rb_data,
                            similarity=round(avg_sim, 2),
                            field_comparisons=comparisons,
                            merged_record=merged,
                        ))

    results.sort(key=lambda x: -x.similarity)
    return results[:30]


def check_duplicates_within_table(table: MasterTable, threshold: float = 0.6) -> list[dict]:
    columns = [c.name for c in table.columns]
    records = []
    for r in table.records:
        data = json.loads(r.data) if isinstance(r.data, str) else r.data
        records.append((r, data))

    pairs = []
    for (ra, da), (rb, db) in itertools.combinations(records, 2):
        comparisons = []
        sims = []
        for col in columns:
            va = str(da.get(col, ""))
            vb = str(db.get(col, ""))
            if not va and not vb:
                sim = 1.0
            elif not va or not vb:
                sim = 0.0
            else:
                sim = _value_similarity(va, vb)
            sims.append(sim)

            if sim >= 0.95:
                status = "一致"
            elif sim >= 0.7:
                status = "近似"
            elif sim >= 0.4:
                status = "類似"
            else:
                status = "不一致"

            comparisons.append(RecordFieldComparison(
                source_column=col, target_column=col,
                source_value=va, target_value=vb,
                similarity=round(sim, 2), status=status,
            ))

        avg_sim = sum(sims) / len(sims) if sims else 0
        if avg_sim >= threshold:
            pairs.append({
                "record_a_id": ra.id,
                "record_b_id": rb.id,
                "record_a_index": ra.record_index,
                "record_b_index": rb.record_index,
                "record_a_data": da,
                "record_b_data": db,
                "overall_similarity": round(avg_sim, 2),
                "field_comparisons": comparisons,
            })

    pairs.sort(key=lambda x: -x["overall_similarity"])
    return pairs[:50]


def suggest_integration(tables: list[MasterTable], mappings: list[AIColumnMapping], variations: list[AIVariation]) -> list[AIIntegrationSuggestion]:
    suggestions = []

    high_conf = [m for m in mappings if m.confidence >= 0.8]
    if high_conf:
        table_pairs = {}
        for m in high_conf:
            key = tuple(sorted([m.source_table, m.target_table]))
            table_pairs.setdefault(key, []).append(m)

        for (t1, t2), cols in table_pairs.items():
            if len(cols) >= 2:
                col_names = ", ".join(f"{c.source_column}↔{c.target_column}" for c in cols[:5])
                suggestions.append(AIIntegrationSuggestion(
                    suggestion_type="テーブル統合",
                    description=f"「{t1}」と「{t2}」は{len(cols)}個の類似カラムを持ち、統合が可能です",
                    tables_involved=[t1, t2],
                    priority="高" if len(cols) >= 3 else "中",
                    details=f"マッピング可能なカラム: {col_names}",
                ))

    if variations:
        suggestions.append(AIIntegrationSuggestion(
            suggestion_type="表記統一",
            description=f"{len(variations)}件の表記揺れが検出されました。統一ルールの策定を推奨します",
            tables_involved=list(set(v.table_name for v in variations)),
            priority="中",
            details="表記揺れを解消することで、データの検索性と一貫性が向上します",
        ))

    all_col_types = {}
    for t in tables:
        for c in t.columns:
            all_col_types.setdefault(c.name, set()).add(c.column_type)
    type_conflicts = {name: types for name, types in all_col_types.items() if len(types) > 1}
    if type_conflicts:
        conflict_details = ", ".join(f"{name}({'/'.join(types)})" for name, types in type_conflicts.items())
        suggestions.append(AIIntegrationSuggestion(
            suggestion_type="型統一",
            description=f"同名カラムで型が異なるケースが{len(type_conflicts)}件あります",
            tables_involved=[t.name for t in tables],
            priority="高",
            details=f"型の不一致: {conflict_details}。統合前に型の統一が必要です。",
        ))

    common_cols = None
    for t in tables:
        col_names = {_normalize(c.name) for c in t.columns}
        if common_cols is None:
            common_cols = col_names
        else:
            common_cols &= col_names
    if common_cols and len(common_cols) >= 2:
        suggestions.append(AIIntegrationSuggestion(
            suggestion_type="共通カラム抽出",
            description=f"全テーブルに共通する{len(common_cols)}個のカラムを上位レイヤーに共通マスタとして抽出可能",
            tables_involved=[t.name for t in tables],
            priority="中",
            details=f"共通カラム: {', '.join(common_cols)}",
        ))

    return suggestions
