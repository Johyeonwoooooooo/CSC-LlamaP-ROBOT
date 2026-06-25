import json
from ai2thor.controller import Controller
c = Controller(scene="Procedural", width=300, height=300, server_timeout=600.0)
def tmpl(roomkey, with_id):
    room={"wallMaterial":{"name":"DrywallOrange"},"floorMaterial":{"name":"PinkTile"},
          "floorColliderThickness":1.0,"roomType":"Bedroom"}
    if with_id: room["id"]=f"room|{roomkey}"
    layout="\n".join(" ".join(("0" if v==0 else str(roomkey)) for v in row)
                     for row in [[0,0,0,0],[0,1,1,0],[0,1,1,0],[0,0,0,0]])
    return {"id":"house","layout":layout,
      "objectsLayouts":[layout.replace(str(roomkey),"=")],
      "rooms":{str(roomkey):room},"doors":{},"windows":{},
      "proceduralParameters":{"ceilingMaterial":{"name":"CeilingMaterial"},
        "floorColliderThickness":1.0,"lights":[],"receptacleHeight":0.7,
        "reflections":[],"skyboxId":"Sky1"}}
def go(name, t):
    r=c.step(action="GetHouseFromTemplate", template=t)
    ok=r.metadata["lastActionSuccess"]
    print(f"[{name}] success={ok} err={(r.metadata.get('errorMessage') or '')[:70]!r}")
    return r.metadata["actionReturn"] if ok else None
try:
    house=None
    for nm,t in [("k1_id", tmpl(1,True)), ("k1_noid", tmpl(1,False)),
                 ("k2_id", tmpl(2,True))]:
        house=go(nm,t)
        if house: print("  WIN ->",nm); break
    if house:
        json.dump(house, open("template_house.json","w"), indent=2)
        print("  walls:",len(house.get("walls",[])),"rooms:",len(house.get("rooms",[])))
        print("  floorMat:",house["rooms"][0].get("floorMaterial"),
              "wallMat:",house["walls"][0].get("material") if house.get("walls") else None)
        print("  skyboxId:",house["proceduralParameters"].get("skyboxId"))
        r2=c.step(action="CreateHouse", house=house)
        print("  CreateHouse success =",r2.metadata["lastActionSuccess"],
              (r2.metadata.get('errorMessage') or '')[:70])
finally:
    c.stop()
