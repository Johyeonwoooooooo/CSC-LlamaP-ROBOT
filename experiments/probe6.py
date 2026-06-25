from ai2thor.controller import Controller
c = Controller(scene="Procedural", width=300, height=300, server_timeout=600.0)
def try_action(a, **kw):
    try:
        r=c.step(action=a, **kw)
        ret=r.metadata.get("actionReturn")
        info=type(ret).__name__
        if isinstance(ret,list): info=f"list[{len(ret)}] sample={ret[:5]}"
        elif isinstance(ret,dict): info=f"dict keys={list(ret.keys())[:8]}"
        print(f"[{a}] ok={r.metadata['lastActionSuccess']} ret={info}")
    except Exception as e:
        print(f"[{a}] EXC {str(e).splitlines()[0][:60]}")
try:
    for a in ["GetMaterials","GetMaterialProperties","GetAssetDatabase",
              "GetRuntimeAssets","GetAssetMetadata","GetAvailableMaterials",
              "GetSceneBounds"]:
        try_action(a)
    # 재질을 color 로 지정해보기 (이름 lookup 회피 시도)
    c2=[(0.0,0.0),(0.0,4.0),(4.0,4.0),(4.0,0.0)]
    def wall(wid,p0,p1):
        return {"id":wid,"roomId":"room1","material":{"color":{"r":0.8,"g":0.5,"b":0.3,"a":1.0}},
                "polygon":[{"x":p0[0],"y":0,"z":p0[1]},{"x":p1[0],"y":0,"z":p1[1]},
                           {"x":p1[0],"y":2.5,"z":p1[1]},{"x":p0[0],"y":2.5,"z":p0[1]}]}
    h={"metadata":{"schema":"1.0.0"},
      "rooms":[{"id":"room1","roomType":"Bedroom","floorMaterial":{"color":{"r":0.6,"g":0.6,"b":0.6,"a":1.0}},
                "floorPolygon":[{"x":x,"y":0,"z":z} for x,z in c2],"ceilings":[],"children":[]}],
      "walls":[wall("wall1",c2[0],c2[1]),wall("wall2",c2[1],c2[2]),
               wall("wall3",c2[2],c2[3]),wall("wall4",c2[3],c2[0])],
      "doors":[],"windows":[],"objects":[],
      "proceduralParameters":{"ceilingMaterial":{"color":{"r":0.9,"g":0.9,"b":0.9,"a":1.0}},
        "floorColliderThickness":1.0,"receptacleHeight":0.7,"reflections":[],
        "skyboxColor":{"r":0.5,"g":0.6,"b":0.8,"a":1.0},"lights":[]}}
    r=c.step(action="CreateHouse", house=h)
    print("[CreateHouse color-material] ok=",r.metadata["lastActionSuccess"],
          (r.metadata.get('errorMessage') or '')[:80])
finally:
    c.stop()
