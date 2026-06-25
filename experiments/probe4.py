import json, inspect
from ai2thor.controller import Controller
c = Controller(scene="Procedural", width=300, height=300, server_timeout=600.0)
def tmpl():
    return {
      "id":"house","layout":"0 0 0 0\n0 2 2 0\n0 2 2 0\n0 0 0 0",
      "objectsLayouts":["0 0 0 0\n0 = = 0\n0 = = 0\n0 0 0 0"],
      "rooms":{"2":{"wallMaterial":{"name":"DrywallOrange"},
                    "floorMaterial":{"name":"PinkTile"},
                    "floorColliderThickness":1.0,"roomType":"Bedroom"}},
      "doors":{},"windows":{},
      "proceduralParameters":{"ceilingMaterial":{"name":"CeilingMaterial"},
        "floorColliderThickness":1.0,"lights":[],"receptacleHeight":0.7,
        "reflections":[],"skyboxId":"Sky1"}}
try:
    for ob in [0, 1]:
        r = c.step(action="GetHouseFromTemplate", template=tmpl(), outsideBoundaryId=ob)
        ok = r.metadata["lastActionSuccess"]
        print(f"[outsideBoundaryId={ob}] success={ok} err={(r.metadata.get('errorMessage') or '')[:80]!r}")
        if ok:
            house = r.metadata["actionReturn"]
            json.dump(house, open("template_house.json","w"), indent=2)
            print("  저장 template_house.json; keys:", list(house.keys()))
            print("  wall[0]:", json.dumps(house["walls"][0])[:200])
            print("  room[0] floorMaterial:", house["rooms"][0].get("floorMaterial"))
            print("  skyboxId:", house["proceduralParameters"].get("skyboxId"))
            # 바로 CreateHouse 시도
            r2 = c.step(action="CreateHouse", house=house)
            print("  CreateHouse success =", r2.metadata["lastActionSuccess"],
                  (r2.metadata.get('errorMessage') or '')[:80])
            break
finally:
    c.stop()
