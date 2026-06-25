"""[3] 기본 방 가구를 내 맘대로 바꾸기 / 스위칭하기.

iTHOR 장면(FloorPlan*)은 '미리 지어진 방'이라 새 가구를 무에서 추가하긴 어렵지만,
이미 놓여 있는 물체들은 액션으로 자유롭게 조작/스위칭할 수 있다. 이 스크립트는
대표적인 5가지 조작을 보여주고, 각 단계마다 top-down 이미지를 저장해 비교한다.

  (A) 물체 상태 스위칭   : 냉장고 열기(OpenObject), 전등 켜기(ToggleObjectOn)
  (B) 물체 위치 옮기기   : 특정 가구를 다른 좌표로 순간이동(TeleportObject)
  (C) 물체 제거하기      : 가구를 장면에서 빼기(DisableObject)
  (D) 통째로 재배치       : 모든 집을 수 있는 물체를 랜덤 재배치(InitialRandomSpawn)
  (E) 방 자체 스위칭      : 다른 FloorPlan으로 reset

핵심 패턴:
    controller.step(action="액션이름", objectId="<물체ID>", ...)
물체 ID는 metadata["objects"] 에서 얻는다.
"""

import os
import sys
import traceback

from PIL import Image
from ai2thor.controller import Controller


# 결과 이미지는 프로젝트 루트의 outputs/ 폴더에 저장 (실행 위치와 무관)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUT, exist_ok=True)


def topdown(controller, name):
    """현재 장면을 top-down 카메라로 찍어 저장."""
    frames = controller.last_event.third_party_camera_frames
    if not frames:  # 아직 카메라가 없으면 추가
        cam = controller.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
        controller.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
        frames = controller.last_event.third_party_camera_frames
    path = os.path.join(OUT, name)
    Image.fromarray(frames[0]).save(path)
    print(f"[저장] {path}")


def find(controller, object_type):
    """objectType(예: 'Fridge')에 해당하는 첫 번째 물체의 objectId를 반환."""
    for o in controller.last_event.metadata["objects"]:
        if o["objectType"] == object_type:
            return o["objectId"]
    return None


def report(controller, label, object_id):
    o = next(x for x in controller.last_event.metadata["objects"] if x["objectId"] == object_id)
    print(f"  [{label}] {object_id}  open={o.get('isOpen')} on={o.get('isToggled')} pos={o['position']}")


def main():
    controller = Controller(scene="FloorPlan1", width=900, height=700, gridSize=0.25,
                            server_timeout=600.0)
    try:
        # top-down 카메라 미리 추가
        cam = controller.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
        controller.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
        topdown(controller, "3_0_before.png")

        # ---- (A) 상태 스위칭: 냉장고 열기 + 전등 켜기 ----
        fridge = find(controller, "Fridge")
        if fridge:
            controller.step(action="OpenObject", objectId=fridge, openness=1.0, forceAction=True)
            report(controller, "냉장고 열기", fridge)
        light = find(controller, "LightSwitch")
        if light:
            controller.step(action="ToggleObjectOn", objectId=light, forceAction=True)
            report(controller, "전등 스위치 켜기", light)
        topdown(controller, "3_A_state_switched.png")

        # ---- (B) 위치 옮기기: 의자/토스터 같은 가구를 다른 좌표로 이동 ----
        movable = find(controller, "Toaster") or find(controller, "Pot") or find(controller, "Mug")
        if movable:
            report(controller, "이동 전", movable)
            # 현재 위치에서 살짝 옆/위로 옮기기
            o = next(x for x in controller.last_event.metadata["objects"] if x["objectId"] == movable)
            p = o["position"]
            controller.step(
                action="TeleportObject",
                objectId=movable,
                position={"x": p["x"] + 0.3, "y": p["y"] + 0.2, "z": p["z"] + 0.3},
                rotation={"x": 0, "y": 90, "z": 0},
                forceAction=True,
            )
            report(controller, "이동 후", movable)
        topdown(controller, "3_B_moved.png")

        # ---- (C) 가구 제거: 식탁 등을 장면에서 빼버리기 ----
        target = find(controller, "DiningTable") or find(controller, "CounterTop") or find(controller, "GarbageCan")
        if target:
            controller.step(action="DisableObject", objectId=target)
            print(f"  [제거] {target} 를 장면에서 뺐습니다.")
        topdown(controller, "3_C_removed.png")

        # ---- (D) 통째로 랜덤 재배치: 집을 수 있는 모든 물체 위치 섞기 ----
        controller.step(action="InitialRandomSpawn", randomSeed=42,
                        forceVisible=False, numPlacementAttempts=5)
        print("  [재배치] InitialRandomSpawn 으로 물체들을 새로 배치했습니다.")
        topdown(controller, "3_D_respawned.png")

        # ---- (E) 방 자체 스위칭: 완전히 다른 FloorPlan 으로 교체 ----
        controller.reset(scene="FloorPlan201")   # 주방 -> 거실
        cam = controller.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
        controller.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
        topdown(controller, "3_E_other_room.png")
        print("  [스위칭] FloorPlan1(주방) -> FloorPlan201(거실) 로 방 자체를 교체했습니다.")

        print("\n완료: 3_0_before.png ~ 3_E_other_room.png 를 순서대로 비교해보세요.")
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        controller.stop()
        print("[종료] controller.stop()")


if __name__ == "__main__":
    sys.exit(main())
