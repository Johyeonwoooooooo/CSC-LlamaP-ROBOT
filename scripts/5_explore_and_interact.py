"""[5] 방을 직접 돌아다니며 가구와 상호작용하기 (실시간 OpenCV 창).

OpenCV 창에 에이전트의 1인칭 화면이 뜨고, 화면 한가운데 '조준점(+)'이 있다.
키보드로 방을 돌아다니고, 보고 싶은 물체를 조준점에 맞춘 뒤 키를 눌러
열기/켜기/집기 등을 할 수 있다.

※ 이 PC는 GPU 드라이버가 응답하지 않아 소프트웨어 렌더링(llvmpipe)으로 돌아간다.
  한 동작(렌더)에 수 초가 걸리기 때문에, 렌더링을 '백그라운드 스레드'로 분리해서
  그 사이에도 창이 멈추지(응답없음) 않도록 만들었다. 화면 우상단에 '처리중'이 뜨면
  에이전트가 그 동작을 처리하는 중이며, 끝나면 화면이 갱신된다.

─ 이동 / 시점 ─────────────────────────
   w / s   : 앞으로 / 뒤로
   a / d   : 왼쪽 / 오른쪽 게걸음
   마우스   : 창 안에서 움직이면 시점이 따라 돈다 (좌우=회전, 상하=시선)
            ※ 포인터가 창 밖으로 나가면 멈춤(OpenCV 한계). 다시 안으로 움직이면 됨.

─ 상호작용 (조준점에 물체를 맞춘 상태에서) ─
   o       : 열기 / 닫기   (냉장고·서랍·캐비닛 등)
   t       : 켜기 / 끄기   (전등·수도꼭지 등)
   p       : 집기 / 내려놓기 (사과·머그컵 등 작은 물체)
   r       : 방 전체를 위에서 본 top-down 스냅샷 저장

   x 또는 ESC : 종료  (창의 X 버튼을 눌러도 종료)
"""

import os
import sys
import queue
import threading
import traceback

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ai2thor.controller import Controller


SCENE = "FloorPlan1"
WIN = "AI2-THOR  (move wasd  look=mouse  interact o/t/p  quit x)"

# 스냅샷은 프로젝트 루트의 outputs/ 폴더에 저장 (실행 위치와 무관)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUT, exist_ok=True)

# 한글 폰트 로드 — OpenCV 내장 폰트는 한글을 못 그려서(네모/물음표로 깨짐),
# Noto Sans CJK KR 로 PIL 을 통해 그린다.
_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
try:
    _FONT = ImageFont.truetype(_FONT_PATH, 16)
    _FONT_BIG = ImageFont.truetype(_FONT_PATH, 20)
except Exception:
    _FONT = _FONT_BIG = None   # 폰트가 없으면 cv2 영문 폴백


def put_text(frame_bgr, lines):
    """frame_bgr(numpy BGR) 위에 한글 텍스트들을 그린다.
    lines: [(text, (x, y_top), font, (B,G,R)), ...]"""
    if _FONT is None:   # 폰트 없으면 OpenCV 로 폴백(한글은 깨질 수 있음)
        for text, (x, y), _f, color in lines:
            cv2.putText(frame_bgr, text, (x, y + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        return frame_bgr
    img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    for text, org, font, (b, g, r) in lines:
        draw.text(org, text, font=font or _FONT, fill=(r, g, b))   # PIL 은 RGB
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

# 메인 스레드(GUI)와 워커 스레드(렌더링)가 공유하는 상태
state = {"event": None, "status": "로딩 중...", "alive": True}
lock = threading.Lock()
cmd_q = queue.Queue(maxsize=1)   # 한 번에 한 동작만 (밀림 방지)


# ─────────────────────────── 워커 스레드: ai2thor 렌더링 전담 ───────────────────────────
def worker():
    """ai2thor Controller 를 띄우고, 큐로 들어온 동작만 순차 실행한다.
    Controller 관련 호출은 전부 이 스레드 안에서만 일어난다(스레드 안전)."""
    try:
        controller = Controller(
            scene=SCENE,
            width=640, height=480,
            gridSize=0.25,
            visibilityDistance=1.8,
            renderInstanceSegmentation=True,   # 조준점 물체 식별용
            server_timeout=600.0,
        )
    except Exception as e:
        with lock:
            state["status"] = f"Controller 시작 실패: {e}"
            state["alive"] = False
        return

    with lock:
        state["event"] = controller.last_event
        state["status"] = "준비됨. wasd 로 이동해보세요."

    try:
        while state["alive"]:
            try:
                cmd = cmd_q.get(timeout=0.2)
            except queue.Empty:
                continue
            if cmd is None:
                break
            try:
                if cmd.get("_special") == "snapshot":
                    cam = controller.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
                    controller.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
                    td = controller.last_event.third_party_camera_frames[0]
                    snap = os.path.join(OUT, "5_topdown_snapshot.png")
                    cv2.imwrite(snap, cv2.cvtColor(td, cv2.COLOR_RGB2BGR))
                    status = f"top-down 스냅샷 저장: {snap}"
                else:
                    label = cmd.pop("_label", cmd["action"])
                    ev = controller.step(**cmd)
                    if ev.metadata["lastActionSuccess"]:
                        status = f"{label} -> OK"
                    else:
                        status = f"{label} -> 실패: {ev.metadata.get('errorMessage','')[:40]}"
                with lock:
                    state["event"] = controller.last_event
                    state["status"] = status
            except Exception as e:
                with lock:
                    state["status"] = f"동작 오류: {e}"
            finally:
                cmd_q.task_done()
    finally:
        controller.stop()
        print("[정리] controller.stop()")


# ─────────────────────────── 헬퍼: 조준점 물체 찾기 / HUD 그리기 ───────────────────────────
def target_object_id(event):
    seg = event.instance_segmentation_frame
    if seg is None:
        return None
    h, w = seg.shape[:2]
    color = tuple(int(v) for v in seg[h // 2, w // 2])
    return event.color_to_object_id.get(color)


def get_obj(event, object_id):
    if not object_id:
        return None
    for o in event.metadata["objects"]:
        if o["objectId"] == object_id:
            return o
    return None


def draw_hud(event, target, status, busy):
    frame = cv2.cvtColor(event.frame, cv2.COLOR_RGB2BGR)
    h, w = frame.shape[:2]

    cx, cy = w // 2, h // 2
    cv2.line(frame, (cx - 10, cy), (cx + 10, cy), (0, 255, 0), 1)
    cv2.line(frame, (cx, cy - 10), (cx, cy + 10), (0, 255, 0), 1)

    if target:
        bits = [target["objectType"]]
        if target.get("openable"):
            bits.append("열림" if target["isOpen"] else "닫힘")
        if target.get("toggleable"):
            bits.append("ON" if target["isToggled"] else "OFF")
        if target.get("pickupable"):
            bits.append("집기가능")
        vis = "보임" if target["visible"] else "멀어서_안됨"
        line = f"겨냥: {' / '.join(bits)}  [{vis}]"
    else:
        line = "겨냥: (없음 - 물체를 조준점에 맞추세요)"

    cv2.rectangle(frame, (0, h - 46), (w, h), (0, 0, 0), -1)

    texts = [
        (line, (8, h - 44), _FONT, (0, 255, 0)),
        (status, (8, h - 22), _FONT, (200, 200, 255)),
    ]
    if busy:   # 워커가 동작 처리 중이면 우상단에 표시
        texts.append(("처리중...", (w - 110, 6), _FONT_BIG, (0, 200, 255)))
    return put_text(frame, texts)


# 이동 키 -> ai2thor 액션 (시점 회전/시선은 이제 마우스가 담당)
MOVES = {
    ord('w'): dict(action="MoveAhead", _label="MoveAhead"),
    ord('s'): dict(action="MoveBack", _label="MoveBack"),
    ord('a'): dict(action="MoveLeft", _label="MoveLeft"),
    ord('d'): dict(action="MoveRight", _label="MoveRight"),
}


# ─────────────────────────── 마우스 시점(마우스룩) ───────────────────────────
# 창 안에서 마우스를 움직이면 시점이 따라 돈다. 좌우=회전(yaw), 상하=시선(horizon).
# 매 프레임 TeleportFull 로 '절대 방향'을 한 번에 설정한다(회전+시선 동시).
# OpenCV 는 포인터를 가둘 수 없어 창 밖으로 나가면 멈춘다(다시 안으로 움직이면 됨).
MOUSE_SENS = 0.30                          # 픽셀당 회전 각도(deg). 키우면 빨라진다.
HORIZON_MIN, HORIZON_MAX = -30.0, 60.0     # 시선 위/아래 한계(ai2thor 카메라 범위)

mouse = {"x": None, "y": None, "dx": 0.0, "dy": 0.0}
look = {"yaw": None, "horizon": None, "dirty": False}   # 목표 방향(None=미초기화)


def on_mouse(event_type, x, y, flags, param):
    """마우스 이동량(dx, dy)을 누적. (cv2.waitKey 안에서 호출됨)"""
    if event_type == cv2.EVENT_MOUSEMOVE:
        if mouse["x"] is not None:
            mouse["dx"] += x - mouse["x"]
            mouse["dy"] += y - mouse["y"]
        mouse["x"], mouse["y"] = x, y


def update_look(event):
    """누적된 마우스 이동량을 목표 yaw/horizon 에 반영한다(전송과는 분리)."""
    agent = event.metadata["agent"]
    if look["yaw"] is None:                # 첫 초기화: 현재 에이전트 방향에서 시작
        look["yaw"] = float(agent["rotation"]["y"])
        look["horizon"] = float(round(agent.get("cameraHorizon", 0.0)))
    dx, dy = mouse["dx"], mouse["dy"]
    mouse["dx"] = mouse["dy"] = 0.0
    if dx or dy:
        look["yaw"] = (look["yaw"] + dx * MOUSE_SENS) % 360
        look["horizon"] = max(HORIZON_MIN,
                              min(HORIZON_MAX, look["horizon"] + dy * MOUSE_SENS))
        look["dirty"] = True


def look_action(event):
    """목표 방향이 바뀌어 있으면(dirty) TeleportFull 동작 dict 를 반환."""
    if not look["dirty"]:
        return None
    agent = event.metadata["agent"]
    p = agent["position"]
    return {
        "action": "TeleportFull",
        "position": {"x": p["x"], "y": p["y"], "z": p["z"]},
        "rotation": {"x": 0.0, "y": look["yaw"], "z": 0.0},
        "horizon": float(look["horizon"]),
        "standing": agent.get("isStanding", True),
        "forceAction": True,
        "_label": "마우스시점",
    }


def plan(event, key):
    """키를 받아 워커에게 보낼 동작 dict 를 만든다. (메인 스레드에서 호출)
    상호작용 키는 지금 조준 중인 물체를 보고 구체 액션으로 변환한다."""
    if key in MOVES:
        return dict(MOVES[key]), None

    if key == ord('r'):
        return {"_special": "snapshot"}, None

    if key in (ord('o'), ord('t'), ord('p')):
        target = get_obj(event, target_object_id(event))
        if not target:
            return None, "겨냥된 물체가 없습니다. 조준점을 물체에 맞추세요."
        oid = target["objectId"]
        otype = target["objectType"]

        if key == ord('o'):
            if not target.get("openable"):
                return None, f"{otype} 은(는) 열 수 없는 물체입니다."
            act = "CloseObject" if target["isOpen"] else "OpenObject"
            return {"action": act, "objectId": oid, "_label": f"{act} {otype}"}, None

        if key == ord('t'):
            if not target.get("toggleable"):
                return None, f"{otype} 은(는) 켤 수 없는 물체입니다."
            act = "ToggleObjectOff" if target["isToggled"] else "ToggleObjectOn"
            return {"action": act, "objectId": oid, "_label": f"{act} {otype}"}, None

        if key == ord('p'):
            if event.metadata["inventoryObjects"]:
                return {"action": "DropHandObject", "forceAction": True, "_label": "내려놓기"}, None
            if target.get("pickupable"):
                return {"action": "PickupObject", "objectId": oid, "_label": f"집기 {otype}"}, None
            return None, f"{otype} 은(는) 집을 수 없는 물체입니다."

    return None, None


# ─────────────────────────── 메인 스레드: 창 그리기 + 키 입력 ───────────────────────────
def main():
    print("=== 인터랙티브 탐험 시작 ===")
    print("OpenCV 창에 포커스를 둔 채 키를 누르세요. (x/ESC 종료)")
    print("Controller 가 처음 뜨는 데 시간이 좀 걸립니다(소프트웨어 렌더링).")

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN, 640, 480)
    cv2.setMouseCallback(WIN, on_mouse)   # 마우스 시점

    try:
        while True:
            with lock:
                event = state["event"]
                status = state["status"]
                alive = state["alive"]
            busy = not cmd_q.empty()

            if not alive and event is None:
                print(f"[종료] {status}")
                break

            if event is None:
                # 아직 로딩 중 — 안내만 보여주고 창은 계속 펌프
                blank = np.zeros((480, 640, 3), dtype="uint8")
                cv2.putText(blank, "Loading AI2-THOR ...", (150, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2, cv2.LINE_AA)
                cv2.imshow(WIN, blank)
                if cv2.waitKey(100) & 0xFF in (ord('x'), 27):
                    break
                continue

            target = get_obj(event, target_object_id(event))
            cv2.imshow(WIN, draw_hud(event, target, status, busy))

            if cv2.getWindowProperty(WIN, cv2.WND_PROP_VISIBLE) < 1:
                break

            key = cv2.waitKey(20) & 0xFF
            if key in (ord('x'), 27):
                break

            # 마우스 이동량을 항상 목표 시점에 반영(busy 여부 무관 -> 끊김 없이 누적)
            update_look(event)

            # (1) 키 동작 우선, (2) 키가 없으면 마우스 시점 동작
            action, msg = (None, None)
            if key != 255:
                action, msg = plan(event, key)
            if action is None and msg is None and not busy:
                action = look_action(event)   # 마우스 시점은 워커가 한가할 때만 전송

            if msg:                  # 즉시 안내(겨냥 없음 등)
                with lock:
                    state["status"] = msg
            if action is not None:
                is_look = action.get("_label") == "마우스시점"
                if busy:
                    if not is_look:  # 마우스 시점은 busy면 조용히 버림(다음 프레임에 최신값 재전송)
                        with lock:
                            state["status"] = "아직 이전 동작 처리 중... 잠시 후 다시"
                else:
                    if not is_look:  # HUD 상태줄은 키 동작일 때만 갱신(마우스로 도배 방지)
                        with lock:
                            state["status"] = f"처리 요청: {action.get('_label', action.get('action','?'))}"
                    try:
                        cmd_q.put_nowait(action)
                        if is_look:
                            look["dirty"] = False   # 전송 성공 -> 목표 도달 처리
                    except queue.Full:
                        pass
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        state["alive"] = False
        try:
            cmd_q.put_nowait(None)
        except queue.Full:
            pass
        cv2.destroyAllWindows()
        t.join(timeout=10)
        print("[종료]")


if __name__ == "__main__":
    sys.exit(main())
