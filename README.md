# AI2-THOR (iTHOR) 설치 및 동작 테스트

Ubuntu 22.04에서 AI2-THOR의 iTHOR 환경을 Python으로 실행하고,
`FloorPlan1` 장면에서 에이전트를 이동시키는 간단한 테스트를 수행합니다.

## 환경

- OS: Ubuntu 22.04.5 LTS (x86_64)
- CPU: Intel Core i5-12400F
- GPU: NVIDIA GeForce RTX 4060 Ti
- Python: 3.10.12
- ai2thor: 5.0.0

## 프로젝트 구조

```
ai2thor-test/
├── scripts/        # 학습용 튜토리얼 스크립트 (실행 대상)
│   ├── 2_render_basic_room.py   기본 방 렌더링
│   ├── 3_swap_furniture.py      가구 조작/스위칭
│   ├── 4_custom_room.py         커스텀 방 만들기(Procedural, ⚠️ 미완성)
│   ├── 5_explore_and_interact.py  WASD + 마우스로 직접 돌아다니기 (OpenCV 창)
│   ├── 6_robot_view.py          방에 로봇 N대 소환 → 탑뷰 + 로봇별 1인칭 창
│   ├── 7_arrange_then_robots.py  탑뷰에서 가구 배치 편집 → 완료 후 그 배치로 로봇 조종
│   ├── interactive_ai2thor.py   ai2thor 내장 interact 모드
│   └── test_ai2thor.py          설치 동작 확인
├── experiments/    # 일회성 탐색 스크립트(probe*) — 보관용, 재실행 불필요
├── outputs/        # 스크립트가 생성하는 PNG 결과물
├── logs/           # 과거 실행 로그
├── data/           # materials.json (유효 재질명 목록)
├── tools/          # check_after_reboot.sh, set_kernel_124.sh
├── docs/           # STATUS.md (작업 인수인계 메모)
└── .venv/          # 가상환경
```

> 모든 스크립트는 결과물을 자동으로 `outputs/` 에 저장한다(실행 위치 무관).

## 1. 설치 방법

### 시스템 패키지 (최초 1회, sudo 필요)

가상환경 생성과 OpenGL 진단에 필요합니다.

```bash
sudo apt update
sudo apt install -y python3.10-venv python3-pip mesa-utils
```

Unity 빌드 실행에 필요한 그래픽 라이브러리(`libvulkan1`, `libgl1`,
`libglu1-mesa`, `libxrandr2`, `libnss3` 등)는 이미 설치되어 있었습니다.

### 가상환경 생성 및 패키지 설치

```bash
cd ~/ai2thor-test
python3.10 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install ai2thor
# 또는 고정 버전:  .venv/bin/python -m pip install -r requirements.txt
```

> 최초 실행 시 Unity 빌드(`thor-Linux64-*.zip`, 약 769MB)가
> `~/.ai2thor/releases/` 아래로 자동 다운로드됩니다.

## 2. 가상환경 활성화 방법

```bash
cd ~/ai2thor-test
source .venv/bin/activate      # 활성화
# ... 작업 ...
deactivate                     # 비활성화
```

활성화하지 않고 `.venv/bin/python ...` 으로 직접 실행해도 됩니다.

## 3. 실행 명령

```bash
cd ~/ai2thor-test
source .venv/bin/activate
python scripts/test_ai2thor.py
```

## 4. 생성되는 이미지 파일 (모두 `outputs/` 에 저장)

| 파일 | 설명 |
|------|------|
| `outputs/initial_frame.png` | Controller 실행 직후, 에이전트 시점의 초기 RGB 프레임 (800x600) |
| `outputs/moved_frame.png`   | `MoveAhead` 1회 실행 후의 RGB 프레임 (800x600) |

두 이미지를 비교하면 에이전트가 앞으로 이동한 결과가 반영된 것을 볼 수 있습니다.

## 5. 자주 발생하는 오류와 해결 방법

### `ensurepip is not available` (venv 생성 실패)
- 원인: `python3.10-venv` 패키지 누락
- 해결: `sudo apt install -y python3.10-venv`

### `ModuleNotFoundError: No module named 'pip'`
- 원인: 시스템 Python에 pip 없음
- 해결: 가상환경 내부에서 작업하거나 `sudo apt install -y python3-pip`

### 화면이 검게 나오거나 Controller가 멈춤 / `Unable to open X display`
- 원인: `DISPLAY` 환경변수 누락 또는 X 서버 미접속
- 해결:
  ```bash
  echo $DISPLAY          # 비어 있으면 :0 등으로 지정
  export DISPLAY=:0
  ```
- 데스크톱 세션 없이(헤드리스 서버) 실행해야 하면 가상 디스플레이를 사용:
  ```bash
  sudo apt install -y xvfb
  xvfb-run -a -s "-screen 0 1024x768x24" python test_ai2thor.py
  ```

### OpenGL / 드라이버 관련 느린 렌더링
- 현재 렌더러 확인: `DISPLAY=:0 glxinfo | grep "OpenGL renderer"`
- `NV1xx`(nouveau) 또는 `llvmpipe`(소프트웨어)로 나오면 NVIDIA 독점 드라이버
  설치를 권장합니다 (아래 참고).

### Vulkan / CloudRendering(헤드리스 GPU 렌더링) 사용 시
- NVIDIA 독점 드라이버 설치 후 다음처럼 디스플레이 없이 실행 가능:
  ```python
  from ai2thor.controller import Controller
  from ai2thor.platform import CloudRendering
  controller = Controller(scene="FloorPlan1", platform=CloudRendering,
                          width=800, height=600)
  ```

## 6. NVIDIA 독점 드라이버 설치 (권장, 별도 터미널 + 재부팅 필요)

RTX 4060 Ti(Ada Lovelace)는 nouveau로도 동작하지만, 성능·안정성을 위해
독점 드라이버를 권장합니다. `sudo`는 암호 입력이 필요하므로 일반 터미널에서:

```bash
sudo ubuntu-drivers install          # 권장 드라이버(nvidia-driver-595-open) 자동 설치
sudo reboot                          # 재부팅 후 nouveau -> nvidia 전환
```

재부팅 후 확인:

```bash
nvidia-smi                           # GPU/드라이버 상태 표시되면 성공
```
