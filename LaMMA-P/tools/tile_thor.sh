#!/usr/bin/env bash
# AI2-THOR 창을 화면에 격자로 자동 정렬/리사이즈 (X11 + wmctrl).
#
# 사용법:
#   tools/tile_thor.sh                # "thor" 패턴 창들을 격자 정렬
#   tools/tile_thor.sh unity          # 다른 패턴으로 매칭
#   tools/tile_thor.sh thor --watch   # 창이 뜰 때까지 기다렸다가 정렬
#
# 창 이름을 모르면:  wmctrl -l  로 현재 창 목록 보고 패턴을 넘기면 됨.
set -uo pipefail

PATTERN="${1:-thor}"
WATCH="${2:-}"

command -v wmctrl >/dev/null || { echo "wmctrl 필요:  sudo apt install -y wmctrl"; exit 1; }

# 화면 크기 (primary 모니터)
read SW SH < <(xrandr 2>/dev/null | awk '/ connected primary/{split($4,a,"+");split(a[1],b,"x");print b[1],b[2];exit}')
SW=${SW:-1920}; SH=${SH:-1080}
TOP=40                       # GNOME 상단바 여유
USABLE_H=$((SH - TOP))

find_ids() { wmctrl -l | grep -iE "$PATTERN" | awk '{print $1}'; }

# --watch: 창이 나타날 때까지 대기
if [ "$WATCH" = "--watch" ]; then
  echo "'$PATTERN' 창이 뜨길 기다리는 중... (Ctrl+C로 중단)"
  while [ -z "$(find_ids)" ]; do sleep 1; done
  sleep 1   # 창이 완전히 뜨도록 잠깐
fi

mapfile -t IDS < <(find_ids)
N=${#IDS[@]}
if [ "$N" -eq 0 ]; then
  echo "'$PATTERN' 패턴에 맞는 창 없음. 현재 떠있는 창:"
  wmctrl -l
  exit 1
fi

# 격자 계산 (정사각형에 가깝게)
COLS=$(python3 -c "import math;print(math.ceil(math.sqrt($N)))")
ROWS=$(python3 -c "import math;print(-(-$N//$COLS))")
CW=$((SW / COLS)); CH=$((USABLE_H / ROWS))

i=0
for id in "${IDS[@]}"; do
  r=$((i / COLS)); c=$((i % COLS))
  X=$((c * CW)); Y=$((TOP + r * CH))
  wmctrl -i -r "$id" -b remove,maximized_vert,maximized_horz 2>/dev/null
  wmctrl -i -r "$id" -e "0,$X,$Y,$((CW-8)),$((CH-8))"
  title=$(wmctrl -l | grep "^$id" | cut -d' ' -f5-)
  echo "  정렬: $id  ${CW}x${CH} @($X,$Y)  ($title)"
  i=$((i+1))
done
echo "완료: $N개 창을 ${COLS}x${ROWS} 격자로 정렬"
