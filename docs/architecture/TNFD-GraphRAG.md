# Project Design: TNFD-GraphRAG
**Nature-related Financial Disclosure Analysis System based on Knowledge Graph**

## 1. 개요 (Overview)
본 프로젝트는 기업의 지속가능성 보고서(Sustainability Reports)를 분석하여 TNFD(자연 관련 재무 정보 공개 태스크포스) 프레임워크에 따른 **의존성, 영향, 리스크, 기회(LEAP)**를 자동으로 식별하고, 구조화된 지식 그래프(Knowledge Graph)로 구축하여 고정밀 질의응답(RAG) 시스템을 구현하는 것을 목표로 한다.

### 1.1 핵심 목표
* **비정형 데이터의 구조화:** 방대한 PDF 보고서에서 TNFD 관련 엔티티(위치, 자연 자산, 리스크 등) 간의 연결 관계 추출.
* **설명 가능한 AI (XAI):** 답변 생성 시 근거가 되는 보고서의 원문(Evidence Node)과 논리적 경로(Graph Path)를 함께 제시.
* **복합 추론:** 단순 키워드 검색을 넘어, "특정 지역(Location)의 물 부족(Risk)이 기업의 어떤 공정(Activity)에 영향을 미치는가?"와 같은 다단(Multi-hop) 추론 수행.

---

## 2. 온톨로지 스키마 설계 (Ontology Schema)
NatureKG 논문과 TNFD 공식 가이드라인(Glossary, LEAP)을 기반으로 한 핵심 스키마이다.

### 2.1 Nodes (Entities)
| Node Type | 설명 | 주요 속성 (Properties) |
| :--- | :--- | :--- |
| **Organization** | 분석 대상 기업/조직 | `name`, `industry_code` (ISIC) |
| **Location** | 사업장 또는 자산의 위치 | `name`, `coordinates` (Lat/Lon), `country` |
| **Biome** | 생태계 유형 (TNFD Biomes) | `type` (Tropical Forest, River, etc.) |
| **ValueChain** | 가치사슬 단계 | `stage` (Upstream, Direct, Downstream) |
| **Activity** | 기업의 경제 활동 | `name`, `description` |
| **NatureAsset** | 자연 자본 (물, 토양, 대기 등) | `type` (Water, Soil, Biodiversity) |
| **NatureService** | 생태계 서비스 | `type` (Provisioning, Regulating) |
| **DriverOfChange** | 자연 변화 유발 요인 (오염 등) | `pressure_type` |
| **Risk** | 물리적/이행 리스크 | `category` (Acute, Chronic), `financial_impact` |
| **Action** | 완화 조치 및 전략 | `type` (Avoid, Reduce, Restore), `status` |
| **Target** | 성과 목표 (SBTN 연계) | `metric`, `baseline_year`, `target_year` |
| **Evidence** | 정보의 출처 (텍스트 청크) | `text`, `source_doc`, `page_num`, `embedding` |

### 2.2 Relationships (Edges)
* **Spatial:** `(Organization)-[:OPERATES_IN]->(Location)`, `(Location)-[:LOCATED_IN]->(Biome)`
* **LEAP Flow:**
    * `(ValueChain)-[:GENERATES]->(DriverOfChange)`
    * `(DriverOfChange)-[:IMPACTS]->(NatureAsset)`
    * `(ValueChain)-[:DEPENDS_ON]->(NatureService)`
    * `(NatureAsset)-[:PROVIDES]->(NatureService)`
* **Risk & Response:**
    * `(DriverOfChange)-[:CREATES]->(Risk)`
    * `(Organization)-[:IMPLEMENTS]->(Action)`
    * `(Action)-[:MITIGATES]->(DriverOfChange)` or `(Risk)`
* **Grounding:** `(Evidence)-[:SUPPORTS]->(Action)`, `(Evidence)-[:MENTIONS]->(Risk)`

---

## 3. 시스템 아키텍처 (System Architecture)

### 3.1 Data Pipeline (ETL & Graph Construction)
1.  **Ingestion:** PDF 로드 (PyMuPDF / Unstructured)
2.  **Chunking:** 문맥 보존을 위한 Semantic Chunking 또는 Parent-Child Chunking 적용.
3.  **Extraction (LLM Agent):**
    * **Terms Matching:** TNFD Glossary를 활용하여 텍스트 내 전문 용어 식별.
    * **Triple Extraction:** 프롬프트를 통해 `(Subject, Predicate, Object)` 추출.
    * *Tools:* LlamaIndex `PropertyGraphIndex` 또는 LangChain `LLMGraphTransformer`.
4.  **Entity Resolution:** 'Samsung Elec', 'Samsung Electronics' 등 동의어 병합.
5.  **Storage:**
    * **Graph DB:** Neo4j (구조 저장)
    * **Vector DB:** Neo4j Vector Index (Evidence 노드의 텍스트 임베딩 저장)

### 3.2 Retrieval Pipeline (Hybrid Graph RAG)
1.  **Query Processing:** 사용자의 자연어 질문 입력.
2.  **Keyword/Vector Search:** 질문과 유사한 `Evidence` 및 주요 Entity 노드 검색 (Anchor Nodes).
3.  **Graph Traversal:** Anchor Node로부터 설정된 Depth(예: 2-hop)만큼 이웃 노드 탐색.
4.  **Context Assembly:** 탐색된 서브그래프(Subgraph)와 연결된 텍스트를 LLM 컨텍스트로 조합.
5.  **Generation:** TNFD 전문 용어를 사용하여 답변 생성 및 출처(Citation) 표기.

---

## 4. 구현 상세 가이드 (Implementation Guide)

### 4.1 Tech Stack
* **Language:** Python 3.10+
* **Orchestration:** PyMuPDF4LLLM
* **LLM:** gemini-3-flash-preview
* **Embedding:** text-embedding-3-small or huggingface/bge-m3 (Multilingual)
* **Database:** Neo4j AuraDB (Free Tier 가능) or Dockerized Neo4j
* **Visualization:** Neo4j Bloom or Cytoscape.js

### 4.2 Prompt Strategy (Few-Shot for Extraction)
NatureKG 논문의 Table 1 예시를 프롬프트의 **Few-shot Examples**로 반드시 포함한다.

```text
Example:
Input: "We are implementing regenerative agriculture to reduce soil erosion in our Vietnam farms."
Output:
Nodes: [
  {id: "Regenerative Agriculture", type: "Action", class: "Reduce"},
  {id: "Soil Erosion", type: "DriverOfChange"},
  {id: "Vietnam Farms", type: "Location"},
  {id: "Vietnam", type: "Biome", detail: "Tropical"}
]
Relationships: [
  ("Regenerative Agriculture", "MITIGATES", "Soil Erosion"),
  ("Regenerative Agriculture", "APPLIED_AT", "Vietnam Farms")
]
```
## 5. 단계별 개발 로드맵 (Roadmap)

### Phase 1: MVP (Minimum Viable Product)
* **목표:** 단일 PDF(예: A기업 지속가능경영보고서)에 대한 그래프 구축 및 단순 질의.
* **범위:** Core Ontology 중 5개 핵심 노드(Org, Risk, Action, Location, Evidence)만 구현.
* **검증:** "이 기업의 주요 물리적 리스크는 무엇인가?" 질의 시 정확한 노드 탐색 확인.

### Phase 2: Ontology Extension & Scaling
* **목표:** 전체 온톨로지 적용 및 멀티 문서 처리.
* **작업:**
    * TNFD Glossary 연동 엔티티 추출기 고도화.
    * Biomes, SBTN Target 등 하위 클래스 확장.
    * Entity Resolution 로직 추가 (여러 문서 간 중복 제거).

### Phase 3: Advanced Reasoning & UI
* **목표:** 복합 추론 및 시각화.
* **작업:**
    * Graph Query(Cypher) 자동 생성 에이전트 도입.
    * Streamlit 기반의 Chat UI + 그래프 시각화(Graph Visualization) 대시보드 구축.

---

## 6. 예상되는 도전 과제 및 해결 방안 (Challenges & Solutions)

### 6.1 환각(Hallucination) 관계 생성
* **문제:** LLM이 문서에 없는 허구의 관계를 지어내는 현상.
* **해결:** 온톨로지에 정의된 관계(Schema Constraint) 외에는 생성하지 못하도록 프롬프트 가이드라인을 강화하고, 추출된 모든 관계에 대해 원문 텍스트(Evidence Node)의 연결을 필수화하여 검증 가능하게 함.

### 6.2 모호한 엔티티 처리 (Super Node 문제)
* **문제:** 'Climate Change'나 'Nature'처럼 너무 일반적인 단어가 노드화되어 모든 노드와 연결되는 현상.
* **해결:** 일반 명사는 노드화하지 않고 제외(Skip) 리스트로 관리하거나, TNFD Glossary에 기반하여 구체적인 물리적 리스크(예: 'Extreme Heat', 'Water Stress')로 세분화하여 추출함.

### 6.3 데이터 업데이트 및 버전 관리
* **문제:** 기업 보고서가 매년 업데이트됨에 따라 기존 그래프와의 정합성 유지 필요.
* **해결:** 각 노드와 엣지에 `reporting_period` 또는 `timestamp` 속성을 부여하여 시계열 데이터로 관리하고, 동일 엔티티에 대한 업데이트 로직 적용.

---

## 7. 결론 및 기대 효과 (Conclusion)
본 Graph RAG 시스템을 통해 단순 키워드 검색으로는 발견하기 어려운 **"공급망 내 자연 자본 의존성 - 기후 시나리오 - 재무적 리스크"** 간의 복잡한 인과관계를 가시화할 수 있다. 이는 투자자의 의사결정 지원 및 기업의 TNFD 공시 품질 향상에 크게 기여할 것으로 기대된다.