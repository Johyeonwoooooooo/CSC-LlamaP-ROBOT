"""[6] 방에 로봇을 불러와서 '탑뷰 + 로봇별 1인칭'을 창 여러 개로 보기.

FloorPlan1(2번 방)에 로봇을 N대 띄우고, OpenCV 창을 여러 개 연다:
  - "TopDown"        : 방 전체를 위에서 내려다보는 창 1개
  - "Robot 0", "1".. : 로봇 수만큼, 각 로봇의 1인칭 시점 창

키보드로 '조종 중인 로봇'을 골라(숫자 0~9) 돌아다닐 수 있다. 탑뷰에는 항상
모든 로봇의 움직임이 반영된다.

─ 조작 ────────────────────────────────
   0 ~ 9   : 조종할 로봇 선택 (로봇 번호)
   w / s   : 앞으로 / 뒤로
   a / d   : 왼쪽 / 오른쪽 게걸음
   q / e   : 왼쪽 / 오른쪽 회전
   r / f   : 시선 위 / 아래
   x / ESC : 종료

─ 로봇 모델 (명령줄 인자) ───────────────
   python scripts/6_robot_view.py [모델] [로봇수]
   예) python scripts/6_robot_view.py locobot 2
       python scripts/6_robot_view.py stretch 1
   모델: locobot | stretch    (기본값: locobot 2대)

※ AI2-THOR 제약: agentMode(로봇 종류)는 Controller 당 하나라서, 한 방에
  LoCoBot 과 Stretch 를 '동시에' 띄울 수는 없다. 두 모델을 다 보려면 인자를
  바꿔 두 번 실행하면 된다. (원하면 두 터미널에서 각각 실행해 나란히 비교)
"""

import os
import sys
import math
import traceback

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ai2thor.controller import Controller


SCENE = "FloorPlan1"
W, H = 500, 400                 # 각 창 해상도
VALID_MODELS = ("locobot", "stretch", "default")

# 한글 라벨용 폰트 — OpenCV 내장 폰트는 한글을 못 그린다(네모로 깨짐).
_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
try:
    _FONT = ImageFont.truetype(_FONT_PATH, 18)
except Exception:
    _FONT = None


def label(frame_bgr, text, color_bgr=(0, 255, 0)):
    """frame 좌상단에 검은 배경 + 한글 텍스트를 얹는다."""
    h, w = frame_bgr.shape[:2]
    cv2.rectangle(frame_bgr, (0, 0), (w, 26), (0, 0, 0), -1)
    if _FONT is None:                          # 폰트 없으면 영문 폴백
        cv2.putText(frame_bgr, text, (8, 18), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, color_bgr, 1, cv2.LINE_AA)
        return frame_bgr
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    b, g, r = color_bgr
    d.text((8, 3), text, font=_FONT, fill=(r, g, b))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def spread_robots(c, count):
    """로봇들이 겹치지 않도록 갈 수 있는 좌표에 고루 흩어 놓는다."""
    if count < 2:
        return
    pts = c.step(action="GetReachablePositions").metadata["actionReturn"]
    if not pts:
        return
    pts = sorted(pts, key=lambda p: (p["x"], p["z"]))
    for i in range(count):
        p = pts[(i * len(pts)) // count]       # 균등 간격으로 하나씩
        c.step(action="TeleportFull", agentId=i,
               position={"x": p["x"], "y": p["y"], "z": p["z"]},
               rotation={"x": 0, "y": (i * 90) % 360, "z": 0},
               horizon=0, forceAction=True)


def add_topdown_camera(c):
    cam = c.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
    c.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)


def render(c, model, active, busy=False):
    """탑뷰 + 각 로봇 1인칭을 해당 창에 그린다."""
    le = c.last_event
    # 탑뷰 프레임 위치:
    #  - third-party 프레임은 events[0].third_party_camera_frames 에 모인다(단일/멀티 공통).
    #  - Stretch 등 일부 로봇은 '내장 보조 카메라'가 앞쪽 인덱스를 차지하므로,
    #    내가 마지막에 추가한 맵뷰 카메라는 항상 [-1] 이다. (그래서 [0] 아님)
    td_frames = le.events[0].third_party_camera_frames if le.events else le.third_party_camera_frames
    if td_frames:
        td = cv2.cvtColor(td_frames[-1], cv2.COLOR_RGB2BGR)
        td = label(td, f"전체 방 탑뷰  ·  로봇 {len(le.events)}대  ·  모델: {model}")
        cv2.imshow("TopDown", td)
    # 각 로봇 1인칭
    for i, e in enumerate(le.events):
        f = cv2.cvtColor(e.frame, cv2.COLOR_RGB2BGR)
        tag = f"로봇 {i} 시점" + ("   ◀ 조종 중" if i == active else "")
        color = (0, 220, 255) if i == active else (200, 200, 200)
        cv2.imshow(f"Robot {i}", label(f, tag, color))


# 키 -> (액션, 추가인자)
MOVES = {
    ord('w'): ("MoveAhead", {}),
    ord('s'): ("MoveBack", {}),
    ord('a'): ("MoveLeft", {}),
    ord('d'): ("MoveRight", {}),
    ord('q'): ("RotateLeft", {"degrees": 30}),
    ord('e'): ("RotateRight", {"degrees": 30}),
    ord('r'): ("LookUp", {"degrees": 15}),
    ord('f'): ("LookDown", {"degrees": 15}),
}


def parse_args():
    model = sys.argv[1] if len(sys.argv) > 1 else "locobot"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    if model not in VALID_MODELS:
        print(f"[경고] 알 수 없는 모델 '{model}' -> locobot 으로 진행. (가능: {VALID_MODELS})")
        model = "locobot"
    return model, max(1, min(count, 5))


def run_control_loop(controller, model, count):
    """이미 셋업된 controller(로봇 배치 + 탑뷰 카메라 완료)로 창을 띄우고
    로봇 조종 루프를 실행한다. controller 의 생성/종료(stop)는 호출자가 책임진다.
    (스크립트 7번이 '가구 배치 후 로봇 조종'에서 이 함수를 재사용한다.)"""
    cv2.namedWindow("TopDown", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("TopDown", W, H)
    cv2.moveWindow("TopDown", 10, 10)
    for i in range(count):
        name = f"Robot {i}"
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(name, W, H)
        cv2.moveWindow(name, 30 + (i + 1) * (W + 15), 10)

    active = 0
    render(controller, model, active)

    while True:
        key = cv2.waitKey(30) & 0xFF

        if cv2.getWindowProperty("TopDown", cv2.WND_PROP_VISIBLE) < 1:
            break
        if key == 255:                      # 입력 없음 — 창만 유지
            continue
        if key in (ord('x'), 27):
            break

        if ord('0') <= key <= ord('9'):     # 로봇 선택
            sel = key - ord('0')
            if sel < count:
                active = sel
                print(f"[선택] 로봇 {active} 조종 중")
            else:
                print(f"[무시] 로봇 {sel} 없음 (0~{count-1})")
            render(controller, model, active)
            continue

        if key in MOVES:
            action, kw = MOVES[key]
            ev = controller.step(action=action, agentId=active, **kw)
            if not ev.metadata["lastActionSuccess"]:
                print(f"[로봇 {active}] {action} 실패: {ev.metadata.get('errorMessage','')[:50]}")
            render(controller, model, active)

    cv2.destroyAllWindows()


def main():
    model, count = parse_args()
    print(f"=== 로봇 불러오기: 모델={model}, {count}대, 장면={SCENE} ===")
    print("창에 포커스를 두고 조작하세요. 숫자키로 로봇 선택, wasd 이동, qe 회전, rf 시선, x 종료.")

    controller = Controller(scene=SCENE, width=W, height=H,
                            agentMode=model, agentCount=count,
                            gridSize=0.25, server_timeout=600.0)
    try:
        spread_robots(controller, count)
        add_topdown_camera(controller)
        run_control_loop(controller, model, count)
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        controller.stop()
        print("[종료] controller.stop()")


if __name__ == "__main__":
    sys.exit(main())
