"""
Triple 추출을 위한 Few-shot 프롬프트 정의

NatureKG 논문과 TNFD 가이드라인을 기반으로 한 프롬프트를 정의합니다.
LLM이 텍스트에서 (Subject, Predicate, Object) 형태의 Triple을 추출하도록 안내합니다.
"""

# ============ 시스템 프롬프트 ============
SYSTEM_PROMPT = """당신은 TNFD(자연 관련 재무 정보 공개) 전문가입니다.
기업의 지속가능성 보고서 텍스트를 분석하여 Knowledge Graph에 적합한 
엔티티(노드)와 관계(엣지)를 추출하는 것이 당신의 임무입니다.

## 규칙
1. 온톨로지 스키마에 정의된 노드 타입만 사용하세요:
   - Organization: 기업/조직
   - Location: 사업장 위치
   - Risk: 물리적/이행 리스크
   - Action: 완화 조치 및 전략
   
2. 온톨로지 스키마에 정의된 관계 타입만 사용하세요:
   - OPERATES_IN: Organization -> Location
   - HAS_RISK: Organization -> Risk
   - IMPLEMENTS: Organization -> Action  
   - MITIGATES: Action -> Risk
   - LOCATED_IN: Location -> Location (지역 포함 관계)

3. 너무 일반적인 용어(예: 'Nature', 'Environment', 'Climate Change')는 
   구체적인 리스크나 자산으로 세분화하세요.
   
4. 문서에 명시적으로 언급된 정보만 추출하세요. 추론이나 가정은 하지 마세요.

5. 추출된 모든 엔티티와 관계는 원문을 근거로 해야 합니다.
"""

# ============ Few-shot 예시 ============
FEW_SHOT_EXAMPLES = """
## 예시 1
입력 텍스트:
"Samsung Electronics operates manufacturing facilities in Vietnam. The company is implementing regenerative agriculture programs to reduce soil erosion in nearby farmlands."

출력:
```json
{
  "nodes": [
    {"name": "Samsung Electronics", "type": "Organization"},
    {"name": "Vietnam Manufacturing Facility", "type": "Location", "country": "Vietnam"},
    {"name": "Regenerative Agriculture Program", "type": "Action", "action_type": "Reduce"},
    {"name": "Soil Erosion", "type": "Risk", "category": "Chronic"}
  ],
  "relationships": [
    {"source": "Samsung Electronics", "relation": "OPERATES_IN", "target": "Vietnam Manufacturing Facility"},
    {"source": "Samsung Electronics", "relation": "IMPLEMENTS", "target": "Regenerative Agriculture Program"},
    {"source": "Regenerative Agriculture Program", "relation": "MITIGATES", "target": "Soil Erosion"}
  ]
}
```

## 예시 2
입력 텍스트:
"당사는 수자원 부족 리스크에 대응하기 위해 중수도 재이용 시스템을 도입하였습니다. 이 시스템은 기흥 사업장에 설치되어 운영 중입니다."

출력:
```json
{
  "nodes": [
    {"name": "Water Recycling System", "type": "Action", "action_type": "Reduce", "status": "In Operation"},
    {"name": "Water Stress", "type": "Risk", "category": "Chronic"},
    {"name": "Giheung Site", "type": "Location", "country": "South Korea"}
  ],
  "relationships": [
    {"source": "Water Recycling System", "relation": "MITIGATES", "target": "Water Stress"},
    {"source": "Water Recycling System", "relation": "APPLIED_AT", "target": "Giheung Site"}
  ]
}
```

## 예시 3
입력 텍스트:
"Climate-related physical risks include extreme weather events such as floods and typhoons that could disrupt our supply chain operations in Southeast Asia."

출력:
```json
{
  "nodes": [
    {"name": "Flood", "type": "Risk", "category": "Acute", "description": "Supply chain disruption risk"},
    {"name": "Typhoon", "type": "Risk", "category": "Acute", "description": "Supply chain disruption risk"},
    {"name": "Southeast Asia Operations", "type": "Location"}
  ],
  "relationships": [
    {"source": "Flood", "relation": "AFFECTS", "target": "Southeast Asia Operations"},
    {"source": "Typhoon", "relation": "AFFECTS", "target": "Southeast Asia Operations"}
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
