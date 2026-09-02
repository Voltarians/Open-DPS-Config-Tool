from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import ConfigurationModel, parse_rpos, write_bundle


def _rpos(args) -> set[str]:
    values = parse_rpos(args.rpos or "")
    if getattr(args, "build_record", None):
        values |= parse_rpos(Path(args.build_record).read_text(encoding="utf-8"))
    return values


def _readback(path: str | None) -> dict[str, str] | None:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(v, str) for v in data.values()):
        raise ValueError("Readback JSON must map DID names/numbers to hexadecimal strings")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(prog="opendps-config")
    commands = parser.add_subparsers(dest="command", required=True)

    inspect = commands.add_parser("inspect", help="Inspect a DPS ECU configuration XML")
    inspect.add_argument("xml")

    plan = commands.add_parser("plan", help="Generate an offline configuration plan")
    plan.add_argument("xml")
    plan.add_argument("--rpos", default="")
    plan.add_argument("--build-record")
    plan.add_argument("--output")
    plan.add_argument("--readback", help="JSON map of DID to current payload hex")

    decode = commands.add_parser("decode", help="Decode one DID payload")
    decode.add_argument("xml")
    decode.add_argument("--did", required=True)
    decode.add_argument("--payload", required=True)

    compare = commands.add_parser("compare", help="Compare current, default, and RPO-calculated data")
    compare.add_argument("xml")
    compare.add_argument("--rpos", default="")
    compare.add_argument("--build-record")
    compare.add_argument("--readback", required=True)
    compare.add_argument("--output")

    bundle = commands.add_parser("bundle", help="Create an offline configuration bundle")
    bundle.add_argument("xml")
    bundle.add_argument("--rpos", default="")
    bundle.add_argument("--build-record")
    bundle.add_argument("--output", required=True)
    bundle.add_argument("--readback", help="Optional JSON map of current DID payloads")

    args = parser.parse_args()
    model = ConfigurationModel.load(args.xml)
    if args.command == "inspect":
        result = model.summary()
    elif args.command == "plan":
        result = model.generate_plan(_rpos(args), _readback(args.readback))
    elif args.command == "decode":
        result = model.decode_did(args.did, args.payload)
    elif args.command == "compare":
        result = model.compare(_rpos(args), _readback(args.readback) or {})
    else:
        result = write_bundle(Path(args.xml), _rpos(args), Path(args.output), _readback(args.readback))
    rendered = json.dumps(result, indent=2) + "\n"
    if getattr(args, "output", None) and args.command in {"plan", "compare"}:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
