import json
from backend.models import LayerNode, MasterTable, MasterColumn, MasterRecord, Project, ProcessNode, ProcessEdge
from sqlalchemy.orm import Session


def _add_table(db, layer_node_id, name, description, columns, records):
    table = MasterTable(layer_node_id=layer_node_id, name=name, description=description, record_count=len(records))
    db.add(table)
    db.flush()
    for i, col in enumerate(columns):
        db.add(MasterColumn(master_table_id=table.id, display_order=i, **col))
    for i, rec in enumerate(records):
        db.add(MasterRecord(
            master_table_id=table.id,
            record_index=i,
            data=json.dumps(rec, ensure_ascii=False),
        ))
    return table


def seed_data(db: Session):
    if db.query(LayerNode).count() > 0:
        return

    # ==========================================================
    # Layer 1: 全社共通基幹システム（会計/人事）
    # 名簿マスタを中心に、各システムでバラバラに管理されている問題を可視化
    # ==========================================================
    layer1 = LayerNode(
        name="全社共通基幹システム（会計/人事）",
        description="全社で統一すべき基幹マスタ。現状は各システムが個別にマスタを保持しており整合が取れていない。名簿マスタの統一が最優先課題。Informaticaのカバー範囲。",
        layer_level=1,
    )
    db.add(layer1)
    db.flush()

    # --- 名簿マスタの重複問題を示す3バリエーション ---

    _add_table(db, layer1.id,
        "社員名簿マスタ①（人事部・正式台帳）",
        "人事部が管理する正式な社員名簿。全社統一マスタの基盤とすべきデータ。",
        columns=[
            {"name": "社員番号", "column_type": "String", "is_required": True, "sample_values": "S10234, S10567, S20891"},
            {"name": "氏名", "column_type": "String", "is_required": True, "sample_values": "山田太郎, 鈴木一郎, 佐藤美咲"},
            {"name": "所属部門", "column_type": "String", "is_required": True, "sample_values": "建築事業部, 土木事業部, 設備事業部"},
            {"name": "役職", "column_type": "String", "sample_values": "現場所長, 部長, 課長, 主任"},
            {"name": "メールアドレス", "column_type": "String", "sample_values": "yamada.t@shimizu.co.jp, suzuki.i@shimizu.co.jp"},
            {"name": "入社日", "column_type": "Date", "is_required": True, "sample_values": "2005-04-01, 2010-10-01, 2018-04-01"},
        ],
        records=[
            {"社員番号": "S10234", "氏名": "山田太郎", "所属部門": "建築事業部", "役職": "現場所長", "メールアドレス": "yamada.t@shimizu.co.jp", "入社日": "2005-04-01"},
            {"社員番号": "S10567", "氏名": "鈴木一郎", "所属部門": "土木事業部", "役職": "課長", "メールアドレス": "suzuki.i@shimizu.co.jp", "入社日": "2010-04-01"},
            {"社員番号": "S20891", "氏名": "佐藤美咲", "所属部門": "設備事業部", "役職": "主任", "メールアドレス": "sato.m@shimizu.co.jp", "入社日": "2015-04-01"},
            {"社員番号": "S30124", "氏名": "高橋健太", "所属部門": "建築事業部", "役職": "係長", "メールアドレス": "takahashi.k@shimizu.co.jp", "入社日": "2012-10-01"},
            {"社員番号": "S30456", "氏名": "渡辺直子", "所属部門": "管理本部", "役職": "課長", "メールアドレス": "watanabe.n@shimizu.co.jp", "入社日": "2008-04-01"},
        ],
    )

    _add_table(db, layer1.id,
        "社員名簿マスタ②（日報管理システム）",
        "日報管理システムが保持する作業員台帳。「明日○の作業場に○名いる」を管理。人事部マスタと名前表記・所属名が異なり突合不可の原因。",
        columns=[
            {"name": "作業員ID", "column_type": "String", "is_required": True, "sample_values": "NR-0234, NR-0567, NR-0891"},
            {"name": "名前", "column_type": "String", "is_required": True, "sample_values": "山田 太郎, 鈴木 一郎, 佐藤 美咲"},
            {"name": "所属", "column_type": "String", "is_required": True, "sample_values": "建築部, 土木部, 設備部"},
            {"name": "配置先作業場", "column_type": "String", "sample_values": "豊洲タワー現場, 横浜駅北口再開発, 品川新駅前"},
            {"name": "予定作業内容", "column_type": "String", "sample_values": "鉄筋組立検査, 型枠建込, コンクリート打設"},
            {"name": "登録日", "column_type": "Date", "sample_values": "2025-04-01, 2025-04-15, 2025-05-01"},
        ],
        records=[
            {"作業員ID": "NR-0234", "名前": "山田 太郎", "所属": "建築部", "配置先作業場": "豊洲タワー現場", "予定作業内容": "鉄筋組立検査", "登録日": "2025-04-01"},
            {"作業員ID": "NR-0567", "名前": "鈴木 一郎", "所属": "土木部", "配置先作業場": "横浜駅北口再開発", "予定作業内容": "型枠建込", "登録日": "2025-04-15"},
            {"作業員ID": "NR-0891", "名前": "佐藤 美咲", "所属": "設備部", "配置先作業場": "品川新駅前", "予定作業内容": "電気配管敷設", "登録日": "2025-05-01"},
            {"作業員ID": "NR-1124", "名前": "高橋 健太", "所属": "建築部", "配置先作業場": "豊洲タワー現場", "予定作業内容": "コンクリート打設", "登録日": "2025-04-10"},
        ],
    )

    _add_table(db, layer1.id,
        "社員名簿マスタ③（顔認証出勤管理システム）",
        "顔認証出勤管理システムが保持する台帳。「誰が何時に出退勤したか」を記録。氏名がカタカナ・会社名の(株)表記など人事部マスタと異なり、予定と実績が突合できない問題がある。",
        columns=[
            {"name": "認証ID", "column_type": "String", "is_required": True, "sample_values": "FC-10234, FC-10567, FC-20891"},
            {"name": "氏名", "column_type": "String", "is_required": True, "sample_values": "ヤマダタロウ, スズキイチロウ, サトウミサキ"},
            {"name": "会社名", "column_type": "String", "is_required": True, "sample_values": "清水建設(株), (株)丸山鉄筋工業, 東海型枠(株)"},
            {"name": "所属現場", "column_type": "String", "sample_values": "豊洲タワー, 横浜駅北口, 品川新駅前"},
            {"name": "出勤時刻", "column_type": "String", "sample_values": "07:45, 08:00, 07:30"},
            {"name": "退勤時刻", "column_type": "String", "sample_values": "17:30, 18:15, 17:00"},
        ],
        records=[
            {"認証ID": "FC-10234", "氏名": "ヤマダタロウ", "会社名": "清水建設(株)", "所属現場": "豊洲タワー", "出勤時刻": "07:45", "退勤時刻": "17:30"},
            {"認証ID": "FC-10567", "氏名": "スズキイチロウ", "会社名": "清水建設(株)", "所属現場": "横浜駅北口", "出勤時刻": "08:00", "退勤時刻": "18:15"},
            {"認証ID": "FC-20891", "氏名": "サトウミサキ", "会社名": "清水建設(株)", "所属現場": "品川新駅前", "出勤時刻": "07:30", "退勤時刻": "17:00"},
            {"認証ID": "FC-31124", "氏名": "タカハシケンタ", "会社名": "清水建設(株)", "所属現場": "豊洲タワー", "出勤時刻": "07:50", "退勤時刻": "17:45"},
        ],
    )

    # --- 取引先マスタの重複問題 ---

    _add_table(db, layer1.id,
        "取引先マスタ①（購買部）",
        "購買部が管理する取引先台帳。正式名称で登録。",
        columns=[
            {"name": "取引先コード", "column_type": "String", "is_required": True, "sample_values": "T00123, T00456, T00789"},
            {"name": "会社名", "column_type": "String", "is_required": True, "sample_values": "株式会社丸山鉄筋工業, 株式会社東海型枠, 日本クレーン株式会社"},
            {"name": "代表者", "column_type": "String", "sample_values": "丸山正夫, 田中誠, 山本健一"},
            {"name": "住所", "column_type": "String", "sample_values": "東京都江東区新木場1-3-5, 東京都港区元赤坂1-3-1"},
            {"name": "電話番号", "column_type": "String", "sample_values": "03-3456-7890, 03-5544-1111, 045-678-9012"},
            {"name": "取引区分", "column_type": "Picklist", "is_required": True, "sample_values": "協力会社, 資材業者, リース, コンサル"},
        ],
        records=[
            {"取引先コード": "T00123", "会社名": "株式会社丸山鉄筋工業", "代表者": "丸山正夫", "住所": "東京都江東区新木場1-3-5", "電話番号": "03-3456-7890", "取引区分": "協力会社"},
            {"取引先コード": "T00456", "会社名": "株式会社東海型枠", "代表者": "田中誠", "住所": "神奈川県横浜市鶴見区大黒町5-20", "電話番号": "045-678-9012", "取引区分": "協力会社"},
            {"取引先コード": "T00789", "会社名": "太平洋セメント株式会社", "代表者": "山本健一", "住所": "東京都港区台場2-3-1", "電話番号": "03-5531-7111", "取引区分": "資材業者"},
            {"取引先コード": "T01023", "会社名": "アクティオ株式会社", "代表者": "小沢直義", "住所": "東京都中央区日本橋3-12-2", "電話番号": "03-3279-0621", "取引区分": "リース"},
        ],
    )

    _add_table(db, layer1.id,
        "取引先マスタ②（サプライチェーン管理）",
        "サプライチェーン管理システムが保持する業者台帳。「株式会社」が省略される等、購買部マスタと表記が異なり突合できない問題がある。",
        columns=[
            {"name": "業者コード", "column_type": "String", "is_required": True, "sample_values": "SC-0123, SC-0456, SC-0789"},
            {"name": "企業名", "column_type": "String", "is_required": True, "sample_values": "丸山鉄筋工業, 東海型枠, 日本クレーン"},
            {"name": "担当者", "column_type": "String", "sample_values": "中村浩二, 小林正樹, 高橋義男"},
            {"name": "所在地", "column_type": "String", "sample_values": "江東区新木場, 港区元赤坂, 横浜市鶴見区"},
            {"name": "TEL", "column_type": "String", "sample_values": "03-3456-7890, 03-5544-1111, 045-678-9012"},
            {"name": "業種分類", "column_type": "String", "is_required": True, "sample_values": "鉄筋工事, 型枠工事, 揚重工事, 塗装工事"},
        ],
        records=[
            {"業者コード": "SC-0123", "企業名": "丸山鉄筋工業", "担当者": "中村浩二", "所在地": "江東区新木場", "TEL": "03-3456-7890", "業種分類": "鉄筋工事"},
            {"業者コード": "SC-0456", "企業名": "東海型枠", "担当者": "小林正樹", "所在地": "横浜市鶴見区", "TEL": "045-678-9012", "業種分類": "型枠工事"},
            {"業者コード": "SC-0789", "企業名": "太平洋セメント", "担当者": "高橋義男", "所在地": "港区台場", "TEL": "03-5531-7111", "業種分類": "資材供給"},
            {"業者コード": "SC-1023", "企業名": "アクティオ", "担当者": "田村隆", "所在地": "中央区日本橋", "TEL": "03-3279-0621", "業種分類": "機械リース"},
        ],
    )

    # --- 勘定科目マスタ ---

    _add_table(db, layer1.id,
        "勘定科目マスタ（本社経理）",
        "本社経理部の正式な勘定科目体系。全社共通の会計基盤。",
        columns=[
            {"name": "勘定科目コード", "column_type": "String", "is_required": True, "sample_values": "5110, 5120, 5130, 5210"},
            {"name": "勘定科目名", "column_type": "String", "is_required": True, "sample_values": "材料費, 労務費, 外注費, 経費"},
            {"name": "科目区分", "column_type": "Picklist", "is_required": True, "sample_values": "原価, 販管費, 営業外"},
            {"name": "補助科目", "column_type": "String", "sample_values": "鉄筋材料, 型枠材料, コンクリート材料"},
        ],
        records=[
            {"勘定科目コード": "5110", "勘定科目名": "材料費", "科目区分": "原価", "補助科目": "鉄筋材料"},
            {"勘定科目コード": "5120", "勘定科目名": "労務費", "科目区分": "原価", "補助科目": "直接労務"},
            {"勘定科目コード": "5130", "勘定科目名": "外注費", "科目区分": "原価", "補助科目": "躯体工事"},
            {"勘定科目コード": "5210", "勘定科目名": "経費", "科目区分": "原価", "補助科目": "現場経費"},
        ],
    )

    db.flush()

    # ==========================================================
    # Layer 2: 一部共通マスタ
    # 全社ではないが、建築・土木など一部の事業ドメイン間で共通するマスタ
    # ==========================================================

    layer2_construction = LayerNode(
        parent_id=layer1.id,
        name="建築・土木共通マスタ",
        description="建築事業と土木事業で共通利用するマスタ。全社ではないが複数ドメインで横断的に使用。",
        layer_level=2,
    )
    db.add(layer2_construction)
    db.flush()

    tbl_subcontractor = _add_table(db, layer2_construction.id,
        "協力会社マスタ①（建築部）",
        "建築部が管理する協力会社台帳。土木部とは別管理で、同じ会社が異なる情報で登録されている。",
        columns=[
            {"name": "会社名", "column_type": "String", "is_required": True, "sample_values": "丸山鉄筋工業, 東海型枠, 日本クレーン"},
            {"name": "担当者名", "column_type": "String", "sample_values": "中村浩二, 小林正樹, 高橋義男"},
            {"name": "連絡先", "column_type": "String", "sample_values": "03-3456-7890, 045-678-9012, 03-5544-1111"},
            {"name": "専門工種", "column_type": "String", "is_required": True, "sample_values": "鉄筋工事, 型枠工事, 揚重工事, 塗装工事"},
            {"name": "評価", "column_type": "Picklist", "sample_values": "A, B, C"},
        ],
        records=[
            {"会社名": "丸山鉄筋工業", "担当者名": "中村浩二", "連絡先": "03-3456-7890", "専門工種": "鉄筋工事", "評価": "A"},
            {"会社名": "東海型枠", "担当者名": "小林正樹", "連絡先": "045-678-9012", "専門工種": "型枠工事", "評価": "A"},
            {"会社名": "日本クレーン", "担当者名": "高橋義男", "連絡先": "03-5544-1111", "専門工種": "揚重工事", "評価": "B"},
            {"会社名": "関東塗装工業", "担当者名": "伊藤大輔", "連絡先": "048-234-5678", "専門工種": "塗装工事", "評価": "A"},
        ],
    )

    _add_table(db, layer2_construction.id,
        "協力会社マスタ②（土木部）",
        "土木部が管理する協力業者台帳。建築部と同じ会社でもカラム名・評価基準が異なる。",
        columns=[
            {"name": "企業名", "column_type": "String", "is_required": True, "sample_values": "丸山鉄筋工業, 東海型枠, 日本クレーン"},
            {"name": "担当者", "column_type": "String", "sample_values": "中村浩二, 小林正樹, 高橋義男"},
            {"name": "電話番号", "column_type": "String", "sample_values": "03-3456-7890, 045-678-9012, 03-5544-1111"},
            {"name": "工事種別", "column_type": "String", "is_required": True, "sample_values": "鉄筋, 型枠, 揚重, 塗装"},
            {"name": "ランク", "column_type": "Picklist", "sample_values": "S, A, B, C"},
        ],
        records=[
            {"企業名": "丸山鉄筋工業", "担当者": "中村浩二", "電話番号": "03-3456-7890", "工事種別": "鉄筋", "ランク": "S"},
            {"企業名": "東海型枠", "担当者": "小林正樹", "電話番号": "045-678-9012", "工事種別": "型枠", "ランク": "A"},
            {"企業名": "日本クレーン", "担当者": "高橋義男", "電話番号": "03-5544-1111", "工事種別": "揚重", "ランク": "A"},
            {"企業名": "関東塗装", "担当者": "伊藤大輔", "電話番号": "048-234-5678", "工事種別": "塗装", "ランク": "B"},
        ],
    )

    _add_table(db, layer2_construction.id,
        "工種マスタ（建築・土木共通）",
        "建築・土木で横断的に使用する工種分類。工程表作成時の標準的な工種選択肢の基盤。",
        columns=[
            {"name": "工種コード", "column_type": "String", "is_required": True, "sample_values": "WK001, WK012, WK023, WK034"},
            {"name": "工種名", "column_type": "String", "is_required": True, "sample_values": "鉄筋工事, 型枠工事, コンクリート工事, 鉄骨工事, 防水工事"},
            {"name": "大分類", "column_type": "String", "is_required": True, "sample_values": "躯体, 仕上, 設備, 外構"},
            {"name": "適用ドメイン", "column_type": "Picklist", "is_required": True, "sample_values": "建築・土木共通, 建築のみ, 土木のみ"},
            {"name": "標準工期（日）", "column_type": "Integer", "sample_values": "14, 21, 7, 30"},
        ],
        records=[
            {"工種コード": "WK001", "工種名": "鉄筋工事", "大分類": "躯体", "適用ドメイン": "建築・土木共通", "標準工期（日）": 14},
            {"工種コード": "WK012", "工種名": "型枠工事", "大分類": "躯体", "適用ドメイン": "建築・土木共通", "標準工期（日）": 21},
            {"工種コード": "WK023", "工種名": "コンクリート工事", "大分類": "躯体", "適用ドメイン": "建築・土木共通", "標準工期（日）": 7},
            {"工種コード": "WK034", "工種名": "防水工事", "大分類": "仕上", "適用ドメイン": "建築のみ", "標準工期（日）": 10},
        ],
    )

    _add_table(db, layer2_construction.id,
        "資格マスタ（建築・土木共通）",
        "建築・土木ドメインで共通する資格・免許の台帳。人員配置の要件確認に使用。",
        columns=[
            {"name": "資格コード", "column_type": "String", "is_required": True, "sample_values": "Q001, Q015, Q028, Q042"},
            {"name": "資格名", "column_type": "String", "is_required": True, "sample_values": "1級建築施工管理技士, 1級土木施工管理技士, 建築士(一級), コンクリート技士"},
            {"name": "種別", "column_type": "Picklist", "is_required": True, "sample_values": "国家資格, 技能資格, 講習"},
            {"name": "有効期限", "column_type": "Date", "sample_values": "無期限, 2027-03-31, 2026-09-30"},
        ],
        records=[
            {"資格コード": "Q001", "資格名": "1級建築施工管理技士", "種別": "国家資格", "有効期限": "無期限"},
            {"資格コード": "Q015", "資格名": "1級土木施工管理技士", "種別": "国家資格", "有効期限": "無期限"},
            {"資格コード": "Q028", "資格名": "足場の組立作業主任者", "種別": "技能資格", "有効期限": "2027-03-31"},
            {"資格コード": "Q042", "資格名": "玉掛け技能講習", "種別": "講習", "有効期限": "無期限"},
        ],
    )

    db.flush()

    # --- サプライチェーン共通マスタ ---
    layer2_supply = LayerNode(
        parent_id=layer1.id,
        name="サプライチェーン共通マスタ",
        description="資材調達・物流で事業ドメイン横断的に使用するマスタ。",
        layer_level=2,
    )
    db.add(layer2_supply)
    db.flush()

    _add_table(db, layer2_supply.id,
        "資材マスタ（全社共通品目）",
        "セメント・鉄筋など、建築・土木・設備で横断的に使用する資材の標準品目台帳。",
        columns=[
            {"name": "品目コード", "column_type": "String", "is_required": True, "sample_values": "MAT-001, MAT-015, MAT-032"},
            {"name": "品名", "column_type": "String", "is_required": True, "sample_values": "ポルトランドセメント, 異形棒鋼D16, 合板型枠12mm, H形鋼200x200"},
            {"name": "規格", "column_type": "String", "is_required": True, "sample_values": "JIS R 5210, JIS G 3112 SD345, JIS A 5908, JIS G 3192"},
            {"name": "単位", "column_type": "String", "is_required": True, "sample_values": "t, 本, 枚, kg"},
            {"name": "標準単価", "column_type": "Integer", "sample_values": "12500, 980, 1850, 125000"},
            {"name": "メーカー", "column_type": "String", "sample_values": "太平洋セメント, 東京製鐵, 大建工業, JFEスチール"},
        ],
        records=[
            {"品目コード": "MAT-001", "品名": "ポルトランドセメント", "規格": "JIS R 5210", "単位": "t", "標準単価": 12500, "メーカー": "太平洋セメント"},
            {"品目コード": "MAT-015", "品名": "異形棒鋼D16", "規格": "JIS G 3112 SD345", "単位": "本", "標準単価": 980, "メーカー": "東京製鐵"},
            {"品目コード": "MAT-032", "品名": "合板型枠12mm", "規格": "JIS A 5908", "単位": "枚", "標準単価": 1850, "メーカー": "大建工業"},
            {"品目コード": "MAT-048", "品名": "H形鋼200x200", "規格": "JIS G 3192", "単位": "kg", "標準単価": 125, "メーカー": "JFEスチール"},
        ],
    )

    _add_table(db, layer2_supply.id,
        "倉庫・配送ルートマスタ",
        "資材の保管場所と現場への配送ルートを管理。",
        columns=[
            {"name": "ルートコード", "column_type": "String", "is_required": True, "sample_values": "RT001, RT002, RT015"},
            {"name": "ルート名", "column_type": "String", "is_required": True, "sample_values": "新木場→豊洲現場, 川崎倉庫→横浜現場, 埼玉倉庫→品川現場"},
            {"name": "出発地", "column_type": "String", "is_required": True, "sample_values": "東京資材センター, 川崎物流倉庫, 埼玉第二倉庫"},
            {"name": "到着地", "column_type": "String", "is_required": True, "sample_values": "豊洲タワー現場, 横浜駅北口再開発現場, 品川新駅前現場"},
            {"name": "所要時間（分）", "column_type": "Integer", "sample_values": "45, 90, 120"},
        ],
        records=[
            {"ルートコード": "RT001", "ルート名": "新木場→豊洲現場", "出発地": "東京資材センター", "到着地": "豊洲タワー現場", "所要時間（分）": 45},
            {"ルートコード": "RT002", "ルート名": "川崎倉庫→横浜現場", "出発地": "川崎物流倉庫", "到着地": "横浜駅北口再開発現場", "所要時間（分）": 90},
            {"ルートコード": "RT015", "ルート名": "埼玉倉庫→品川現場", "出発地": "埼玉第二倉庫", "到着地": "品川新駅前現場", "所要時間（分）": 120},
        ],
    )

    db.flush()

    # ==========================================================
    # Layer 3: 分類マスタ（事業ドメインごと）
    # 事業ドメインに特化したマスタ。工程表・建物用途・見積項目など
    # ==========================================================

    # --- 建築事業ドメイン ---
    layer3_architecture = LayerNode(
        parent_id=layer2_construction.id,
        name="建築事業ドメインマスタ",
        description="建築事業に特化した分類マスタ。建物用途・工程表・見積項目など。プロジェクトへのタグ付けや発注量分析の基盤。",
        layer_level=3,
    )
    db.add(layer3_architecture)
    db.flush()

    _add_table(db, layer3_architecture.id,
        "建物用途マスタ（建築）",
        "建築プロジェクトの用途分類。学校・病院・マンション等。どの用途の発注量が多いか等の分析に使用。",
        columns=[
            {"name": "用途コード", "column_type": "String", "is_required": True, "sample_values": "BU-001, BU-002, BU-003, BU-010"},
            {"name": "用途名", "column_type": "String", "is_required": True, "sample_values": "学校, 病院, マンション, オフィスビル, 商業施設"},
            {"name": "大分類", "column_type": "Picklist", "is_required": True, "sample_values": "公共施設, 住居, 商業, 産業"},
            {"name": "標準工期目安（月）", "column_type": "Integer", "sample_values": "18, 24, 36, 12"},
            {"name": "主要規制法規", "column_type": "String", "sample_values": "建築基準法・学校設置基準, 医療法・建築基準法, 建築基準法・消防法"},
        ],
        records=[
            {"用途コード": "BU-001", "用途名": "学校", "大分類": "公共施設", "標準工期目安（月）": 18, "主要規制法規": "建築基準法・学校設置基準"},
            {"用途コード": "BU-002", "用途名": "病院", "大分類": "公共施設", "標準工期目安（月）": 24, "主要規制法規": "医療法・建築基準法"},
            {"用途コード": "BU-003", "用途名": "マンション", "大分類": "住居", "標準工期目安（月）": 36, "主要規制法規": "建築基準法・消防法"},
            {"用途コード": "BU-010", "用途名": "オフィスビル", "大分類": "商業", "標準工期目安（月）": 30, "主要規制法規": "建築基準法・省エネ法"},
        ],
    )

    tbl_arch_process = _add_table(db, layer3_architecture.id,
        "工程表マスタ①（建築工事）",
        "建築工事の標準工程項目。現場所長ごとに書き方が異なり全現場を横串で見られない問題を解決。Excelから脱却し選択式にすることで全社集計を可能にする。",
        columns=[
            {"name": "工程コード", "column_type": "String", "is_required": True, "sample_values": "AP-001, AP-002, AP-003, AP-010"},
            {"name": "工程名", "column_type": "String", "is_required": True, "sample_values": "仮設工事, 基礎工事, 躯体工事, 仕上工事, 設備工事"},
            {"name": "フェーズ", "column_type": "Picklist", "is_required": True, "sample_values": "準備, 地下, 地上, 仕上, 検査"},
            {"name": "標準日数", "column_type": "Integer", "sample_values": "14, 30, 80, 60, 45"},
            {"name": "前工程コード", "column_type": "String", "sample_values": "-, AP-001, AP-002, AP-003"},
            {"name": "必要資格", "column_type": "String", "sample_values": "-, 1級建築施工管理技士, 鉄筋施工技能士, コンクリート技士"},
        ],
        records=[
            {"工程コード": "AP-001", "工程名": "仮設工事", "フェーズ": "準備", "標準日数": 14, "前工程コード": "-", "必要資格": "-"},
            {"工程コード": "AP-002", "工程名": "基礎工事", "フェーズ": "地下", "標準日数": 30, "前工程コード": "AP-001", "必要資格": "1級建築施工管理技士"},
            {"工程コード": "AP-003", "工程名": "躯体工事", "フェーズ": "地上", "標準日数": 80, "前工程コード": "AP-002", "必要資格": "鉄筋施工技能士"},
            {"工程コード": "AP-004", "工程名": "仕上工事", "フェーズ": "仕上", "標準日数": 60, "前工程コード": "AP-003", "必要資格": "-"},
            {"工程コード": "AP-005", "工程名": "設備工事", "フェーズ": "地上", "標準日数": 45, "前工程コード": "AP-003", "必要資格": "電気工事士"},
        ],
    )

    _add_table(db, layer3_architecture.id,
        "見積項目マスタ（建築）",
        "建築工事の見積書で使用する標準項目。工程表マスタと連携し、雨等で工程変更があれば見積もり・人員配置へ自動反映を目指す。",
        columns=[
            {"name": "見積項目コード", "column_type": "String", "is_required": True, "sample_values": "EST-A001, EST-A010, EST-A025"},
            {"name": "項目名", "column_type": "String", "is_required": True, "sample_values": "仮設足場, 鉄筋加工組立, コンクリート打設, 型枠工"},
            {"name": "カテゴリ", "column_type": "Picklist", "is_required": True, "sample_values": "仮設, 躯体, 仕上, 設備"},
            {"name": "単位", "column_type": "String", "sample_values": "m², t, m³, 式"},
            {"name": "標準単価", "column_type": "Integer", "sample_values": "2800, 85000, 16500, 120000"},
            {"name": "対応工程コード", "column_type": "String", "sample_values": "AP-001, AP-003, AP-002"},
        ],
        records=[
            {"見積項目コード": "EST-A001", "項目名": "仮設足場", "カテゴリ": "仮設", "単位": "m²", "標準単価": 2800, "対応工程コード": "AP-001"},
            {"見積項目コード": "EST-A010", "項目名": "鉄筋加工組立", "カテゴリ": "躯体", "単位": "t", "標準単価": 85000, "対応工程コード": "AP-003"},
            {"見積項目コード": "EST-A025", "項目名": "コンクリート打設", "カテゴリ": "躯体", "単位": "m³", "標準単価": 16500, "対応工程コード": "AP-003"},
            {"見積項目コード": "EST-A040", "項目名": "型枠工", "カテゴリ": "躯体", "単位": "m²", "標準単価": 4200, "対応工程コード": "AP-003"},
        ],
    )

    db.flush()

    # --- 土木事業ドメイン ---
    layer3_civil = LayerNode(
        parent_id=layer2_construction.id,
        name="土木事業ドメインマスタ",
        description="土木事業に特化した分類マスタ。ダム・橋梁・トンネル等の用途分類と工程表。建築とは体系が異なる。",
        layer_level=3,
    )
    db.add(layer3_civil)
    db.flush()

    _add_table(db, layer3_civil.id,
        "土木用途マスタ（土木）",
        "土木プロジェクトの用途分類。ダム・橋梁・道路等。建築の「学校・病院」とは異なる分類体系。",
        columns=[
            {"name": "用途コード", "column_type": "String", "is_required": True, "sample_values": "CU-001, CU-002, CU-003, CU-010"},
            {"name": "用途名", "column_type": "String", "is_required": True, "sample_values": "ダム, 橋梁, トンネル, 道路, 河川護岸"},
            {"name": "大分類", "column_type": "Picklist", "is_required": True, "sample_values": "河川・ダム, 道路・橋梁, トンネル, 港湾"},
            {"name": "標準工期目安（月）", "column_type": "Integer", "sample_values": "60, 36, 48, 24"},
            {"name": "主要発注者", "column_type": "String", "sample_values": "国土交通省, NEXCO, 都道府県, 市区町村"},
        ],
        records=[
            {"用途コード": "CU-001", "用途名": "ダム", "大分類": "河川・ダム", "標準工期目安（月）": 60, "主要発注者": "国土交通省"},
            {"用途コード": "CU-002", "用途名": "橋梁", "大分類": "道路・橋梁", "標準工期目安（月）": 36, "主要発注者": "NEXCO"},
            {"用途コード": "CU-003", "用途名": "トンネル", "大分類": "トンネル", "標準工期目安（月）": 48, "主要発注者": "国土交通省"},
            {"用途コード": "CU-010", "用途名": "道路", "大分類": "道路・橋梁", "標準工期目安（月）": 24, "主要発注者": "都道府県"},
        ],
    )

    _add_table(db, layer3_civil.id,
        "工程表マスタ②（土木工事）",
        "土木工事の標準工程項目。建築工事とは工程体系が異なる。天候影響度の管理が重要。",
        columns=[
            {"name": "工程コード", "column_type": "String", "is_required": True, "sample_values": "CP-001, CP-002, CP-003, CP-010"},
            {"name": "工程名", "column_type": "String", "is_required": True, "sample_values": "用地準備・測量, 掘削工事, 基礎杭打設, コンクリート打設"},
            {"name": "フェーズ", "column_type": "Picklist", "is_required": True, "sample_values": "準備, 掘削, 構造, 仕上, 検査"},
            {"name": "標準日数", "column_type": "Integer", "sample_values": "30, 60, 45, 90"},
            {"name": "前工程コード", "column_type": "String", "sample_values": "-, CP-001, CP-002, CP-003"},
            {"name": "天候影響度", "column_type": "Picklist", "sample_values": "低, 中, 高"},
        ],
        records=[
            {"工程コード": "CP-001", "工程名": "用地準備・測量", "フェーズ": "準備", "標準日数": 30, "前工程コード": "-", "天候影響度": "低"},
            {"工程コード": "CP-002", "工程名": "掘削工事", "フェーズ": "掘削", "標準日数": 60, "前工程コード": "CP-001", "天候影響度": "高"},
            {"工程コード": "CP-003", "工程名": "基礎杭打設", "フェーズ": "構造", "標準日数": 45, "前工程コード": "CP-002", "天候影響度": "中"},
            {"工程コード": "CP-010", "工程名": "コンクリート打設", "フェーズ": "構造", "標準日数": 90, "前工程コード": "CP-003", "天候影響度": "高"},
        ],
    )

    db.flush()

    # --- 設備事業ドメイン ---
    layer3_equipment = LayerNode(
        parent_id=layer2_construction.id,
        name="設備事業ドメインマスタ",
        description="設備工事（電気・空調・給排水等）に特化した分類マスタ。建築躯体工程との連動が重要。",
        layer_level=3,
    )
    db.add(layer3_equipment)
    db.flush()

    _add_table(db, layer3_equipment.id,
        "工程表マスタ③（設備工事）",
        "設備工事の標準工程項目。建築躯体の進捗に連動して計画する必要がある。",
        columns=[
            {"name": "工程コード", "column_type": "String", "is_required": True, "sample_values": "EP-001, EP-002, EP-003, EP-010"},
            {"name": "工程名", "column_type": "String", "is_required": True, "sample_values": "電気配管・配線（地中埋設）, 空調ダクト設置, 給排水配管, 受変電設備搬入"},
            {"name": "設備区分", "column_type": "Picklist", "is_required": True, "sample_values": "電気, 空調, 給排水, 防災"},
            {"name": "標準日数", "column_type": "Integer", "sample_values": "10, 15, 20, 5"},
            {"name": "前工程コード", "column_type": "String", "sample_values": "-, EP-001, EP-002, EP-003"},
            {"name": "連動建築工程", "column_type": "String", "sample_values": "基礎工事, 躯体工事（1F-8F）, 躯体工事（9F-15F）, 仕上工事"},
        ],
        records=[
            {"工程コード": "EP-001", "工程名": "電気配管・配線（地中埋設）", "設備区分": "電気", "標準日数": 10, "前工程コード": "-", "連動建築工程": "基礎工事"},
            {"工程コード": "EP-002", "工程名": "空調ダクト設置", "設備区分": "空調", "標準日数": 15, "前工程コード": "EP-001", "連動建築工程": "躯体工事（1F-8F）"},
            {"工程コード": "EP-003", "工程名": "給排水配管", "設備区分": "給排水", "標準日数": 20, "前工程コード": "EP-001", "連動建築工程": "躯体工事（1F-8F）"},
            {"工程コード": "EP-010", "工程名": "受変電設備搬入", "設備区分": "電気", "標準日数": 5, "前工程コード": "EP-002", "連動建築工程": "仕上工事"},
        ],
    )

    tbl_equipment = _add_table(db, layer3_equipment.id,
        "設備機器マスタ（設備）",
        "設備工事で使用する機器の標準台帳。型式・メーカー・設置場所を管理。",
        columns=[
            {"name": "機器コード", "column_type": "String", "is_required": True, "sample_values": "EQ-001, EQ-002, EQ-003, EQ-010"},
            {"name": "機器名称", "column_type": "String", "is_required": True, "sample_values": "パッケージエアコン, 受変電設備, エレベーター, 給水ポンプユニット"},
            {"name": "設備区分", "column_type": "Picklist", "is_required": True, "sample_values": "空調, 電気, 昇降機, 給排水, 防災"},
            {"name": "メーカー", "column_type": "String", "sample_values": "ダイキン工業, 日立産機, 三菱電機, 荏原製作所"},
            {"name": "標準単価", "column_type": "Integer", "sample_values": "3200000, 15000000, 28000000, 4500000"},
            {"name": "耐用年数", "column_type": "Integer", "sample_values": "15, 20, 25, 15"},
        ],
        records=[
            {"機器コード": "EQ-001", "機器名称": "パッケージエアコン", "設備区分": "空調", "メーカー": "ダイキン工業", "標準単価": 3200000, "耐用年数": 15},
            {"機器コード": "EQ-002", "機器名称": "受変電設備500KVA", "設備区分": "電気", "メーカー": "日立産機", "標準単価": 15000000, "耐用年数": 20},
            {"機器コード": "EQ-003", "機器名称": "乗用エレベーター", "設備区分": "昇降機", "メーカー": "三菱電機", "標準単価": 28000000, "耐用年数": 25},
            {"機器コード": "EQ-010", "機器名称": "給水ポンプユニット", "設備区分": "給排水", "メーカー": "荏原製作所", "標準単価": 4500000, "耐用年数": 15},
        ],
    )

    db.flush()

    # ==========================================================
    # Project (BPM) — 建築・設備の工程表統合と見積連携の実証
    # ==========================================================
    project = Project(
        name="豊洲タワーマンション新築工事",
        description="RC造15階建タワーマンション新築工事。建築・設備の工程表統合と見積連携の実証プロジェクト。",
        status="施工中",
        created_by="管理者",
    )
    db.add(project)
    db.flush()

    nodes_data = [
        {"label": "着工準備", "node_type": "milestone", "position_x": 100, "position_y": 150, "duration_days": 7, "status": "完了"},
        {"label": "仮設工事", "node_type": "task", "position_x": 350, "position_y": 50, "duration_days": 14, "status": "完了"},
        {"label": "地盤改良", "node_type": "task", "position_x": 350, "position_y": 250, "duration_days": 21, "status": "施工中"},
        {"label": "基礎工事", "node_type": "task", "position_x": 600, "position_y": 150, "duration_days": 30, "status": "未着手"},
        {"label": "躯体工事（1F-8F）", "node_type": "task", "position_x": 850, "position_y": 50, "duration_days": 80, "status": "未着手"},
        {"label": "躯体工事（9F-15F）", "node_type": "task", "position_x": 850, "position_y": 250, "duration_days": 70, "status": "未着手"},
        {"label": "設備工事（電気・空調）", "node_type": "task", "position_x": 1100, "position_y": 50, "duration_days": 45, "status": "未着手"},
        {"label": "仕上工事", "node_type": "task", "position_x": 1100, "position_y": 250, "duration_days": 60, "status": "未着手"},
        {"label": "竣工検査", "node_type": "milestone", "position_x": 1350, "position_y": 150, "duration_days": 5, "status": "未着手"},
    ]

    node_table_links = {
        0: tbl_subcontractor.id,
        3: tbl_arch_process.id,
        6: tbl_equipment.id,
    }

    created_nodes = []
    for i, nd in enumerate(nodes_data):
        node = ProcessNode(
            project_id=project.id,
            master_table_id=node_table_links.get(i),
            **nd,
        )
        db.add(node)
        db.flush()
        created_nodes.append(node)

    edges_data = [
        (0, 1), (0, 2),
        (1, 3), (2, 3),
        (3, 4), (3, 5),
        (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 8), (7, 8),
    ]
    for src_idx, tgt_idx in edges_data:
        edge = ProcessEdge(
            project_id=project.id,
            source_node_id=created_nodes[src_idx].id,
            target_node_id=created_nodes[tgt_idx].id,
        )
        db.add(edge)

    bpm_records = [
        (tbl_subcontractor.id, created_nodes[0].id, {"会社名": "東京足場工業", "担当者名": "佐々木一郎", "連絡先": "03-6789-0123", "専門工種": "足場工事", "評価": "A"}),
        (tbl_arch_process.id, created_nodes[3].id, {"工程コード": "AP-006", "工程名": "杭打ち工事", "フェーズ": "地下", "標準日数": 20, "前工程コード": "AP-001", "必要資格": "1級建築施工管理技士"}),
        (tbl_equipment.id, created_nodes[6].id, {"機器コード": "EQ-011", "機器名称": "非常用発電機500KVA", "設備区分": "電気", "メーカー": "ヤンマー", "標準単価": 12000000, "耐用年数": 20}),
    ]
    for table_id, node_id, data in bpm_records:
        idx = db.query(MasterRecord).filter(MasterRecord.master_table_id == table_id).count()
        db.add(MasterRecord(
            master_table_id=table_id,
            record_index=idx,
            data=json.dumps(data, ensure_ascii=False),
            source_node_id=node_id,
        ))
        tbl = db.query(MasterTable).get(table_id)
        if tbl:
            tbl.record_count = idx + 1

    db.commit()
