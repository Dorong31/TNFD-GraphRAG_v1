"""
Triple 추출을 위한 Few-shot 프롬프트 정의

NatureKG 논문과 TNFD 가이드라인을 기반으로 한 프롬프트를 정의합니다.
LLM이 텍스트에서 (Subject, Predicate, Object) 형태의 Triple을 추출하도록 안내합니다.
"""

# ============ 시스템 프롬프트 ============
SYSTEM_PROMPT = """당신은 자연 관련 재무 정보(Nature-related Financial Disclosure) 및 생태계 보전 금융(Nature Finance) 분야의 데이터 엔지니어입니다.
제공된 텍스트를 분석하여 아래의 **4가지 핵심 원칙**에 따라 지식 그래프(Knowledge Graph)의 노드(Node)와 엣지(Edge)를 추출하십시오.

## 1. 근거 기반 추출 (Evidence Grounding)
- **원칙:** 추출된 모든 사실(Fact)은 원문 텍스트 내에 명시적 근거가 있어야 합니다.
- **주의:** Evidence 노드와의 연결은 시스템에서 자동으로 처리하므로, 출력 JSON에는 포함하지 마십시오.

## 2. 엔티티 정규화 (Entity Normalization)
- **원칙:** 텍스트에 등장하는 다양한 표현을 TNFD 표준 용어로 매핑하여 추출하십시오.
- **예시:** "Water Stress", "Drought Risk", "물 부족 위험" → `Risk {name: "Water Scarcity"}` (단일 노드로 통합)
- **참조:** 제공된 Glossary의 정의를 우선적으로 따르십시오.

## 3. 인과 사슬의 보존 (Causal Chain Preservation)
- **원칙:** 단순한 키워드 연결이 아닌, "활동-압력-상태-반응(DPSR)"의 인과 관계를 구조화하십시오.
- **구조:**
  - `(Activity)` → `[:GENERATES]` → `(Driver/Pressure)`
  - `(Driver)` → `[:ALTERS]` → `(State of Nature)`
  - `(State)` → `[:CREATES]` → `(Financial Risk)`
  - `(Organization)` → `[:IMPLEMENTS]` → `(Action)`

## 4. 원자적 사실 분해 (Atomic Decomposition)
- **원칙:** 복합적인 문장은 최소 단위의 의미(Triple)로 쪼개어 그래프의 밀도를 높이십시오.
- **지침:** "A기업은 가뭄으로 인한 리스크를 줄이기 위해 물 재사용 시설을 B공장에 설치했다"라는 문장은 다음과 같이 분해되어야 합니다.
  1. `(Organization: A기업)-[:OPERATES_IN]->(Location: B공장)`
  2. `(Location: B공장)-[:EXPOSED_TO]->(Risk: 가뭄)`
  3. `(Organization: A기업)-[:IMPLEMENTS]->(Action: 물 재사용 시설 설치)`
  4. `(Action: 물 재사용 시설 설치)-[:MITIGATES]->(Risk: 가뭄)`

## 5. 온톨로지 규칙 준수
- **노드 타입:** 
   - Organization: 기업/조직
   - Location: 사업장 위치
   - Risk: 물리적/이행 리스크 (TNFD 분류: Acute, Chronic, Transition)
   - Action: 완화 조치 및 전략 (TNFD 분류: Avoid, Reduce, Restore, Regenerate)
- **관계 타입:** 
   - OPERATES_IN: Organization -> Location
   - EXPOSED_TO: Location -> Risk (또는 Organization -> Risk)
   - IMPLEMENTS: Organization -> Action  
   - MITIGATES: Action -> Risk
   - GENERATES: Action/Organization -> Risk (Driver 생성)
   - ALTERS: Risk(Driver) -> Location(State)
   - CREATES: Risk(State) -> Risk(Financial)
   - LOCATED_IN: Location -> Location
"""

# ============ Few-shot 예시 ============
FEW_SHOT_EXAMPLES = """
## 예시 1
입력 텍스트:
"Samsung Electronics has established a water recycling facility at its Vietnam plant to mitigate the risk of drought impacting production."

출력:
```json
{
  "nodes": [
    {"name": "Samsung Electronics", "type": "Organization"},
    {"name": "Vietnam Plant", "type": "Location", "country": "Vietnam"},
    {"name": "Water Recycling Facility", "type": "Action", "action_type": "Reduce"},
    {"name": "Drought", "type": "Risk", "category": "Chronic"}
  ],
  "relationships": [
    {"source": "Samsung Electronics", "relation": "OPERATES_IN", "target": "Vietnam Plant"},
    {"source": "Vietnam Plant", "relation": "EXPOSED_TO", "target": "Drought"},
    {"source": "Samsung Electronics", "relation": "IMPLEMENTS", "target": "Water Recycling Facility"},
    {"source": "Water Recycling Facility", "relation": "MITIGATES", "target": "Drought"}
  ]
}
```

## 예시 2
입력 텍스트:
"Our excessive groundwater extraction in the region has led to land subsidence, creating physical risks for our infrastructure."

출력:
```json
{
  "nodes": [
    {"name": "Groundwater Extraction", "type": "Action", "action_type": "Reduce", "description": "Excessive extraction activity"},
    {"name": "Land Subsidence", "type": "Risk", "category": "Chronic", "description": "State of nature change"},
    {"name": "Infrastructure Damage", "type": "Risk", "category": "Acute", "description": "Physical risk to assets"}
  ],
  "relationships": [
    {"source": "Groundwater Extraction", "relation": "GENERATES", "target": "Land Subsidence"},
    {"source": "Land Subsidence", "relation": "CREATES", "target": "Infrastructure Damage"}
  ]
}
```
"""

# ============ 추출 프롬프트 템플릿 ============
EXTRACTION_PROMPT_TEMPLATE = """
{system_prompt}

{few_shot_examples}

---

## 작업
다음 텍스트를 분석하여 엔티티(노드)와 관계를 JSON 형식으로 추출하세요.

### 입력 텍스트:
{text}

### 출력 형식:
```json
{{
  "nodes": [
    {{"name": "...", "type": "Organization|Location|Risk|Action", ...추가속성}},
    ...
  ],
  "relationships": [
    {{"source": "노드이름1", "relation": "관계타입", "target": "노드이름2"}},
    ...
  ]
}}
```

노드와 관계만 JSON 형식으로 출력하세요. 다른 설명은 포함하지 마세요.
"""


def build_extraction_prompt(text: str, include_few_shot: bool = True) -> str:
    """
    Triple 추출을 위한 완성된 프롬프트를 생성합니다.
    
    Args:
        text: 분석할 텍스트
        include_few_shot: Few-shot 예시 포함 여부
        
    Returns:
        완성된 프롬프트 문자열
    """
    return EXTRACTION_PROMPT_TEMPLATE.format(
        system_prompt=SYSTEM_PROMPT,
        few_shot_examples=FEW_SHOT_EXAMPLES if include_few_shot else "",
        text=text
    )


# ============ JSON 파싱 프롬프트 (오류 복구용) ============
JSON_REPAIR_PROMPT = """
다음 텍스트에서 JSON 부분만 추출하여 올바른 JSON 형식으로 수정하세요.
```
{malformed_json}
```

수정된 JSON만 출력하세요.
"""


if __name__ == "__main__":
    # 프롬프트 예시 출력
    sample_text = "Our company faces water stress risks in Vietnam operations."
    prompt = build_extraction_prompt(sample_text)
    print("=== 생성된 프롬프트 ===")
    print(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
