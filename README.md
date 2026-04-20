# 建設BPM+MDM v3

建設業向けのマスタデータ管理（MDM）と工程管理（BPM）を統合したWebアプリケーション v3。
議事録ベースのユースケースから設計された3階層マスタデータ構造（全社基幹→共通→ドメイン別）と、AIによるテーブル分析・統合機能、ReactFlowによるビジュアル工程管理を提供する。

## v2からの主な変更点

- **データベースをLakeBase(PostgreSQL)に移行**: SQLiteからDatabricks LakeBase（PostgreSQL互換）に切り替え。永続的なクラウドDBにより、アプリ再起動後もデータが保持される
- **AI重複チェック機能**: 単一テーブル内のレコード重複をAIが検出。フィールド単位の類似度比較、サイドバイサイドの比較モーダル、マニュアル編集、解決アクション（Aを残す/Bを残す/マージ/両方残す）を提供
- **静的重複チェック列の廃止**: 複合キーベースの固定「重複チェック」列を削除し、AI判定に置き換え
- **デプロイ先変更**: dbc-1b865228-e1e5ワークスペース（`lakebase-workspace`プロファイル）

## マスタデータ構造

```
▼ 全社共通基幹システム（会計/人事） [レイヤー1]
   ├ 社員名簿マスタ①（人事部・正式台帳）(6列)
   ├ 社員名簿マスタ②（日報管理システム）(6列)
   ├ 社員名簿マスタ③（顔認証出勤管理）(6列)
   ├ 取引先マスタ①（購買部）(6列)
   ├ 取引先マスタ②（サプライチェーン管理）(6列)
   └ 勘定科目マスタ（本社経理）(4列)
   ▼ 建築・土木共通マスタ [レイヤー2]
      ├ 協力会社マスタ①（建築部）(5列)
      ├ 協力会社マスタ②（土木部）(5列)
      ├ 工種マスタ（建築・土木共通）(5列)
      └ 資格マスタ（建築・土木共通）(4列)
   ▼ サプライチェーン共通マスタ [レイヤー2]
      ├ 資材マスタ（全社共通品目）(6列)
      └ 倉庫・配送ルートマスタ(5列)
   ▼ 建築事業ドメインマスタ [レイヤー3]
      ├ 建物用途マスタ（建築）(5列)
      ├ 工程表マスタ①（建築工事）(6列)
      └ 見積項目マスタ（建築）(6列)
   ▼ 土木事業ドメインマスタ [レイヤー3]
      ├ 土木用途マスタ（土木）(5列)
      └ 工程表マスタ②（土木工事）(6列)
   ▼ 設備事業ドメインマスタ [レイヤー3]
      ├ 工程表マスタ③（設備工事）(6列)
      └ 設備機器マスタ（設備）(6列)
```

**合計**: 6レイヤーノード / 19マスタテーブル / 104カラム / 80シードレコード

## 技術スタック

### バックエンド

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| FastAPI | 0.115.0 | APIサーバー |
| Uvicorn | 0.30.6 | ASGIサーバー |
| SQLAlchemy | 2.0.35 | ORM |
| Pydantic | 2.9.2 | バリデーション |
| psycopg2-binary | 2.9.10 | PostgreSQLドライバー |
| aiofiles | 24.1.0 | 非同期ファイルI/O |

### フロントエンド

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| React | 18.3.1 | UIフレームワーク |
| React Router | 6.26.2 | ルーティング |
| ReactFlow | 11.11.4 | フローダイアグラム |
| Lucide React | 0.447.0 | アイコン |
| Vite | 5.4.9 | ビルドツール |
| TailwindCSS | 3.4.13 | CSSフレームワーク |

### インフラ

| 項目 | 内容 |
|------|------|
| データベース | Databricks LakeBase (PostgreSQL互換) |
| フォールバックDB | SQLite（ローカル開発用） |
| デプロイ先 | Databricks Apps (dbc-1b865228-e1e5) |
| ホスティング | FastAPIによるSPA配信 + APIサーバー一体型 |

## システムアーキテクチャ

```
┌──────────────────────────────────────────────────────────┐
│          Databricks Apps (dbc-1b865228-e1e5)             │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Uvicorn (port 8000)                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │              FastAPI                          │  │  │
│  │  │                                              │  │  │
│  │  │  /api/*  ──→  APIエンドポイント群            │  │  │
│  │  │  /assets/* ──→ 静的ファイル配信              │  │  │
│  │  │  /*       ──→ SPA (index.html)               │  │  │
│  │  │                                              │  │  │
│  │  │  ┌─────────────┐  ┌──────────────────────┐  │  │  │
│  │  │  │ SQLAlchemy   │  │ AI Analysis Engine  │  │  │  │
│  │  │  │   ORM        │  │ (重複検出/統合分析)  │  │  │  │
│  │  │  └──────┬───────┘  └──────────────────────┘  │  │  │
│  │  │         │                                    │  │  │
│  │  │  ┌──────▼────────────────────────────────┐   │  │  │
│  │  │  │  Databricks LakeBase (PostgreSQL)     │   │  │  │
│  │  │  │  ep-noisy-lab-d1uadqkd.database...    │   │  │  │
│  │  │  └───────────────────────────────────────┘   │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                      ブラウザ                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  React SPA (Vite ビルド)                            │  │
│  │  ┌──────────┐ ┌──────────────┐ ┌────────────┐      │  │
│  │  │Dashboard │ │ MasterData   │ │   BPM      │      │  │
│  │  │  Page    │ │   Page       │ │   Page     │      │  │
│  │  └──────────┘ └──────────────┘ └────────────┘      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### ディレクトリ構成

```
construction-bpm-mdm-v3/
├── backend/
│   ├── __init__.py
│   ├── main.py            # FastAPIアプリ & 全APIエンドポイント
│   ├── models.py           # SQLAlchemy ORMモデル
│   ├── schemas.py          # Pydanticスキーマ
│   ├── database.py         # DB接続設定（LakeBase/SQLite切替）
│   ├── ai_analysis.py      # AI分析エンジン（重複検出・統合分析）
│   └── seed.py             # 初期データ投入（リアルな建設業データ）
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # ルーティング & ナビゲーション
│   │   ├── main.jsx        # エントリポイント
│   │   ├── index.css       # グローバルCSS
│   │   └── pages/
│   │       ├── DashboardPage.jsx    # ダッシュボード
│   │       ├── MasterDataPage.jsx   # マスタデータ管理（ツリーUI + AI重複チェック）
│   │       └── BPMPage.jsx          # 工程管理
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── index.html
├── static/                 # Viteビルド出力（デプロイ用）
│   ├── index.html
│   └── assets/
├── app.yaml                # Databricks Appsデプロイ設定 + DATABASE_URL
├── requirements.txt        # Python依存パッケージ
├── .gitignore
└── .databricksignore       # Databricks sync除外設定
```

## ER図

```
┌──────────────────────┐
│      LayerNode       │
│──────────────────────│
│ id (PK)              │
│ name                 │         ┌─────────────────────────┐
│ description          │         │      MasterTable        │
│ layer_level          │         │─────────────────────────│
│ parent_id (FK:self)  │────1:N──│ id (PK)                 │
│ created_at           │         │ layer_node_id (FK)      │
│ updated_at           │         │ name                    │
└──────┬───────────────┘         │ description             │
       │                         │ record_count            │
       │ self                    │ created_at              │
       │ 1:N                     │ updated_at              │
       └─── LayerNode            └──────┬──────────┬───────┘
             (children)                 │          │
                                        │ 1:N      │ 1:N
                                        ▼          ▼
                            ┌──────────────────┐  ┌─────────────────┐
                            │  MasterColumn    │  │  MasterRecord   │
                            │──────────────────│  │─────────────────│
                            │ id (PK)          │  │ id (PK)         │
                            │ master_table_id  │  │ master_table_id │
                            │ name             │  │ record_index    │
                            │ column_type      │  │ data (JSON)     │
                            │ description      │  │ source_node_id  │
                            │ is_required      │  │ created_at      │
                            │ source_object    │  └─────────────────┘
                            │ source_field     │
                            │ sample_values    │
                            │ display_order    │
                            │ created_at       │
                            │ updated_at       │
                            └────────┬─────────┘
                                     │
                                     │ M:N
                                     │ (node_master_columns)
                                     │
┌──────────────────────┐             │
│       Project        │             │
│──────────────────────│             │
│ id (PK)              │             │
│ name                 │             │
│ description          │             │
│ status               │             │
│ created_by           │             │
│ created_at           │         ┌───▼────────────────┐
│ updated_at           │────1:N──│    ProcessNode     │
└──────────┬───────────┘         │────────────────────│
           │                     │ id (PK)            │
           │                     │ project_id (FK)    │
           │                     │ label              │
           │                     │ node_type          │
           │                     │ position_x         │
           │                     │ position_y         │
           │                     │ duration_days      │
           │                     │ status             │
           │                     │ description        │
           │                     │ master_table_id    │
           │                     │ created_at         │
           │                     │ updated_at         │
           │                     └────────────────────┘
           │                              ▲       ▲
           │                              │       │
           │                     source_node_id  target_node_id
           │                              │       │
           │     ┌────────────────────────┴───────┘
           │     │
           │ 1:N │
           │     ▼
           │  ┌──────────────────────┐
           └──│    ProcessEdge       │
              │──────────────────────│
              │ id (PK)              │
              │ project_id (FK)      │
              │ source_node_id (FK)  │
              │ target_node_id (FK)  │
              │ label                │
              │ created_at           │
              └──────────────────────┘
```

### モデル間の関係

| 関係 | 説明 |
|------|------|
| LayerNode → LayerNode | 自己参照 (parent_id)。3階層のツリー構造 |
| LayerNode → MasterTable | 1:N。各レイヤーに複数のマスタテーブル |
| MasterTable → MasterColumn | 1:N。テーブル内のカラム定義 |
| MasterTable → MasterRecord | 1:N。JSONデータとして格納されるレコード |
| Project → ProcessNode | 1:N。プロジェクト内の工程ノード |
| Project → ProcessEdge | 1:N。ノード間の接続 |
| ProcessNode ↔ MasterColumn | M:N。工程とマスタカラムの紐付け |
| ProcessNode → MasterTable | N:1。工程ノードとマスタテーブルの紐付け |

## デプロイ方法

### 前提条件

- Python 3.10+
- Node.js 18+
- Databricks CLI（認証設定済み、`lakebase-workspace`プロファイル）

### 1. ローカル環境セットアップ

```bash
git clone https://github.com/ytsuchiya-work/construction-bpm-mdm-v3.git
cd construction-bpm-mdm-v3

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
cd ..
```

### 2. ローカル開発サーバー起動

```bash
# SQLiteモード（デフォルト）
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# LakeBase接続モード
DATABASE_URL="postgresql+psycopg2://user:token@host/dbname?sslmode=require" \
  uvicorn backend.main:app --reload --port 8000
```

- APIサーバー: http://localhost:8000
- フロントエンド開発サーバー: http://localhost:5173（`cd frontend && npm run dev`）
- Viteの設定により `/api` リクエストはバックエンドに自動プロキシされる

### 3. Databricks Appsへのデプロイ

```bash
# フロントエンドビルド（static/ ディレクトリに出力）
cd frontend && npm run build && cd ..

# Databricks Appsの作成（初回のみ）
databricks apps create construction-bpm-mdm-v3 --profile lakebase-workspace

# ファイルをWorkspaceに同期
databricks sync . /Workspace/Users/<your-email>/construction-bpm-mdm-v3 \
  --profile lakebase-workspace --watch=false

# デプロイ
databricks apps deploy construction-bpm-mdm-v3 \
  --source-code-path /Workspace/Users/<your-email>/construction-bpm-mdm-v3 \
  --profile lakebase-workspace
```

### 4. デプロイ後の確認

```bash
databricks apps get construction-bpm-mdm-v3 --profile lakebase-workspace
```

## アプリの使用方法

### ダッシュボード (`/`)

アプリ全体の統計情報を表示する。レイヤー別のノード数、マスタテーブル数、カラム数、レコード数、プロジェクト数を一覧で確認できる。

### マスタデータ管理 (`/master`)

#### ツリーナビゲーション（左パネル）

- 3階層のレイヤー構造をツリー形式で表示
  - **レイヤー1**（青）: 全社共通基幹システム（会計/人事）
  - **レイヤー2**（オレンジ）: 建築・土木共通マスタ / サプライチェーン共通マスタ
  - **レイヤー3**（赤）: 建築 / 土木 / 設備 ドメインマスタ
- 各レイヤーの展開/折りたたみが可能
- レイヤー配下のマスタテーブルを一覧表示
- 検索ボックスでレイヤー名・テーブル名をフィルタリング

#### テーブル閲覧（メインエリア）

- テーブルをクリックすると詳細を表示
- **データ一覧タブ**: レコードを通常のテーブル形式で表示。各テーブルには4〜5件のシードレコードが登録されている
- **カラム定義タブ**: カラム名・型・必須フラグ・ソース情報・サンプル値を表示。インライン編集に対応

#### AI重複チェック

1. テーブルを選択し「AI重複チェック」ボタンをクリック
2. AIがテーブル内の全レコードペアを比較し、類似度が閾値以上のペアを検出
3. モーダルで重複ペアをサイドバイサイド表示:
   - 各フィールドの類似度（%表示 + カラーコード）
   - 編集可能なテキスト入力でマニュアル修正
4. 解決アクション:
   - **Aを残す**: レコードAを（編集内容で）更新し、Bを削除
   - **Bを残す**: レコードBを（編集内容で）更新し、Aを削除
   - **マージして残す**: AとBの編集内容をマージしてAに保存、Bを削除
   - **両方残す**: 何もせず次のペアへ

#### AI分析（右パネル）

1. ツリーのチェックボックスで2つ以上のテーブルを選択
2. 「AI分析実行」ボタンをクリック
3. 4つのタブで分析結果を確認:
   - **列マッピング**: テーブル間のカラム対応関係と一致度
   - **レコード照合**: テーブル間のレコード一致度とマージプレビュー
   - **表記揺れ**: カタカナ表記・漢字同義語の検出
   - **統合サジェスト**: テーブル統合の提案と優先度
4. 「統合マスタ作成」でAIが分析結果に基づき統合テーブルを自動生成

#### テーブルの追加・削除

- レイヤーノード横の「＋」ボタンから新規テーブルを作成
- テーブル横のゴミ箱アイコンで削除（確認ダイアログ付き）
- 複数テーブルを選択して一括削除も可能

### 工程管理 (`/bpm`)

#### プロジェクト選択（左パネル上部）

- ドロップダウンから管理対象のプロジェクトを選択

#### フローキャンバス（メインエリア）

- ノードをドラッグで配置を変更
- ノード間をドラッグして接続（エッジ作成）
- ミニマップとズームコントロールで全体把握
- ステータスに応じた色分け:
  - グレー: 未着手
  - 青: 施工中
  - 緑: 完了

#### ノードの追加・編集（左パネル）

- パレットから「タスク」「マイルストーン」をキャンバスにドラッグ&ドロップで追加
- ノードをクリックすると左パネルに詳細を表示:
  - 名前、工期（日数）、ステータスを編集
  - マスタテーブルとの紐付け
  - マスタカラムとの紐付け（ツリーからチェックボックスで選択）
  - ノード削除
- エッジをクリックすると接続情報を表示・削除可能
