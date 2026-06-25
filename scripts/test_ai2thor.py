"""AI2-THOR (iTHOR) 동작 확인용 간단 테스트 스크립트.

- FloorPlan1 장면을 열고
- 초기 프레임을 저장한 뒤
- MoveAhead 액션을 1회 실행하고
- 에이전트 위치/회전값을 출력한 후
- 이동 후 프레임을 저장한다.
"""

import os
import sys
import traceback

from PIL import Image


# 결과 이미지는 프로젝트 루트의 outputs/ 폴더에 저장 (실행 위치와 무관)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUT, exist_ok=True)


def save_frame(event, name):
    """event.frame(RGB numpy 배열)을 PNG로 저장."""
    if event is None or event.frame is None:
        print(f"[경고] 프레임이 비어 있어 {name} 저장을 건너뜀")
        return
    path = os.path.join(OUT, name)
    Image.fromarray(event.frame).save(path)
    print(f"[저장] {path}  (shape={event.frame.shape})")


def main():
    from ai2thor.controller import Controller

    print("=" * 60)
    print("AI2-THOR iTHOR 테스트 시작")
    print(f"작업 디렉터리: {os.getcwd()}")
    print(f"DISPLAY={os.environ.get('DISPLAY')!r}")
    print("=" * 60)

    controller = None
    try:
        # FloorPlan1 장면을 800x600 해상도로 실행
        controller = Controller(
            scene="FloorPlan1",
            width=800,
            height=600,
        )
        print("[OK] Controller 실행 성공 (FloorPlan1, 800x600)")

        # 초기 RGB 프레임 저장
        event = controller.last_event
        save_frame(event, "initial_frame.png")

        # 초기 에이전트 상태 출력
        agent = event.metadata["agent"]
        print(f"[초기 위치] {agent['position']}")
        print(f"[초기 회전] {agent['rotation']}")

        # MoveAhead 액션 1회 실행
        event = controller.step(action="MoveAhead")
        success = event.metadata["lastActionSuccess"]
        print(f"[MoveAhead] 성공 여부: {success}")
        if not success:
            print(f"[MoveAhead] 실패 사유: {event.metadata.get('errorMessage')}")

        # 이동 후 에이전트 상태 출력
        agent = event.metadata["agent"]
        print(f"[이동 후 위치] {agent['position']}")
        print(f"[이동 후 회전] {agent['rotation']}")

        # 이동 후 프레임 저장
        save_frame(event, "moved_frame.png")

        print("=" * 60)
        print("테스트 완료: 정상 종료")
        print("=" * 60)
        return 0

    except Exception:
        print("=" * 60)
        print("[오류] 테스트 중 예외 발생:")
        traceback.print_exc()
        print("=" * 60)
        return 1

    finally:
        if controller is not None:
            controller.stop()
            print("[종료] controller.stop() 호출 완료")


if __name__ == "__main__":
    sys.exit(main())
