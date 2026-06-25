#!/usr/bin/env bash
# 재부팅 후 이 한 줄만 실행해서 결과를 Claude 에게 붙여주면 바로 상황 파악됨:
#     bash ~/ai2thor-test/check_after_reboot.sh
# (sudo 불필요)

echo "================ AI2-THOR 재부팅 후 상태 점검 ================"
echo "[날짜] $(date)"
echo

echo "## 1. 커널 (기대값: 6.8.0-124-generic)"
echo "  현재 커널: $(uname -r)"
echo

echo "## 2. NVIDIA GPU (기대: RTX 4060 Ti 표가 뜨면 성공)"
if nvidia-smi >/tmp/_nvsmi 2>&1; then
  grep -E "Driver Version|4060|NVIDIA-SMI" /tmp/_nvsmi | head -3 | sed 's/^/  /'
  echo "  => GPU 정상 (OK)"
else
  echo "  => nvidia-smi 실패:"; sed 's/^/     /' /tmp/_nvsmi | head -2
  echo "  => 아직 소프트웨어 렌더링 상태 (GRUB 124 적용/재부팅 확인 필요)"
fi
echo

echo "## 3. OpenGL 렌더러 (NVIDIA 면 성공 / llvmpipe 면 아직 소프트웨어)"
echo "  $(glxinfo 2>/dev/null | grep -i 'OpenGL renderer' || echo '(glxinfo 없음)')"
echo

echo "## 4. nvidia 커널 모듈 로드 여부"
if lsmod | grep -q '^nvidia'; then echo "  nvidia 모듈 로드됨 (OK)"; else echo "  nvidia 모듈 미로드"; fi
echo

echo "## 5. GRUB 기본 커널 설정"
grep '^GRUB_DEFAULT=' /etc/default/grub 2>/dev/null | sed 's/^/  /'
echo

echo "## 6. ai2thor venv / 패키지"
~/ai2thor-test/.venv/bin/python -c "import ai2thor; print('  ai2thor', ai2thor.__version__)" 2>/dev/null || echo "  ai2thor import 실패"
echo

echo "## 7. 프로젝트 스크립트 목록 (scripts/)"
ls -1 ~/ai2thor-test/scripts/*.py 2>/dev/null | sed 's/^/  /'
echo
echo "================ 점검 끝. 위 내용을 Claude 에게 붙여주세요 ================"
