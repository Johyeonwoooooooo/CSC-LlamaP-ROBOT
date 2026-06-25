import os, importlib.util, numpy as np
from ai2thor.controller import Controller
# 5번 모듈에서 헬퍼 재사용 (scripts/ 로 이동했으므로 경로 보정)
_m5_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "scripts", "5_explore_and_interact.py")
spec = importlib.util.spec_from_file_location("m5", _m5_path)
m5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(m5)

c = Controller(scene="FloorPlan1", width=640, height=480, gridSize=0.25,
               visibilityDistance=1.8, renderInstanceSegmentation=True, server_timeout=600.0)
try:
    ev = c.last_event
    print("instance_segmentation_frame:", None if ev.instance_segmentation_frame is None else ev.instance_segmentation_frame.shape)
    print("color_to_object_id 개수:", len(ev.color_to_object_id))
    # 조준점 물체 식별
    tid = m5.target_object_id(ev)
    print("시작 조준점 물체:", tid)

    # 몇 걸음 움직이며 조준 물체 추적
    for act in ["MoveAhead","RotateRight","MoveAhead","LookDown"]:
        ev = c.step(action=act, **({"degrees":30} if "Rotate" in act else {"degrees":20} if "Look" in act else {}))
        tid = m5.target_object_id(ev)
        t = m5.get_obj(ev, tid)
        print(f"{act:12s} ok={ev.metadata['lastActionSuccess']}  조준->{t['objectType'] if t else None}")

    # 보이는 openable / toggleable / pickupable 한 개씩 직접 동작시켜 검증
    objs = ev.metadata["objects"]
    def first(prop): 
        return next((o for o in objs if o.get(prop) and o["visible"]), 
                    next((o for o in objs if o.get(prop)), None))
    op = first("openable")
    if op:
        r=c.step(action=("CloseObject" if op["isOpen"] else "OpenObject"), objectId=op["objectId"], forceAction=True)
        print("OPEN test:", op["objectType"], r.metadata["lastActionSuccess"])
    tg = first("toggleable")
    if tg:
        r=c.step(action=("ToggleObjectOff" if tg["isToggled"] else "ToggleObjectOn"), objectId=tg["objectId"], forceAction=True)
        print("TOGGLE test:", tg["objectType"], r.metadata["lastActionSuccess"])
    pk = first("pickupable")
    if pk:
        r=c.step(action="PickupObject", objectId=pk["objectId"], forceAction=True)
        print("PICKUP test:", pk["objectType"], r.metadata["lastActionSuccess"],
              "| inventory:", [o["objectType"] for o in c.last_event.metadata["inventoryObjects"]])
        r=c.step(action="DropHandObject", forceAction=True)
        print("DROP test:", r.metadata["lastActionSuccess"])
    print("SMOKE OK")
finally:
    c.stop()
