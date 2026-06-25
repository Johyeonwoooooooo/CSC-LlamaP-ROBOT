import json
from ai2thor.controller import Controller
c = Controller(scene="Procedural", width=300, height=300, server_timeout=600.0)
try:
    # 1) 아주 단순한 템플릿으로 완성된 house dict 받아오기
    template = {
        "id": "house",
        "layout": "0 0 0 0\n0 2 2 0\n0 2 2 0\n0 0 0 0",
        "objectsLayouts": ["0 0 0 0\n0 = + 0\n0 + + 0\n0 0 0 0"],
        "rooms": {
            "2": {
                "wallMaterial": {"name": "DrywallOrange"},
                "floorMaterial": {"name": "PinkTile"},
                "floorColliderThickness": 1.0,
                "roomType": "Bedroom",
            }
        },
        "doors": {},
        "windows": {},
        "proceduralParameters": {
            "ceilingMaterial": {"name": "CeilingMaterial"},
            "floorColliderThickness": 1.0,
            "lights": [],
            "receptacleHeight": 0.7,
            "reflections": [],
            "skyboxId": "Sky1",
        },
    }
    r = c.step(action="GetHouseFromTemplate", template=template)
    print("GetHouseFromTemplate success =", r.metadata["lastActionSuccess"])
    print("err =", r.metadata.get("errorMessage"))
    house = r.metadata.get("actionReturn")
    if house:
        with open("template_house.json", "w") as f:
            json.dump(house, f, indent=2)
        print("저장: template_house.json")
        print("keys:", list(house.keys()))
        if house.get("walls"):
            print("wall[0] keys:", list(house["walls"][0].keys()))
            print("wall[0] material:", house["walls"][0].get("material"))
        if house.get("rooms"):
            print("room[0] keys:", list(house["rooms"][0].keys()))
        print("proceduralParameters keys:", list(house["proceduralParameters"].keys()))
        print("skyboxId:", house["proceduralParameters"].get("skyboxId"))
finally:
    c.stop()
