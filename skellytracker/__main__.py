from __future__ import annotations

import argparse
import sys

_TRACKERS = ("mediapipe", "rtmpose", "aruco", "charuco")


def _build_demo(tracker: str):
    # Each import is in its branch: the `detectors` and `describe` commands must not need an extra.
    if tracker == "mediapipe":
        from skellytracker.core.detectors.keypoint_detectors.mediapipe.run_demo import build_mediapipe_demo

        return build_mediapipe_demo()
    if tracker == "rtmpose":
        from skellytracker.core.detectors.keypoint_detectors.rtmpose.run_demo import build_rtmpose_demo

        return build_rtmpose_demo()
    if tracker == "aruco":
        from skellytracker.core.detectors.calibration_detectors.aruco.run_demo import build_aruco_demo

        return build_aruco_demo()
    from skellytracker.core.detectors.calibration_detectors.charuco.run_demo import build_charuco_demo

    return build_charuco_demo()


def cli_main() -> None:
    if sys.argv[1:2] and sys.argv[1] in ("detectors", "describe"):
        from skellytracker.core.detectors.cli import main

        sys.exit(main(sys.argv[1:]))
    parser = argparse.ArgumentParser(
        description="skellytracker live demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  skellytracker\n"
            "  skellytracker --tracker rtmpose\n"
            "  skellytracker --tracker aruco --camera 1\n"
            "  skellytracker detectors\n"
            "  skellytracker describe <key>\n"
            "\n"
            "for tracker-specific options (model, provider, etc.) use the tracker's module directly:\n"
            "  python -m skellytracker.core.detectors.keypoint_detectors.rtmpose.run_demo --help"
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list available trackers and exit",
    )
    parser.add_argument(
        "--tracker",
        choices=list(_TRACKERS),
        default="mediapipe",
        help="tracker to run (default: mediapipe)",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="camera index (default: 0)",
    )
    parser.add_argument(
        "--rotate",
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help="rotate incoming frames clockwise by this many degrees before tracking (default: 0)",
    )
    args = parser.parse_args()

    if args.list:
        for name in _TRACKERS:
            print(name)
        return

    demo = _build_demo(args.tracker)
    demo.run_webcam(camera_index=args.camera, rotation=args.rotate)


if __name__ == "__main__":
    cli_main()
