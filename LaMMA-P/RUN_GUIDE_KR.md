# LaMMA-P 실행 가이드 (이 PC 전용 정리)

> 이 PC(ai2thor-test, RTX 4060 Ti)에서 실제로 동작하는 명령어 모음.
> 원본 영어 설치문서는 `README.md` 참고. 여기는 우리 환경(venv·수정사항·비용) 기준.

## 0. 핵심 개념 & 비용
3단계 파이프라인:
| 단계 | 스크립트 | LLM(GPT-4o) | 비용 |
|------|----------|------------|------|
| 1. 계획 생성 | `pddlrun_llmseparate.py` | ✅ 사용 | **유료** (~$0.3~1.0/floorplan) |
| 2. 코드 변환 | `plantocode.py` | ✅ 사용 | **유료** (~$0.1~0.5) |
| 3. THOR 실행 | `execute_plan.py` | ❌ 안 씀 | **무료** (몇 번이든) |

- 한 번 1·2단계로 계획을 만들어두면, 3단계는 **공짜로 무한 재생**.
- **새 task / 새 floorplan** 하면 1·2단계 다시 = 또 과금.
- 비용 폭주 방지: platform.openai.com → Settings → Limits 에서 예산 한도 설정.

## 1. 매번 준비 (새 터미널마다)
```bash
cd ~/ai2thor-test/LaMMA-P
source ~/ai2thor-test/.venv/bin/activate
```
- OpenAI 키 위치: `~/ai2thor-test/LaMMA-P/api_key.txt` (sk-... 만, 줄바꿈 없이)

## 2. 1단계 — 계획 생성 (유료)
```bash
python scripts/pddlrun_llmseparate.py --floor-plan 6
```
- 사용 가능한 floor plan: `6, 15, 21, 201, 209, 303, 414`
- 옵션: `--gpt-version gpt-3.5-turbo` (더 저렴, 품질↓)
- 결과: `logs/<task이름>_plans_<타임스탬프>/` 폴더들 생성

## 3. 2단계 — 코드 변환 (유료)
```bash
python scripts/plantocode.py --logs-dir ./logs --validate-code
```
- 각 로그 폴더에 `code_plan.py`(AI2-THOR 실행 코드) 저장

## 4. 3단계 — THOR에서 로봇 실행 (무료)
```bash
ls logs/                                              # 폴더 이름 확인
python scripts/execute_plan.py --command "<폴더이름>"
```

### 현재 생성돼 있는 FloorPlan6 task 3개 (바로 3단계 가능, 무료)
```bash
python scripts/execute_plan.py --command "Throw_the_Spatula_in_the_trash_plans_06-25-2026-19-06-40"
python scripts/execute_plan.py --command "Slice_the_tomato_plans_06-25-2026-19-06-40"
python scripts/execute_plan.py --command "Wash_the_lettuce_and_place_lettuce_on_the_Countertop_plans_06-25-2026-19-06-40"
```

### 여러 개 한 번에
**순차 (권장 — 하나 끝나면 다음):**
```bash
for d in \
  "Throw_the_Spatula_in_the_trash_plans_06-25-2026-19-06-40" \
  "Slice_the_tomato_plans_06-25-2026-19-06-40" \
  "Wash_the_lettuce_and_place_lettuce_on_the_Countertop_plans_06-25-2026-19-06-40"; do
    python scripts/execute_plan.py --command "$d"
done
```
**병렬 (창 동시에 여러 개 — 8GB GPU엔 무거움, 비권장):**
```bash
python scripts/execute_plan.py --command "<폴더1>" &
python scripts/execute_plan.py --command "<폴더2>" &
wait
```

## 5. 2대 이상 로봇이 "같이 다른 일" 하게 만들기
한 명령 안에서 여러 로봇이 병렬로 일하게 하려면 **복합 task + robot list 여러 대**로 새 task를 만든다.
task 정의 파일: `data/final_test/FloorPlan6.json` (JSONL — 한 줄 = task 하나)

task 한 줄 형식:
```json
{"task": "할 일 문장", "robot list": [1, 2], "object_states": [...], "trans": 0, "max_trans": 0}
```
- `robot list`: 참여 로봇 번호 (resources/robots.py 의 robot1~28). 1~4 = 모든 스킬.
- 복합 명령("A 하고 B 해")이면 allocator가 subtask를 쪼개 각 로봇에 병렬 할당 → 생성 코드가 `threading`으로 동시에 실행.

예시 — robot1=주걱 버리기, robot2=양상추 옮기기 (동시):
```bash
cp data/final_test/FloorPlan6.json data/final_test/FloorPlan6.json.bak   # 원본 백업
cat > data/final_test/FloorPlan6.json << 'EOF'
{"task": "Throw the Spatula in the trash and place the Lettuce on the CounterTop", "robot list": [1, 2], "object_states": [{"name": "GarbageCan", "contains": ["Spatula"], "state": "None"}, {"name": "Lettuce", "contains": [], "state": "None"}], "trans": 0, "max_trans": 0}
EOF

python scripts/pddlrun_llmseparate.py --floor-plan 6      # 1단계 (유료)
python scripts/plantocode.py --logs-dir ./logs --validate-code   # 2단계 (유료)
ls logs/
python scripts/execute_plan.py --command "<새 폴더 이름>"  # 3단계 (무료)

cp data/final_test/FloorPlan6.json.bak data/final_test/FloorPlan6.json   # 원본 3개 task 복구
```

## 6. 실행 영상 만들기 (선택)
원본 코드가 실행 끝에 ffmpeg로 영상을 만든다. ffmpeg 설치 시 자동 생성:
```bash
sudo apt install -y ffmpeg          # 최초 1회
# 이후 3단계 실행하면 아래에 영상 생성
#   data/aithor_connect/video_agent_1.mp4   (로봇1 시점)
#   data/aithor_connect/video_top_view.mp4  (위에서 본 전체)
```
ffmpeg 없어도 task 수행엔 지장 없음(마지막에 영상 단계만 에러).

## 7. 이 PC에서 적용한 수정사항 (원본과 다른 점)
- `.venv`(Python 3.10) 사용. `openai`는 **2.x**(스크립트가 신버전 API 사용). `pip install -r requirements.txt`는 하지 말 것(pathlib 백포트가 3.10 깨뜨림).
- `data/aithor_connect/aithor_connect.py`: 객체 이름 매칭을 견고화(`_norm_name`/`_match_obj`) — LLM이 만든 `'spatula_location'` 같은 이름도 실제 객체(`Spatula`)에 매칭. 매칭 실패 시 크래시 대신 스킵.
- `scripts/execute_plan.py`: 생성 코드의 `robots = [robot1]` 처럼 따옴표 없는 robots 정의도 실제 로봇 목록으로 치환(정규식). (이전엔 NameError로 크래시)
- Fast Downward는 `downward/`에 빌드 완료.
