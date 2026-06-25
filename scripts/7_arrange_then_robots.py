"""[7] 가구 배치 편집 → (완료) → 로봇 조종.  두 단계로 흐른다.

   ┌─ 1단계: 배치 편집 (탑뷰 1창) ──────────────────────────────┐
   │ 방을 위에서 내려다보며 가구를 골라 옮기고 돌린다.          │
   │ 선택한 가구는 노란 동그라미로 표시된다.                     │
   └────────────────────────────────────────────────────────────┘
              │  g (배치 완료)
              ▼
   ┌─ 2단계: 로봇 조종 (6번과 동일) ────────────────────────────┐
   │ 방금 만든 배치 그대로 로봇을 N대 불러와 조종한다.          │
   └────────────────────────────────────────────────────────────┘

─ 1단계(배치) 조작 ────────────────────────────
   n / b   : 다음 / 이전 가구 선택
   w / s   : 선택 가구를 위 / 아래로 이동 (탑뷰 기준, +z / -z)
   a / d   : 선택 가구를 왼 / 오른쪽으로 이동 (-x / +x)
   q / e   : 선택 가구 회전 (-15° / +15°)
   z       : 선택 가구를 원래 자리로 되돌리기
   t       : 소품(컵·접시 등 pickupable)도 편집 대상에 포함/제외
   g       : 배치 완료 → 로봇 단계로
   x / ESC : 취소하고 종료 (로봇 단계 안 감)

─ 2단계(로봇) 조작 ────────────────────────────
   0~9 로봇선택, wasd 이동, qe 회전, rf 시선, x 종료  (6번과 동일)

─ 실행 ────────────────────────────────────────
   python scripts/7_arrange_then_robots.py [모델] [로봇수]
   예) python scripts/7_arrange_then_robots.py stretch 1   (기본값)
       python scripts/7_arrange_then_robots.py default 2

⚠️ 가구 재배치(TeleportObject)는 default / stretch 로봇에서만 적용된다.
   locobot 은 액션 집합에 오브젝트 조작이 없어서, 배치가 반영되지 않고
   기본 배치로 로봇이 뜬다(경고가 출력됨). 배치를 보려면 stretch/default 사용.

배치 결과는 data/arrangement.json 에도 저장된다(나중에 참고용).
"""

import os
import sys
import json
import traceback
import importlib.util

import cv2
import numpy as np
from PIL import Image, ImageDraw
from ai2thor.controller import Controller

# 6번 모듈 재사용 (로봇 배치/탑뷰카메라/조종루프). 파일명이 숫자로 시작해 importlib 로 로드.
_M6 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "6_robot_view.py")
_spec = importlib.util.spec_from_file_location("robot_view6", _M6)
m6 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m6)

SCENE = m6.SCENE
W, H = m6.W, m6.H
DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA, exist_ok=True)

EDIT_WIN = "Arrange Furniture (edit)"
MOVE_STEP = 0.1     # 한 번에 이동하는 거리(m)
ROT_STEP = 15       # 한 번에 회전하는 각도(deg)


# ─────────────────────── 탑뷰 좌표 투영 / 그리기 ───────────────────────
def make_projector(cam):
    """월드(x, z) -> 탑뷰 이미지 픽셀(u, v) 변환 함수. (정사영 카메라 기준)"""
    S = cam["orthographicSize"]
    cx, cz = cam["position"]["x"], cam["position"]["z"]
    aspect = W / H
    hw, hh = S * aspect, S

    def w2p(wx, wz):
        u = (wx - (cx - hw)) / (2 * hw) * W
        v = ((cz + hh) - wz) / (2 * hh) * H     # 월드 +z 가 위로
        return int(round(u)), int(round(v))
    return w2p


def info_bar(frame, lines):
    """하단에 검은 막대 + 한글 안내문(여러 줄)."""
    h, w = frame.shape[:2]
    bar = 22 * len(lines) + 8
    cv2.rectangle(frame, (0, h - bar), (w, h), (0, 0, 0), -1)
    if m6._FONT is None:
        for i, t in enumerate(lines):
            cv2.putText(frame, t, (8, h - bar + 18 + 22 * i),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)
        return frame
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    for i, t in enumerate(lines):
        d.text((8, h - bar + 4 + 22 * i), t, font=m6._FONT, fill=(0, 255, 0))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def objmap(controller):
    return {o["objectId"]: o for o in controller.last_event.metadata["objects"]}


def build_furniture(controller, include_small):
    """편집 대상 오브젝트 id 목록. 기본은 가구(moveable), 토글 시 소품(pickupable) 포함."""
    objs = controller.last_event.metadata["objects"]
    ids = [o["objectId"] for o in objs if o.get("moveable")]
    if include_small:
        ids += [o["objectId"] for o in objs if o.get("pickupable")]
    om = {o["objectId"]: o for o in objs}
    ids.sort(key=lambda i: (om[i]["objectType"], i))
    return ids


def render_edit(controller, cam_proj, ids, sel, include_small):
    le = controller.last_event
    td = cv2.cvtColor(le.third_party_camera_frames[-1], cv2.COLOR_RGB2BGR)
    om = objmap(controller)
    for i, oid in enumerate(ids):
        o = om.get(oid)
        if not o:
            continue
        u, v = cam_proj(o["position"]["x"], o["position"]["z"])
        if i == sel:
            cv2.circle(td, (u, v), 10, (0, 220, 255), 2)
            cv2.drawMarker(td, (u, v), (0, 220, 255), cv2.MARKER_CROSS, 18, 1)
        else:
            cv2.circle(td, (u, v), 4, (0, 0, 255), -1)
    cur = om.get(ids[sel]) if ids else None
    if cur:
        p = cur["position"]
        head = (f"선택: {cur['objectType']}  (x={p['x']:.2f}, z={p['z']:.2f}, "
                f"회전 {cur['rotation']['y']:.0f}°)  [{sel + 1}/{len(ids)}]")
    else:
        head = "편집할 가구가 없습니다."
    scope = "가구+소품" if include_small else "가구만"
    td = info_bar(td, [
        head,
        f"n/b 선택  wasd 이동  q/e 회전  z 원위치  t 소품토글({scope})  g 배치완료→로봇  x 취소",
    ])
    cv2.imshow(EDIT_WIN, td)


# ─────────────────────── 1단계: 가구 배치 편집 ───────────────────────
def edit_phase():
    """배치 편집 창을 띄운다. 반환: (arrangement dict 또는 None).
    None 이면 사용자가 취소한 것(로봇 단계로 가지 않음)."""
    print("=== 1단계: 가구 배치 편집 ===  (g=완료→로봇, x=취소)")
    c = Controller(scene=SCENE, width=W, height=H, gridSize=0.25, server_timeout=600.0)
    try:
        cam = c.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
        c.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
        proj = make_projector(cam)

        # 원래 위치 백업(되돌리기용) + 움직인 것 추적
        orig = {o["objectId"]: {"position": dict(o["position"]), "rotation": dict(o["rotation"])}
                for o in c.last_event.metadata["objects"]}
        moved = set()

        include_small = False
        ids = build_furniture(c, include_small)
        sel = 0

        cv2.namedWindow(EDIT_WIN, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(EDIT_WIN, W, H)
        cv2.moveWindow(EDIT_WIN, 40, 40)
        render_edit(c, proj, ids, sel, include_small)

        def teleport(oid, position, rotation):
            ev = c.step(action="TeleportObject", objectId=oid,
                        position=position, rotation=rotation, forceAction=True)
            if not ev.metadata["lastActionSuccess"]:
                print(f"  [이동 실패] {oid}: {ev.metadata.get('errorMessage','')[:50]}")
            else:
                moved.add(oid)

        while True:
            key = cv2.waitKey(30) & 0xFF
            if cv2.getWindowProperty(EDIT_WIN, cv2.WND_PROP_VISIBLE) < 1:
                return None
            if key == 255:
                continue
            if key in (ord('x'), 27):
                print("[취소] 배치를 취소했습니다.")
                return None
            if key == ord('g'):
                break

            if key == ord('t'):                    # 소품 포함 토글
                cur_id = ids[sel] if ids else None
                include_small = not include_small
                ids = build_furniture(c, include_small)
                sel = ids.index(cur_id) if cur_id in ids else 0
                render_edit(c, proj, ids, sel, include_small)
                continue

            if not ids:
                continue

            if key == ord('n'):
                sel = (sel + 1) % len(ids)
            elif key == ord('b'):
                sel = (sel - 1) % len(ids)
            else:
                oid = ids[sel]
                o = objmap(c)[oid]
                p, r = o["position"], o["rotation"]
                if key == ord('w'):
                    teleport(oid, {"x": p["x"], "y": p["y"], "z": p["z"] + MOVE_STEP}, r)
                elif key == ord('s'):
                    teleport(oid, {"x": p["x"], "y": p["y"], "z": p["z"] - MOVE_STEP}, r)
                elif key == ord('a'):
                    teleport(oid, {"x": p["x"] - MOVE_STEP, "y": p["y"], "z": p["z"]}, r)
                elif key == ord('d'):
                    teleport(oid, {"x": p["x"] + MOVE_STEP, "y": p["y"], "z": p["z"]}, r)
                elif key == ord('q'):
                    teleport(oid, p, {"x": r["x"], "y": (r["y"] - ROT_STEP) % 360, "z": r["z"]})
                elif key == ord('e'):
                    teleport(oid, p, {"x": r["x"], "y": (r["y"] + ROT_STEP) % 360, "z": r["z"]})
                elif key == ord('z'):              # 원래 자리로
                    teleport(oid, orig[oid]["position"], orig[oid]["rotation"])

            render_edit(c, proj, ids, sel, include_small)

        # 배치 완료: 움직인 오브젝트들의 현재 위치/회전 기록
        om = objmap(c)
        arrangement = {oid: {"position": dict(om[oid]["position"]),
                             "rotation": dict(om[oid]["rotation"])}
                       for oid in moved if oid in om}
        print(f"[완료] 옮긴 가구 {len(arrangement)}개. 로봇 단계로 넘어갑니다.")
        with open(os.path.join(DATA, "arrangement.json"), "w") as f:
            json.dump(arrangement, f, indent=2)
        return arrangement
    finally:
        c.stop()
        cv2.destroyAllWindows()    # 로봇 단계가 새로 창을 만들기 전에 편집 창 정리


# ─────────────────────── 2단계: 배치 적용 + 로봇 조종 ───────────────────────
def robot_phase(arrangement, model, count):
    print(f"=== 2단계: 로봇 조종 (모델={model}, {count}대) ===")
    c = Controller(scene=SCENE, width=W, height=H,
                   agentMode=model, agentCount=count,
                   gridSize=0.25, server_timeout=600.0)
    try:
        # 편집 단계에서 만든 배치를 새 장면에 다시 적용
        applied, unsupported = 0, False
        for oid, val in arrangement.items():
            try:
                ev = c.step(action="TeleportObject", objectId=oid,
                            position=val["position"], rotation=val["rotation"], forceAction=True)
            except ValueError as e:
                if "Invalid action" in str(e):    # locobot 등은 오브젝트 조작 액션이 없음
                    unsupported = True
                    break
                raise
            if ev.metadata["lastActionSuccess"]:
                applied += 1
            else:
                print(f"  [재적용 실패] {oid}: {ev.metadata.get('errorMessage','')[:50]}")
        if unsupported:
            print(f"[주의] '{model}' 로봇 모드는 가구 재배치 액션을 지원하지 않습니다(locobot 한계).")
            print("       기본 배치로 로봇을 띄웁니다. 배치를 반영하려면 stretch 또는 default 모델을 쓰세요.")
        else:
            print(f"[배치 적용] {applied}/{len(arrangement)}개 반영")

        m6.spread_robots(c, count)
        m6.add_topdown_camera(c)
        m6.run_control_loop(c, model, count)
    finally:
        c.stop()
        print("[종료] controller.stop()")


def parse_args():
    # 배치 적용이 되는 stretch 를 기본값으로(locobot 은 가구 재배치 불가).
    model = sys.argv[1] if len(sys.argv) > 1 else "stretch"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    if model not in m6.VALID_MODELS:
        print(f"[경고] 알 수 없는 모델 '{model}' -> stretch 로 진행. (가능: {m6.VALID_MODELS})")
        model = "stretch"
    return model, max(1, min(count, 5))


def main():
    model, count = parse_args()
    arrangement = edit_phase()
    if arrangement is None:
        return 0
    robot_phase(arrangement, model, count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
