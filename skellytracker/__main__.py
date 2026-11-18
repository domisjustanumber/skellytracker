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
    if sys.argv[1:2] and sys.argv[1] in ("run", "validate", "nodes"):
        from skellytracker.core.pipelines.cli import main

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
            "  skellytracker --pipeline mediapipe-holistic-tasks@skellytracker\n"
            "  skellytracker run --pipeline <key> --coco <annotations.json> --images <dir> --out <dir>\n"
            "  skellytracker validate <pipeline file or key>\n"
            "  skellytracker nodes\n"
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
    parser.add_argument(
        "--pipeline",
        default=None,
        metavar="KEY_OR_FILE",
        help="run this pipeline on the camera, in place of --tracker: a key of the pipeline catalog or a pipeline file",
    )
    parser.add_argument("--ep", default=None, help="with --pipeline: a key of the EP catalog (default: the recommended EP)")
    parser.add_argument("--ep-option", action="append", metavar="NAME=VALUE", help="with --pipeline: one EP option; repeatable")
    parser.add_argument("--device", action="append", metavar="KEY", help="with --pipeline: one GPU key; repeatable")
    parser.add_argument("--cpu-threads", type=int, default=None, metavar="N", help="with --pipeline: the threads of each session on the CPU EP")
    parser.add_argument("--preprocess", choices=["auto", "cpu", "gpu"], default="auto", help="with --pipeline: the place of the preprocess")
    args = parser.parse_args()

    if args.list:
        for name in _TRACKERS:
            print(name)
        return

    if args.pipeline is not None:
        from skellytracker.core.pipelines.cli import demo_main

        sys.exit(demo_main(args.pipeline, camera=args.camera, rotation=args.rotate, ep=args.ep, ep_option=args.ep_option, device=args.device,
                           cpu_threads=args.cpu_threads, preprocess=args.preprocess))
    if args.ep is not None or args.ep_option or args.device or args.cpu_threads is not None or args.preprocess != "auto":
        parser.error("--ep, --ep-option, --device, --cpu-threads and --preprocess need --pipeline")

    demo = _build_demo(args.tracker)
    demo.run_webcam(camera_index=args.camera, rotation=args.rotate)


if __name__ == "__main__":
    cli_main()
