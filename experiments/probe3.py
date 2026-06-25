from ai2thor.controller import Controller
from copy import deepcopy

def base_house():
    c = [(0.0,0.0),(0.0,4.0),(4.0,4.0),(4.0,0.0)]
    def wall(wid,p0,p1):
        return {"id":wid,"roomId":"room1","material":{"name":"DrywallOrange"},
                "polygon":[{"x":p0[0],"y":0,"z":p0[1]},{"x":p1[0],"y":0,"z":p1[1]},
                           {"x":p1[0],"y":2.5,"z":p1[1]},{"x":p0[0],"y":2.5,"z":p0[1]}]}
    return {
      "metadata":{"schema":"1.0.0","agent":{"horizon":30,"position":{"x":2,"y":0.9,"z":2},
                  "rotation":{"x":0,"y":0,"z":0},"standing":True}},
      "rooms":[{"id":"room1","roomType":"Bedroom","floorMaterial":{"name":"PinkTile"},
                "floorPolygon":[{"x":x,"y":0,"z":z} for x,z in c],"ceilings":[],"children":[]}],
      "walls":[wall("wall1",c[0],c[1]),wall("wall2",c[1],c[2]),
               wall("wall3",c[2],c[3]),wall("wall4",c[3],c[0])],
      "doors":[],"windows":[],"objects":[],
      "proceduralParameters":{"ceilingMaterial":{"name":"CeilingMaterial"},
        "floorColliderThickness":1.0,"receptacleHeight":0.7,"reflections":[],
        "skyboxId":"Sky1",
        "lights":[{"id":"light1","type":"point","position":{"x":2,"y":2.2,"z":2},
                   "intensity":1.0,"range":15,"rgb":{"r":1,"g":1,"b":1},
                   "shadow":{"type":"Soft","strength":1,"normalBias":0.4,"bias":0.05,
                             "nearPlane":0.2,"resolution":"FromQualitySettings"}}]}}

c = Controller(scene="Procedural", width=300, height=300, server_timeout=600.0)
def trial(name, mut):
    h = base_house(); mut(h)
    r = c.step(action="CreateHouse", house=h)
    e = r.metadata.get('errorMessage') or ''
    short = e.split('\n')[0][:90]
    print(f"[{name}] success={r.metadata['lastActionSuccess']} err={short!r}")
def dirlight(h):
    h["proceduralParameters"]["lights"]=[{"id":"light1","type":"directional",
        "position":{"x":0.84,"y":0.13,"z":-0.65},"rotation":{"x":44,"y":17,"z":19},
        "intensity":1.0,"indirectMultiplier":1.0,"rgb":{"r":1,"g":1,"b":1},
        "shadow":{"type":"Soft","strength":1,"normalBias":0.4,"bias":0.05,
                  "nearPlane":0.2,"resolution":"FromQualitySettings"}}]
try:
    trial("A.lights_empty", lambda h: h["proceduralParameters"].__setitem__("lights",[]))
    trial("B.directional", dirlight)
    trial("C.walls_empty", lambda h: h.__setitem__("walls",[]))
    trial("D.livingroom", lambda h: h["rooms"][0].__setitem__("roomType","LivingRoom"))
    trial("E.no_metadata", lambda h: h.pop("metadata"))
    trial("F.dir+id_underscore", lambda h: (dirlight(h),
        [w.__setitem__("id",w["id"].replace("wall","wall_")) for w in h["walls"]]))
finally:
    c.stop()
