"""[2] 기본 방 렌더링 — iTHOR 내장 장면을 열고 이미지로 저장.

AI2-THOR에는 미리 만들어진 120개의 사실적인 실내 장면(FloorPlan*)이 들어 있다.
  - FloorPlan1  ~ FloorPlan30  : 주방(Kitchen)
  - FloorPlan201~FloorPlan230  : 거실(Living room)
  - FloorPlan301~FloorPlan330  : 침실(Bedroom)
  - FloorPlan401~FloorPlan430  : 욕실(Bathroom)

이 스크립트는 그 중 하나를 열어서
  (1) 에이전트 1인칭 시점 프레임,
  (2) 방 전체를 위에서 내려다보는 top-down 뷰
를 PNG로 저장한다.
"""

import os
import sys
import traceback

from PIL import Image
from ai2thor.controller import Controller


SCENE = "FloorPlan1"   # 원하는 장면으로 바꿔보세요 (예: FloorPlan201, FloorPlan301)

# 결과 이미지는 프로젝트 루트의 outputs/ 폴더에 저장 (실행 위치와 무관)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUT, exist_ok=True)


def save(frame, name):
    path = os.path.join(OUT, name)
    Image.fromarray(frame).save(path)
    print(f"[저장] {path}  shape={frame.shape}")


def main():
    print(f"=== 기본 방 렌더링: {SCENE} ===")
    # server_timeout 을 크게: GPU 드라이버가 없어 소프트웨어 렌더링(llvmpipe)이라 느림
    controller = Controller(scene=SCENE, width=900, height=700, gridSize=0.25,
                            server_timeout=600.0)
    try:
        # (1) 에이전트 1인칭 시점
        event = controller.last_event
        save(event.frame, "2_firstperson.png")

        # (2) 방 전체 top-down 뷰 — 별도 카메라를 띄워서 위에서 내려다본다
        cam = controller.step(action="GetMapViewCameraProperties").metadata["actionReturn"]
        event = controller.step(action="AddThirdPartyCamera", skyboxColor="white", **cam)
        save(event.third_party_camera_frames[0], "2_topdown.png")

        # 장면 안에 어떤 물체들이 있는지 몇 개만 출력
        objs = controller.last_event.metadata["objects"]
        print(f"[정보] 이 방의 물체 수: {len(objs)}")
        print("[정보] 예시 물체:", [o["objectType"] for o in objs[:12]])
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        controller.stop()
        print("[종료] controller.stop()")


if __name__ == "__main__":
    sys.exit(main())
