"""Read-only tool for the lab power meter.

By default it talks to a simulated Thorlabs PM100USB (pyvisa-sim), so the whole
system runs and is tested without hardware. Set LABDESK_VISA_BACKEND to a real
backend ("@ivi" or "@py") and LABDESK_POWER_METER to the resource name to use a
real meter; the code path is the same.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pyvisa

SIM_FILE = Path(__file__).with_name("pm100_sim.yaml")
SIM_RESOURCE = "USB0::0x1313::0x8078::P2000123::INSTR"


@dataclass
class Reading:
    ok: bool
    resource: str
    identity: str = ""
    power_mw: float | None = None
    error: str = ""

    def as_passage(self) -> str:
        if not self.ok:
            return f"Instrument tool: could not read {self.resource}: {self.error}"
        vendor, model, serial, firmware = (self.identity.split(",") + ["", "", "", ""])[:4]
        return (
            f"Instrument tool, live reading from {self.resource}: "
            f"identity '{self.identity}' (vendor {vendor}, model {model}, serial {serial}, firmware {firmware}); "
            f"measured power {self.power_mw:.1f} mW."
        )


def read_power_meter() -> Reading:
    backend = os.environ.get("LABDESK_VISA_BACKEND", f"{SIM_FILE}@sim")
    resource = os.environ.get("LABDESK_POWER_METER", SIM_RESOURCE)
    try:
        rm = pyvisa.ResourceManager(backend)
        try:
            inst = rm.open_resource(resource, read_termination="\n", write_termination="\n", timeout=3000)
            identity = inst.query("*IDN?").strip()
            watts = float(inst.query("MEAS:POW?"))
            inst.close()
        finally:
            rm.close()
        return Reading(True, resource, identity, watts * 1000)
    except Exception as exc:  # the tool reports failures as text; it never crashes the chat
        return Reading(False, resource, error=f"{type(exc).__name__}: {exc}")
