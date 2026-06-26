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

## 2. 1·2단계 — 계획 생성 + 코드 변환

> 모델은 `--gpt-version` 하나로 선택. 이름에 **`gpt` 있으면 OpenAI 클라우드(유료)**,
> 없으면(`llama...`) **로컬 Ollama(무료)** 로 자동 라우팅 (`scripts/llm_backends.py`).
> 사용 가능한 floor plan: `6, 15, 21, 201, 209, 303, 414`
> 결과: `logs/<task이름>_plans_<타임스탬프>/` 폴더들 생성

### 2-A. GPT 버전 (유료, OpenAI)
```bash
# 1단계 계획 생성
python scripts/pddlrun_llmseparate.py --floor-plan 6 --gpt-version gpt-4o
# 2단계 코드 변환
python scripts/plantocode.py --logs-dir ./logs --validate-code --gpt-version gpt-4o
```
- 키 필요: `~/ai2thor-test/LaMMA-P/api_key.txt`
- 더 저렴하게: `--gpt-version gpt-3.5-turbo` (품질↓)

### 2-B. Llama-3.1-8B 버전 (무료, 로컬 Ollama)
논문(LaMMA-P)은 GPT-4o / Llama-3.1-8B / Llama-2-13B 로 평가됨.

> ⚠️ Q4_K_M(4-bit, ~4.9GB)은 형식 준수력이 부족해 PDDL 생성 단계를 통과 못 함(검증됨).
> **q8_0(8-bit, ~8.5GB)을 사용** — 8GB VRAM엔 빠듯해 일부 CPU offload(느려짐)되지만 형식 준수력↑.

**최초 1회 셋업:**
```bash
curl -fsSL https://ollama.com/install.sh | sh        # Ollama 설치 (이미 했으면 생략)
ollama serve &                                       # 서버 실행(백그라운드)
ollama pull llama3.1:8b-instruct-q8_0                 # 모델 받기 (~8.5GB)
```
**실행:**
```bash
# 1단계 계획 생성
python scripts/pddlrun_llmseparate.py --floor-plan 6 --gpt-version llama3.1:8b-instruct-q8_0
# 2단계 코드 변환
python scripts/plantocode.py --logs-dir ./logs --validate-code --gpt-version llama3.1:8b-instruct-q8_0
```
- **API 과금 0원.** OpenAI 키 없어도 됨.
- 환경변수 조정: `LLAMA_BASE_URL`(기본 `http://localhost:11434/v1`), `LLAMA_MODEL`, `LLAMA_API_KEY`(기본 `ollama`).
- 다른 모델: `--gpt-version llama2:13b` 등 (`ollama pull` 먼저).
- q8_0도 8B라 추론력 한계는 여전 → 생성은 통과해도 GPT-4o보다 점수는 낮을 수 있음. 그래도 실패 시 "8B 로컬 한계"가 정당한 비교 결론.

## 4. 3단계 — THOR에서 로봇 실행 (무료)
```bash
ls logs/                                              # 폴더 이름 확인
python scripts/execute_plan.py --command "<폴더이름>"
```

### 현재 생성돼 있는 FloorPlan6 task (바로 3단계 가능, 무료)
폴더 이름 규칙: `_gpt4o`(GPT-4o 생성) / `_llama3`(Llama-3.1-8B fp16 생성).

**GPT-4o 단일 task 3개:**
```bash
python scripts/execute_plan.py --command "Throw_the_Spatula_gpt4o"
python scripts/execute_plan.py --command "Slice_the_tomato_gpt4o"
python scripts/execute_plan.py --command "Wash_the_lettuce_gpt4o"
```

**GPT-4o 2-로봇 병렬 복합 task:**
robot1=주걱 버리기, robot2=양상추 씻고 조리대에 놓기 → `threading`으로 동시 실행.
검증 결과: TC=1, GCR=1.0, Exec=1.0 (두 목표 모두 달성).
```bash
python scripts/execute_plan.py --command "multi_throw_wash_gpt4o"
```

**Llama-3.1-8B(fp16) 생성 — 참고용:**
fp16는 코드 생성까지는 됐으나 결함(slice 미구현·`join()` 누락 등)으로 그대로는 실행 실패.
Slice는 산문 제거 후 실행 가능하나 슬라이스 동작은 안 됨. Throw는 1단계에서 생성 실패(log.txt 없음).
```bash
python scripts/execute_plan.py --command "Slice_the_tomato_llama3"   # 산문제거 완료, 단 SliceObject 미사용
# Wash_the_lettuce_llama3 / Throw_the_Spatula_llama3 (Throw는 log.txt 없어 실행불가)
```

### 여러 개 한 번에
**순차 (권장 — 하나 끝나면 다음):**
```bash
for d in "Throw_the_Spatula_gpt4o" "Slice_the_tomato_gpt4o" "Wash_the_lettuce_gpt4o"; do
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

## 6. 성능 평가 — GPT vs Llama (LaMMA-P 논문 지표)

### 지표 (3단계 실행 끝에 자동 출력됨)
`execute_plan.py` 가 끝나면 마지막 줄에 이렇게 찍힌다 (계산: `data/aithor_connect/end_thread.py`):
```
SR:1, TC:1, GCR:1.0, Exec:0.875, RU:1
```
| 지표 | 의미 | 계산 |
|------|------|------|
| **SR** (Success Rate) | 최종 성공 여부(0/1). TC와 RU 둘 다 1일 때만 1 | 종합 |
| **TC** (Task Completion) | 목표 상태 전부 달성(GCR==1.0)이면 1 | goal 달성 |
| **GCR** (Goal Condition Recall) | 목표 조건 중 달성 비율 (예: Tomato가 SLICED 됐나) | 달성/전체 |
| **Exec** (Executability) | 시도한 액션 중 성공 비율 | 성공액션/전체액션 |
| **RU** (Resource Utilization) | 로봇/전환 자원을 효율적으로 썼나 | 전환 수 기반 |

→ **모델 품질(GPT vs Llama)은 "그 모델이 만든 플랜이 실제로 목표를 달성하느냐"로 드러난다.** Llama가 플랜 포맷을 깨거나 엉뚱한 객체를 고르면 GCR·TC·SR이 떨어진다.

### 평가 절차 (동일 task 집합으로 두 모델 비교)
1. **GPT로 플랜 생성** → 각 task 실행 → 지표 기록
2. **Llama로 플랜 생성** → 각 task 실행 → 지표 기록
3. task별 SR/TC/GCR/Exec/RU 를 **평균**내서 표로 비교

지표 줄만 뽑아 파일로 모으기 (실행 로그를 tee 후 grep):
```bash
# 예: Llama로 생성된 폴더 하나 실행하며 지표 수집
python scripts/execute_plan.py --command "<폴더>" 2>&1 \
  | tee /tmp/run.log | grep -E "^SR:" >> results_llama.csv

# GPT 폴더들도 동일하게 results_gpt.csv 에 모음
```
- 같은 task를 GPT/Llama 각각으로 1·2단계 돌리면 폴더 이름의 타임스탬프가 달라지니, 어느 폴더가 어느 모델인지 메모해둘 것 (또는 모델별로 따로 실행).
- 로봇 위치가 랜덤이라(§참고) **task당 3~5회 반복 후 평균**내야 공정한 비교가 된다.

### 자동 평가 하니스 — `scripts/eval_models.py`
실행·반복·파싱·집계를 자동화. **유료 생성단계(1·2단계)는 건드리지 않고, 미리 만들어둔 폴더를 실행만** 한다.
무한루프(로봇 막힘) 대비 타임아웃 내장 — 안 끝나면 그 run 은 실패(지표 0)로 기록.

```bash
# 1) GPT-4o 폴더들 평가 (각 3회 반복)
python scripts/eval_models.py --model gpt4o --runs 3 \
  "Slice_the_tomato_gpt4o" "Throw_the_Spatula_gpt4o" "Wash_the_lettuce_gpt4o"

# 2) Llama3 폴더들 평가 (각 3회 반복) — fp16는 실행 결함으로 대부분 실패 기록될 것
python scripts/eval_models.py --model llama3 --runs 3 \
  "Slice_the_tomato_llama3" "Wash_the_lettuce_llama3"

# 3) 누적 결과로 모델 비교표 출력
python scripts/eval_models.py --summarize
```
- 결과는 `eval_results.csv` 에 누적(model, command, run, status, SR/TC/GCR/Exec/RU).
- `--timeout`(기본 600초), `--out`(CSV 경로) 옵션.
- 출력 예:
  ```
  | model        | runs | 정상종료 |    SR |    TC |   GCR |  Exec |    RU |
  | gpt          |    9 |      9 | 1.000 | 1.000 | 1.000 | 0.950 | 1.000 |
  | llama3.1:8b  |    9 |      7 | 0.667 | 0.667 | 0.778 | 0.620 | 0.667 |
  ```
- ⚠️ GPT/Llama 플랜은 **모델별로 따로 1·2단계를 돌려** 폴더를 만들어 두고(타임스탬프로 구분), 어느 폴더가 어느 모델인지 기록해 둘 것.

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
