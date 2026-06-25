# AI2-THOR 작업 현황 (재부팅 인계용)

마지막 업데이트: 2026-06-25 (재부팅 + 디렉토리 리팩토링 완료)

## ✅ GPU 문제 해결됨 (2026-06-25 재부팅 후 확인)
커널 **6.8.0-124-generic** 부팅 성공, `nvidia-smi` 에 **RTX 4060 Ti**(Driver 595.71.05) 정상,
OpenGL 렌더러도 **NVIDIA**(소프트웨어 llvmpipe 아님). 즉 더 이상 느리지 않다.
재부팅 후에는 여전히 `bash ~/ai2thor-test/tools/check_after_reboot.sh` 로 상태 재확인 가능.

---

## 지금까지 한 일

### 환경
- ai2thor **5.0.0** 가 `~/ai2thor-test/.venv` 에 설치됨. (`.venv/bin/python` 으로 실행)
- 실행: `cd ~/ai2thor-test && .venv/bin/python scripts/<스크립트>.py`
- **디렉토리 구조**: `scripts/`(튜토리얼) · `experiments/`(probe 보관) · `outputs/`(PNG) · `logs/` · `data/`(materials.json) · `tools/`(쉘) · `docs/`(이 문서). 자세한 건 루트 `README.md`.

### 만든 스크립트
| 파일 | 내용 | 상태 |
|------|------|------|
| `2_render_basic_room.py` | 기본 방(FloorPlan1) 1인칭 + top-down 렌더 → PNG | ✅ 검증됨 |
| `3_swap_furniture.py` | 가구 조작/스위칭(열기·켜기·이동·제거·랜덤재배치·방교체) | ✅ 검증됨 |
| `4_custom_room.py` | Procedural 모드로 커스텀 방 짓기 | ⚠️ 미완성 (아래 참고) |
| `5_explore_and_interact.py` | **OpenCV 창에서 WASD 이동 + 마우스 시점 + 조준점으로 가구 상호작용**. HUD 한글은 PIL+NotoSansCJK 로 렌더(cv2는 한글 못 그림) | ✅ 코드 완성 |
| `6_robot_view.py` | **로봇 N대 소환 → 탑뷰 창 + 로봇별 1인칭 창**. 숫자키로 로봇 선택, wasd/qe/rf 조종. 모델·대수는 명령줄 인자. 조종 루프는 `run_control_loop()` 로 분리(7번이 재사용) | ✅ 헤드리스 검증됨 |
| `7_arrange_then_robots.py` | **2단계 흐름: ① 탑뷰에서 가구 골라 이동·회전(투영 마커) → g → ② 그 배치로 로봇 조종(6번 재사용)**. 기본 stretch 1대 | ✅ 헤드리스 검증됨 |

조작키(5번): 이동 `w/a/s/d`, 회전 `j/l`, 시선 `i/k` / 상호작용(조준점 맞춘 뒤) 열기·닫기 `o`, 켜기·끄기 `t`, 집기·놓기 `p`, top-down 저장 `r`, 종료 `x`/ESC.

### 핵심 문제와 원인 (이번 세션의 가장 큰 이슈)
- 증상: ai2thor 창이 "응답 없음"으로 느림. **코드 버그 아님.**
- 원인: **NVIDIA 드라이버 미작동 → 소프트웨어 렌더링(llvmpipe)** 으로 떨어져서 매우 느림.
- 더 깊은 원인: nvidia 모듈이 커널 **6.8.0-124** 에만 빌드돼 있는데, 시스템이 옛 커널 **6.8.0-117** 로 부팅돼 있었음. `GRUB_DEFAULT` 가 117 로 고정돼 있던 게 원인.
- 조치: `set_kernel_124.sh` 로 GRUB 기본값을 117→124 로 변경 (사용자가 `sudo bash`로 직접 실행) 후 재부팅 예정.
  - 변경 전 백업: `/etc/default/grub.bak`

### 4번(커스텀 방) 미완성 메모
- `CreateHouse` 의 재질 이름을 추측값(PinkTile 등)으로 넣어 `"given key was not present in the dictionary"` 실패.
- **유효한 재질 이름은 `data/materials.json` 에 확보됨** (`GetMaterials` 액션 결과). 예) 벽: `WallDrywallWhite`, `PureWhite`, `BrownDrywall` / 바닥: `BedroomFloor1`, `DarkWoodFloors`, `Carpet1` / 천장: `WallDrywallWhite`.
- 남은 작업: `4_custom_room.py` 의 재질 이름을 유효값으로 교체 후 재실행 검증.
- `GetHouseFromTemplate` 경로는 이 빌드에서 NullReference 로 깨짐 → 사용하지 말 것. `CreateHouse` 에 완성된 house dict 직접 전달 방식 사용.

### 임시 파일 (보관됨)
`experiments/probe*.py`, `experiments/smoke5.py` 와 `logs/` 의 과거 로그. 재실행 불필요.
무슨 시도였는지는 `experiments/README.md` 참고. (`data/materials.json` 은 4번 완성에 필요하니 보존)

## 다음 단계 우선순위
1. ~~재부팅 → GPU 정상 확인~~ ✅ 완료.
2. **`scripts/5_explore_and_interact.py` WASD 동작 테스트** (GPU 살아났으니 빠를 것).
3. `scripts/4_custom_room.py` 재질 이름 고쳐 커스텀 방 완성.
