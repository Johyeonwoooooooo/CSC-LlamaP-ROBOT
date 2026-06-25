"""[4] 내 맘대로 커스텀 방 만들기 — Procedural(절차적 생성) 모드.

FloorPlan* 은 '완성된 집'이라 구조를 못 바꾸지만, scene="Procedural" 로 띄우면
바닥 다각형 / 벽 / 재질 / 조명 / 가구를 JSON(dict)으로 직접 정의해
완전히 새로운 방을 지을 수 있다. (ProcTHOR 가 쓰는 바로 그 방식)

집(house) JSON의 핵심 구조:
    rooms[]   : 방. floorPolygon(바닥 꼭짓점들) + floorMaterial 로 정의
    walls[]   : 벽. polygon(아래 두 꼭짓점 -> 위 두 꼭짓점) + material
    objects[] : 가구. assetId 로 어떤 모델을 어디에 놓을지 지정
    proceduralParameters : 천장/조명/스카이박스 등 전역 설정

이 스크립트는 4m x 4m 방을 하나 짓고, 가구를 한 개 놓아본 뒤 이미지를 저장한다.
바닥 크기/재질/벽 색/조명 위치를 바꿔가며 자유롭게 실험해보세요.
"""

import os
import sys
import traceback

from PIL import Image
from ai2thor.controller import Controller


# 결과 이미지는 프로젝트 루트의 outputs/ 폴더에 저장 (실행 위치와 무관)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUT, exist_ok=True)

# ---- 방 크기 (여기 숫자만 바꿔도 방 크기가 바뀐다) ----
W, D, H = 4.0, 4.0, 2.5   # 폭(x), 깊이(z), 벽 높이(y)


def wall(wid, p0, p1, material):
    """바닥선 (p0 -> p1) 을 따라 높이 H 짜리 벽 하나를 만든다."""
    x0, z0 = p0
    x1, z1 = p1
    return {
        "id": wid,
        "roomId": "room|0",
        "material": {"name": material},
        "polygon": [
            {"x": x0, "y": 0.0, "z": z0},
            {"x": x1, "y": 0.0, "z": z1},
            {"x": x1, "y": H,   "z": z1},
            {"x": x0, "y": H,   "z": z0},
        ],
    }


def build_house():
    # 바닥 네 꼭짓점 (시계방향)
    c = [(0.0, 0.0), (0.0, D), (W, D), (W, 0.0)]
    return {
        "metadata": {"schema": "1.0.0"},
        "rooms": [
            {
                "id": "room|0",
                "roomType": "Bedroom",
                "floorMaterial": {"name": "PinkTile"},      # 바닥 재질
                "floorPolygon": [{"x": x, "y": 0.0, "z": z} for x, z in c],
                "ceilings": [],
                "children": [],
            }
        ],
        "walls": [
            wall("wall|0", c[0], c[1], "DrywallOrange"),
            wall("wall|1", c[1], c[2], "DrywallOrange"),
            wall("wall|2", c[2], c[3], "DrywallOrange"),
            wall("wall|3", c[3], c[0], "DrywallOrange"),
        ],
        "doors": [],
        "windows": [],
        "objects": [],   # 가구는 아래에서 SpawnAsset 으로 따로 추가
        "proceduralParameters": {
            "ceilingMaterial": {"name": "CeilingMaterial"},
            "floorColliderThickness": 1.0,
            "receptacleHeight": 0.7,
            "reflections": [],
            "skyboxId": "Sky1",
            "lights": [
                {
                    "id": "light|0",
                    "type": "point",
                    "position": {"x": W / 2, "y": H - 0.3, "z": D / 2},
                    "intensity": 1.0,
                    "range": 15.0,
                    "rgb": {"r": 1.0, "g": 1.0, "b": 1.0},
                    "shadow": {
                        "type": "Soft", "strength": 1.0, "normalBias": 0.4,
                        "bias": 0.05, "nearPlane": 0.2,
                        "resolution": "FromQualitySettings",
                    },
                }
            ],
        },
    }


def save(frame, name):
    path = os.path.join(OUT, name)
    Image.fromarray(frame).save(path)
    print(f"[저장] {path}")


def main():
    print(f"=== 커스텀 방 만들기 ({W}m x {D}m, 높이 {H}m) ===")
    controller = Controller(scene="Procedural", width=900, height=700, gridSize=0.25,
                            server_timeout=600.0)
    try:
        # 1) 방 짓기
        house = build_house()
        ev = controller.step(action="CreateHouse", house=house)
        print(f"[CreateHouse] success={ev.metadata['lastActionSuccess']} "
              f"err={ev.metadata.get('errorMessage') or '(없음)'}")

        # 2) 에이전트를 방 한가운데로 이동
        controller.step(
            action="TeleportFull",
            position={"x": W / 2, "y": 0.9, "z": D / 2},
            rotation={"x": 0, "y": 0, "z": 0},
            horizon=10, standing=True, forceAction=True,
        )

        # 3) 가구 한 개 놓아보기 (SpawnAsset). assetId 는 ProcTHOR 자산 이름.
        #    버전에 따라 자산명이 다를 수 있어 실패해도 그냥 넘어가도록 try.
        for asset_id in ["Bed_7", "Bed_1", "ArmChair_1", "Dresser_1"]:
            r = controller.step(
                action="SpawnAsset",
                assetId=asset_id,
                generatedId="my_furniture",
                position={"x": W / 2, "y": 0.0, "z": D / 2 + 1.0},
                rotation={"x": 0, "y": 0, "z": 0},
            )
            if r.metadata["lastActionSuccess"]:
                print(f"[SpawnAsset] '{asset_id}' 배치 성공")
                break
            else:
                print(f"[SpawnAsset] '{asset_id}' 실패 -> 다음 후보 시도")
        else:
            print("[SpawnAsset] 후보 자산 모두 실패 — 빈 방으로 진행 (구조는 정상)")

        # 4) 1인칭 + top-down 렌더링
        save(controller.last_event.frame, "4_custom_firstperson.png")
        cam = controller.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
        controller.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
        save(controller.last_event.third_party_camera_frames[0], "4_custom_topdown.png")

        print("\n완료: 4_custom_firstperson.png / 4_custom_topdown.png 확인하세요.")
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        controller.stop()
        print("[종료] controller.stop()")


if __name__ == "__main__":
    sys.exit(main())
