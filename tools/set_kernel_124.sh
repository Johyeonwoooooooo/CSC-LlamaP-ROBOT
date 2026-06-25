#!/usr/bin/env bash
# 다음 부팅부터 커널 6.8.0-124-generic 으로 부팅되도록 GRUB 기본값을 변경한다.
# (124 커널엔 NVIDIA 모듈이 빌드돼 있어 GPU가 살아난다)
# 사용법:  sudo bash set_kernel_124.sh
set -e

GRUB=/etc/default/grub

echo "[1/4] 현재 GRUB_DEFAULT:"
grep '^GRUB_DEFAULT=' "$GRUB"

echo "[2/4] 백업 생성: ${GRUB}.bak"
cp -a "$GRUB" "${GRUB}.bak"

echo "[3/4] 117 -> 124 로 교체"
sed -i 's/gnulinux-6\.8\.0-117-generic-advanced/gnulinux-6.8.0-124-generic-advanced/g' "$GRUB"
echo "  변경 후 GRUB_DEFAULT:"
grep '^GRUB_DEFAULT=' "$GRUB"

echo "[4/4] update-grub 실행"
update-grub

echo
echo "=== 확인: grub.cfg 가 잡은 default ==="
grep -E '^set default' /boot/grub/grub.cfg || true
echo
echo "완료. 이제 재부팅하면 6.8.0-124-generic 으로 부팅됩니다."
echo "재부팅 후:  uname -r  →  6.8.0-124-generic ,   nvidia-smi  →  RTX 4060 Ti 표시되면 성공."
