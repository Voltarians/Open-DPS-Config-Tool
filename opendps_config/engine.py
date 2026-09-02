from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"\s*(!|&|\||\(|\)|[A-Za-z0-9_]+)")


class ConfigError(ValueError):
    pass


class ExpressionParser:
    def __init__(self, expression: str, present_rpos: set[str]):
        self.tokens = [m.group(1) for m in TOKEN_RE.finditer(expression)]
        compact = re.sub(r"\s+", "", expression)
        if "".join(self.tokens) != compact:
            raise ConfigError(f"Unsupported expression syntax: {expression}")
        self.pos = 0
        self.present = {x.upper() for x in present_rpos}

    def parse(self) -> bool:
        if not self.tokens:
            raise ConfigError("Empty RPO expression")
        result = self._or_expr()
        if self.pos != len(self.tokens):
            raise ConfigError(f"Unexpected token: {self.tokens[self.pos]}")
        return result

    def _or_expr(self) -> bool:
        result = self._and_expr()
        while self._peek("|"):
            self.pos += 1
            rhs = self._and_expr()
            result = result or rhs
        return result

    def _and_expr(self) -> bool:
        result = self._unary()
        while self._peek("&"):
            self.pos += 1
            rhs = self._unary()
            result = result and rhs
        return result

    def _unary(self) -> bool:
        if self._peek("!"):
            self.pos += 1
            return not self._unary()
        if self._peek("("):
            self.pos += 1
            result = self._or_expr()
            if not self._peek(")"):
                raise ConfigError("Missing closing parenthesis")
            self.pos += 1
            return result
        if self.pos >= len(self.tokens):
            raise ConfigError("Unexpected end of expression")
        token = self.tokens[self.pos]
        if token in {"&", "|", ")"}:
            raise ConfigError(f"Unexpected token: {token}")
        self.pos += 1
        return token.upper() in self.present

    def _peek(self, token: str) -> bool:
        return self.pos < len(self.tokens) and self.tokens[self.pos] == token


def evaluate_expression(expression: str, present_rpos: Iterable[str]) -> bool:
    return ExpressionParser(expression, set(present_rpos)).parse()


def parse_rpos(text: str) -> set[str]:
    cleaned = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
    return {token.upper() for token in re.findall(r"[A-Za-z0-9]{2,5}", cleaned)}


def _text(node: ET.Element, path: str, default: str = "") -> str:
    found = node.find(path)
    return (found.text or "").strip() if found is not None else default


def _set_bits(payload: bytearray, start_byte: int, start_bit: int, bit_length: int, value: int) -> None:
    if start_byte < 0 or start_bit < 0 or start_bit > 7 or bit_length < 1:
        raise ConfigError("Invalid byte/bit coordinates")
    if value >= (1 << bit_length):
        raise ConfigError(f"Value {value} does not fit in {bit_length} bits")
    for offset in range(bit_length):
        absolute = start_byte * 8 + start_bit + offset
        byte_index, bit_index = divmod(absolute, 8)
        if byte_index >= len(payload):
            raise ConfigError("Parameter extends beyond DID payload")
        mask = 1 << bit_index
        if value & (1 << offset):
            payload[byte_index] |= mask
        else:
            payload[byte_index] &= ~mask


def _get_bits(payload: bytes | bytearray, start_byte: int, start_bit: int, bit_length: int) -> int:
    value = 0
    for offset in range(bit_length):
        absolute = start_byte * 8 + start_bit + offset
        byte_index, bit_index = divmod(absolute, 8)
        if byte_index >= len(payload):
            raise ConfigError("Parameter extends beyond DID payload")
        if payload[byte_index] & (1 << bit_index):
            value |= 1 << offset
    return value


@dataclass
class ConfigurationModel:
    path: Path
    root: ET.Element

    @classmethod
    def load(cls, path: str | Path) -> "ConfigurationModel":
        source = Path(path)
        root = ET.parse(source).getroot()
        if root.tag != "ConfigurationModule":
            raise ConfigError(f"Unsupported root element: {root.tag}")
        if root.find("Header") is None or root.find("DidList") is None:
            raise ConfigError("Missing required configuration sections")
        return cls(source, root)

    def summary(self) -> dict:
        h = self.root.find("Header")
        pin = h.find("Protocol/PhysicalLayer/Pin")
        return {
            "schema_version": self.root.attrib.get("ECU-CONFIG-SCHEMA-VERSION"),
            "ecu_name": _text(h, "EcuName"),
            "diagnostic_address": _text(h, "DiagnosticAddress"),
            "part_number": _text(h, "PartNumber"),
            "alpha_code": _text(h, "AlphaCode"),
            "security_access": _text(h, "useSecurityAccess") == "true",
            "security_algorithm_table": _text(h, "SecurityAlgoTableNo"),
            "security_algorithm": _text(h, "SecurityAlgoNo"),
            "application_layer": _text(h, "Protocol/ApplicationLayer"),
            "physical_layer": _text(h, "Protocol/PhysicalLayer/PhysicalLayerSpec"),
            "physical_signal": pin.attrib.get("PhysicalLayerSignalName") if pin is not None else None,
            "dlc_pin": pin.attrib.get("PinNumber") if pin is not None else None,
            "did_count": len(self.root.findall("DidList/DidItem")),
            "parameter_count": len(self.root.findall("ModificationSection/ModificationItem/Parameter")),
            "rpo_count": len(self.root.findall("RpoList/RpoCodeItem")),
            "write_count": len(self.root.findall("WriteSection/WriteItem")),
        }

    def _did_nodes(self) -> dict[str, ET.Element]:
        return {_text(d, "ID"): d for d in self.root.findall("DidList/DidItem")}

    def _normalize_readback(self, readback: dict[str, str] | None) -> dict[str, bytearray]:
        if not readback:
            return {}
        did_nodes = self._did_nodes()
        aliases = {}
        for did_id, node in did_nodes.items():
            number = _text(node, "DidNo").upper()
            aliases[did_id.upper()] = did_id
            aliases[number] = did_id
            aliases[f"0X{number}"] = did_id
        normalized = {}
        for key, raw in readback.items():
            did_id = aliases.get(str(key).upper())
            if not did_id:
                raise ConfigError(f"Unknown DID in readback: {key}")
            try:
                payload = bytearray.fromhex(str(raw).replace(" ", ""))
            except ValueError as exc:
                raise ConfigError(f"Invalid payload hex for {key}") from exc
            expected = int(_text(did_nodes[did_id], "DidLength"))
            if len(payload) != expected:
                raise ConfigError(f"{key} readback is {len(payload)} bytes; expected {expected}")
            normalized[did_id] = payload
        return normalized

    def decode_did(self, did: str, payload_hex: str) -> dict:
        nodes = self._did_nodes()
        target_id = None
        wanted = did.upper().removeprefix("0X")
        for did_id, node in nodes.items():
            if wanted in {did_id.upper(), _text(node, "DidNo").upper()}:
                target_id = did_id
                break
        if not target_id:
            raise ConfigError(f"Unknown DID: {did}")
        payload = self._normalize_readback({target_id: payload_hex})[target_id]
        fields = []
        mod = self.root.find(f'ModificationSection/ModificationItem[@IDREF="{target_id}"]')
        if mod is not None:
            for parameter in mod.findall("Parameter"):
                value = _get_bits(payload, int(_text(parameter, "StartByte")),
                                  int(_text(parameter, "StartBit")), int(_text(parameter, "BitLength")))
                value_hex = f'{value:0{max(2, (int(_text(parameter, "BitLength")) + 3) // 4)}X}'
                interpretation = None
                for item in parameter.findall("ServiceSection/Interpretation"):
                    if item.attrib.get("Value", "").upper() == value_hex:
                        interpretation = item.attrib.get("Text")
                        break
                fields.append({
                    "parameter": _text(parameter, "ParameterName"),
                    "start_byte": int(_text(parameter, "StartByte")),
                    "start_bit": int(_text(parameter, "StartBit")),
                    "bit_length": int(_text(parameter, "BitLength")),
                    "value_hex": value_hex,
                    "interpretation": interpretation,
                })
        return {"did_id": target_id, "did": _text(nodes[target_id], "DidNo"),
                "payload_hex": payload.hex().upper(), "fields": fields}

    def generate_plan(self, present_rpos: set[str], readback: dict[str, str] | None = None) -> dict:
        did_nodes = self._did_nodes()
        vehicle_payloads = self._normalize_readback(readback)
        payloads = {}
        baseline_source = {}
        changes = []
        warnings = []
        for did_id, d in did_nodes.items():
            default_hex = _text(d, "DefaultValue")
            expected = int(_text(d, "DidLength", "0"))
            try:
                payload = bytearray.fromhex(default_hex)
            except ValueError as exc:
                raise ConfigError(f"Invalid default hex for {did_id}") from exc
            if len(payload) != expected:
                raise ConfigError(f"{did_id} default is {len(payload)} bytes; expected {expected}")
            if did_id in vehicle_payloads:
                payloads[did_id] = bytearray(vehicle_payloads[did_id])
                baseline_source[did_id] = "vehicle_readback"
            else:
                payloads[did_id] = payload
                baseline_source[did_id] = "xml_default"

        for mod in self.root.findall("ModificationSection/ModificationItem"):
            did_id = mod.attrib["IDREF"]
            for parameter in mod.findall("Parameter"):
                conf = parameter.find("ConfData")
                if conf is None or conf.attrib.get("useConfData") != "true":
                    continue
                matches = []
                for rule in conf.findall("ConfigData"):
                    expression = rule.attrib.get("AutoGenExpression", "")
                    if evaluate_expression(expression, present_rpos):
                        matches.append(rule)
                name = _text(parameter, "ParameterName")
                if len(matches) > 1:
                    warnings.append(f"{did_id}/{name}: multiple rules matched; XML order used")
                if not matches:
                    continue
                rule = matches[-1]
                value_hex = rule.attrib["Value"]
                value = int(value_hex, 16)
                _set_bits(payloads[did_id], int(_text(parameter, "StartByte")),
                          int(_text(parameter, "StartBit")), int(_text(parameter, "BitLength")), value)
                changes.append({
                    "did_id": did_id,
                    "did": _text(did_nodes[did_id], "DidNo"),
                    "parameter": name,
                    "expression": rule.attrib.get("AutoGenExpression", ""),
                    "value": value_hex,
                })

        write_order = [w.attrib["IDREF"] for w in self.root.findall("WriteSection/WriteItem")]
        payload_rows = []
        change_only = []
        for i, did_id in enumerate(write_order):
            calculated = payloads[did_id].hex().upper()
            current = vehicle_payloads.get(did_id)
            current_hex = current.hex().upper() if current is not None else None
            changed = current is not None and current_hex != calculated
            row = {"write_order": i + 1, "did_id": did_id,
                   "did": _text(did_nodes[did_id], "DidNo"),
                   "baseline_source": baseline_source[did_id],
                   "current_payload_hex": current_hex,
                   "calculated_payload_hex": calculated,
                   "changed_from_vehicle": changed,
                   "delay_ms": int(self.root.find(f'WriteSection/WriteItem[@IDREF="{did_id}"]').attrib.get("DelayForMS", "0"))}
            payload_rows.append(row)
            if changed:
                change_only.append(row)
        missing = [_text(did_nodes[x], "DidNo") for x in write_order if x not in vehicle_payloads]
        return {
            "tool": "OpenDPS Config Tool",
            "mode": "offline-plan-only",
            "source_xml": self.path.name,
            "source_sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(),
            "target": self.summary(),
            "present_rpos": sorted(present_rpos),
            "matched_rule_count": len(changes),
            "matched_rules": changes,
            "payloads": payload_rows,
            "change_only": change_only,
            "readback_coverage": {"provided": len(vehicle_payloads), "required": len(write_order),
                                  "missing_dids": missing, "complete": not missing},
            "warnings": warnings + ([
                "One or more payloads start from XML defaults because vehicle readback is incomplete.",
                "This plan must not be used as an ECU backup or written without independent validation.",
            ] if missing else ["Vehicle readback is complete; independent validation is still required before writing."]),
        }

    def compare(self, present_rpos: set[str], readback: dict[str, str]) -> dict:
        vehicle = self._normalize_readback(readback)
        plan = self.generate_plan(present_rpos, readback)
        nodes = self._did_nodes()
        comparisons = []
        for row in plan["payloads"]:
            did_id = row["did_id"]
            default_hex = _text(nodes[did_id], "DefaultValue").upper()
            current_hex = row["current_payload_hex"]
            calculated_hex = row["calculated_payload_hex"]
            comparisons.append({
                "did": row["did"], "did_id": did_id,
                "current": current_hex, "xml_default": default_hex,
                "rpo_calculated": calculated_hex,
                "current_vs_default": None if current_hex is None else current_hex != default_hex,
                "current_vs_calculated": None if current_hex is None else current_hex != calculated_hex,
                "calculated_vs_default": calculated_hex != default_hex,
                "current_decoded": None if did_id not in vehicle else self.decode_did(did_id, current_hex)["fields"],
            })
        return {"target": self.summary(), "present_rpos": sorted(present_rpos),
                "readback_coverage": plan["readback_coverage"],
                "comparisons": comparisons, "change_only": plan["change_only"],
                "warnings": plan["warnings"]}


def write_bundle(xml_path: Path, rpos: set[str], output: Path, readback: dict[str, str] | None = None) -> dict:
    model = ConfigurationModel.load(xml_path)
    plan = model.generate_plan(rpos, readback)
    plan_bytes = (json.dumps(plan, indent=2) + "\n").encode()
    build_bytes = ("# Normalized RPO list\n" + " ".join(sorted(rpos)) + "\n").encode()
    manifest = {
        "format": "opendps-config-bundle",
        "format_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "files": {
            xml_path.name: hashlib.sha256(xml_path.read_bytes()).hexdigest(),
            "build-record.txt": hashlib.sha256(build_bytes).hexdigest(),
            "configuration-plan.json": hashlib.sha256(plan_bytes).hexdigest(),
        },
        "notice": "Offline engineering bundle; not a GM DPS Type-4 archive.",
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted({xml_path.name: xml_path.read_bytes(),
                                  "build-record.txt": build_bytes,
                                  "configuration-plan.json": plan_bytes,
                                  "manifest.json": manifest_bytes}.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return plan
