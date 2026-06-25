# experiments/ — 일회성 탐색 스크립트 (보관용)

지난 세션에 `4_custom_room.py`(Procedural 커스텀 방)를 만들다가 막힌 부분을
이것저것 찔러보며(probe) 알아내던 임시 스크립트들이다. **튜토리얼 본편이 아니며,
다시 실행할 필요는 없다.** 무슨 시도였는지 기록으로만 남긴다.

| 파일 | 무엇을 시도했나 | 결과 |
|------|----------------|------|
| `probe.py`  | `GetHouseFromTemplate` 로 완성된 house dict 받기 | NullReference 실패 → 이 빌드에선 못 씀 |
| `probe2.py` | 손으로 만든 최소 house dict 로 `CreateHouse` | 재질명 추측 → "key not present" 실패 |
| `probe3.py` | base_house 복제 후 변형 시도 | 〃 |
| `probe4.py` | 템플릿 dict 구조 뜯어보기 | 구조 파악 |
| `probe5.py` | room key / id 조합 바꿔가며 시도 | 〃 |
| `probe6.py` | 어떤 액션이 먹는지 하나씩 try | 가능 액션 탐색 |
| `probe7.py` | `GetMaterials` 로 **유효한 재질명 목록 추출** | ✅ 성공 → `data/materials.json` 생성 |
| `smoke5.py` | `5_explore_and_interact.py` 헬퍼 비대화식 스모크 테스트 | 동작 확인용 |

핵심 결론: 유효한 재질명은 `data/materials.json` 에 있고,
`GetHouseFromTemplate` 는 피하고 `CreateHouse` 에 전체 house dict 를 넘겨야 한다.
(자세한 내용은 `docs/STATUS.md`)
