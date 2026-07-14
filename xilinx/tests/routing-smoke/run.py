#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


DEVICES = {
    "xczu2cg": {
        "part": "xczu2cg-sbva484-1-e",
        "int_tile": "INT_X29Y118",
    },
    "xcvu33p": {
        "part": "xcvu33p-fsvh2104-2-e",
        "int_tile": "INT_X135Y196",
    },
}


def run(command, log_path, env=None):
    result = subprocess.run(
        command,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    log_path.write_text(result.stdout, encoding="utf-8")
    if result.returncode:
        print(result.stdout, file=sys.stderr)
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Route UltraScale+ smoke designs")
    parser.add_argument("--device", choices=DEVICES, required=True)
    parser.add_argument("--chipdb", type=Path, required=True)
    parser.add_argument("--nextpnr", type=Path, required=True)
    parser.add_argument("--yosys", default="yosys")
    parser.add_argument("--router", choices=("router1", "router2", "both"), default="both")
    parser.add_argument("--work", type=Path)
    parser.add_argument("--require-clean-route-thrus", action="store_true")
    args = parser.parse_args()

    test_dir = Path(__file__).resolve().parent
    work_context = tempfile.TemporaryDirectory(prefix=f"{args.device}-routing-") if args.work is None else None
    work_dir = Path(work_context.name) if work_context else args.work
    work_dir.mkdir(parents=True, exist_ok=True)

    routers = ("router1", "router2") if args.router == "both" else (args.router,)
    route_thru_warnings = 0
    for design in ("passthrough", "lutff"):
        json_path = work_dir / f"{design}.json"
        yosys_script = (
            f"synth_xilinx -flatten -arch xcup -top top; write_json {json_path}"
        )
        run(
            [args.yosys, "-q", "-p", yosys_script, str(test_dir / f"{design}.v")],
            work_dir / f"{design}-yosys.log",
        )

        for router in routers:
            stem = f"{args.device}-{design}-{router}"
            fasm_path = work_dir / f"{stem}.fasm"
            log = run(
                [
                    str(args.nextpnr),
                    "--chipdb", str(args.chipdb),
                    "--json", str(json_path),
                    "--xdc", str(test_dir / f"{args.device}-{design}.xdc"),
                    "--router", router,
                    "--seed", "1",
                    "--write", str(work_dir / f"{stem}.json"),
                    "--fasm", str(fasm_path),
                ],
                work_dir / f"{stem}.log",
            )
            if router == "router2" and not re.search(
                r"overused=0 overuse=0 archfail=0", log
            ):
                raise RuntimeError(f"{stem}: router2 did not finish at zero overuse")
            if router == "router1" and "Routing complete." not in log:
                raise RuntimeError(f"{stem}: router1 did not report completion")
            warning_count = log.count("Unprocessed route-thru")
            route_thru_warnings += warning_count
            if args.require_clean_route_thrus and warning_count:
                raise RuntimeError(f"{stem}: unprocessed route-through remains")
            fasm = fasm_path.read_text(encoding="utf-8")
            if not re.search(r"^INT_X\d+Y\d+\.", fasm, re.MULTILINE):
                raise RuntimeError(f"{stem}: no routed INT PIP feature in FASM")

    graph_env = os.environ.copy()
    graph_env["INT_TILE"] = DEVICES[args.device]["int_tile"]
    graph_log = run(
        [
            str(args.nextpnr),
            "--chipdb", str(args.chipdb),
            "--run", str(test_dir / "check_int_tile.py"),
        ],
        work_dir / f"{args.device}-int-graph.log",
        env=graph_env,
    )
    print(graph_log.strip())
    print(f"ROUTE_THRU_WARNINGS count={route_thru_warnings}")
    print(f"PASS {args.device}: {', '.join(routers)} routed both designs")


if __name__ == "__main__":
    main()
