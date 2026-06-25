"""AI2-THOR 인터랙티브 모드 — Unity 에디터처럼 창을 띄워 놓고 직접 조작.

실행하면 FloorPlan1 장면이 창으로 뜨고, 이 터미널에서 키보드로 에이전트를
계속 움직여볼 수 있다. (창을 닫지 않고 명령을 계속 받는 방식)

조작키(ai2thor 내장 interact 모드):
    w / a / s / d : 앞 / 좌회전 / 뒤 / 우회전
    위/아래 화살표 : 시선(Look) 위/아래
    + 객체 조작 키들 (집기, 열기 등) — 터미널에 안내가 출력됨
    q 또는 Ctrl-C : 종료

종료 전까지 창은 계속 떠 있다.
"""

import sys
import traceback

from ai2thor.controller import Controller


def main():
    print("=" * 60)
    print("AI2-THOR 인터랙티브 모드 시작 (FloorPlan1)")
    print("창이 뜨면 이 터미널에서 키보드로 조작하세요. q로 종료.")
    print("=" * 60)

    controller = None
    try:
        controller = Controller(
            scene="FloorPlan1",
            width=900,
            height=700,
            # 창을 보이게 띄움 (헤드리스 렌더링이 아니라 실제 윈도우)
            gridSize=0.25,
        )
        print("[OK] 장면 로드 완료. 키보드 조작을 시작합니다.")

        # ai2thor 내장 키보드 조작 루프. 창을 띄워 놓고 계속 입력을 받는다.
        controller.interact()

        print("[종료] interact 모드를 빠져나왔습니다.")
        return 0

    except KeyboardInterrupt:
        print("\n[중단] 사용자가 Ctrl-C로 종료했습니다.")
        return 0
    except Exception:
        print("=" * 60)
        print("[오류] 예외 발생:")
        traceback.print_exc()
        print("=" * 60)
        return 1
    finally:
        if controller is not None:
            controller.stop()
            print("[정리] controller.stop() 완료")


if __name__ == "__main__":
    sys.exit(main())
