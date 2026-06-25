import json
from ai2thor.controller import Controller
c = Controller(scene="Procedural", width=300, height=300, server_timeout=600.0)
try:
    mats = c.step(action="GetMaterials").metadata["actionReturn"]
    json.dump(mats, open("materials.json","w"), indent=2)
    print("전체 카테고리:", list(mats.keys()))
    for k in mats:
        kl=k.lower()
        if any(s in kl for s in ["wall","floor","ceil","fabric","wood","tile","metal","drywall"]):
            v=mats[k]
            print(f"\n[{k}] ({len(v)}개) -> {v[:12]}")
finally:
    c.stop()
