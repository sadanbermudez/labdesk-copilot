"""Source of evals/heldout.jsonl: the held-out test set.

Rules for this set (see docs/03-eval-spec.md):
- Written after run 2 and committed before the system ever answered it.
- Phrased like real support tickets: symptoms and goals, not the docs' identifiers,
  and covering doc sections the development set does not.
- Never used for tuning. If a change is made because of a held-out failure, this
  set is spent and a new one must be written.
Every gold file and required fact was checked against the 1.16.2 docs text.
"""
import json

I = "introduction/"
Q = [
 # id, question, gold files, must (each inner list = alternatives, regex, case-insensitive)
 ("arch-mismatch", "Python refuses to load the VISA library and complains about the wrong architecture. How do I fix it?", ["faq/faq.rst", I+"getting.rst", "faq/getting_nivisa.rst"], [[r"match", r"same"]]),
 ("ni-endorsed", "Is PyVISA an official National Instruments product?", ["faq/faq.rst"], [[r"\bno\b", r"independent", r"not endorsed"]]),
 ("maintainer", "Who maintains PyVISA these days?", ["faq/faq.rst"], [["Dartiailh"]]),
 ("system-error", "Creating a ResourceManager fails with VI_ERROR_SYSTEM_ERROR, unknown system error. What can I try?", ["faq/faq.rst"], [["log_to_screen", "reinstall"]]),
 ("hex-ascii", "My scope sends its trace as hexadecimal numbers in ASCII. How do I get integers back?", [I+"rvalues.rst"], [["converter"], [r"['\"]x['\"]"]]),
 ("dollar-sep", "The values my device returns are separated by dollar signs instead of commas. How do I parse them?", [I+"rvalues.rst"], [["separator"]]),
 ("hp-header", "My instrument uses HP-style headers on its binary blocks. What do I change?", [I+"rvalues.rst"], [["header_fmt"], [r"\bhp\b"]]),
 ("no-header", "The binary data from my device has no header at all. How do I read it?", [I+"rvalues.rst"], [["header_fmt"], ["empty"]]),
 ("conn-lost", "Reading a large binary trace fails with VI_ERROR_CONN_LOST even though small reads work. Any workaround?", [I+"rvalues.rst"], [["chunk_size"]]),
 ("progress-bar", "Can I show a progress bar while downloading a big waveform?", [I+"rvalues.rst"], [["monitoring_interface", "tqdm"]]),
 ("keithley-buffer", "My Keithley 2000 returns its whole buffer and PyVISA can't tell how many bytes to expect. What do I do?", [I+"rvalues.rst"], [["data_points"]]),
 ("upload-ascii", "How do I send a list of numbers to my arbitrary waveform generator as text?", [I+"rvalues.rst"], [["write_ascii_values"]]),
 ("upload-binary", "How do I upload a waveform to my function generator in binary instead of text?", [I+"rvalues.rst"], [["write_binary_values"]]),
 ("default-endian", "Which byte order does PyVISA assume for binary data unless I say otherwise?", [I+"rvalues.rst"], [["little"]]),
 ("callback-srq", "Instead of waiting in a loop, I want a function of mine to run when the instrument raises a service request. How?", [I+"event_handling.rst"], [["install_handler"]]),
 ("handler-signature", "After wrapping my event handler, what arguments does it receive?", [I+"event_handling.rst"], [["resource"], ["event"], ["user_handle"]]),
 ("both-mechanisms", "Can I use the event queue and a handler at the same time?", [I+"event_handling.rst"], [[r"\ball\b"]]),
 ("install", "How do I install PyVISA?", [I+"getting.rst"], [[r"pip install"]]),
 ("vendor-free", "Do I have to pay for the NI or Keysight VISA library to use PyVISA?", [I+"getting.rst"], [["free"]]),
 ("pyvisa-py-coverage", "Does the pure Python backend support everything NI-VISA does?", [I+"getting.rst"], [["subset", "limited", r"not support"]]),
 ("dev-version", "How do I install the latest development version?", [I+"getting.rst"], [[r"git\+https"]]),
 ("closed-session", "I closed my instrument and now reading its session raises an exception. Is that expected?", [I+"resources.rst"], [["InvalidSession", "closed"]]),
 ("force-class", "PyVISA picks the wrong Python class for my serial device. Can I choose it myself?", [I+"resources.rst"], [["resource_pyclass"]]),
 ("raw-attribute", "How do I set a low-level VISA attribute that has no friendly Python name?", [I+"resources.rst"], [["set_visa_attribute"]]),
 ("shell-timeout", "In the interactive shell, how do I check the timeout and change it to 1.5 seconds?", [I+"shell.rst"], [[r"timeout 1500"]]),
 ("shell-attrs", "In the interactive shell, how do I see every VISA attribute of the instrument I opened?", [I+"shell.rst", I+"resources.rst"], [[r"\battr\b"]]),
 ("shell-no-ni", "I don't have NI-VISA installed. Can I still use the interactive shell?", [I+"shell.rst"], [[r"-b py", r"--backend py"]]),
 ("why-ms", "Why are timeouts in milliseconds rather than seconds?", ["faq/migrating.rst"], [["C-API", "LabVIEW", r"\.NET", "other VISA"]]),
 ("no-hardware", "Can I test my instrument code without the instrument connected?", [I+"shell.rst", "advanced/backends.rst"], [["sim"]]),
 ("ci-hardware", "Why can't PyVISA's own tests run against real instruments on GitHub Actions?", ["advanced/continuous_integration.rst"], [["self-hosted", "hardware", "fork"]]),
 ("class-selection", "How does PyVISA decide which kind of object open_resource returns?", [I+"resources.rst", I+"communication.rst"], [["resource name"]]),
 # out of scope: correct answer is the refusal sentence
 ("oos-kinesis", "How do I move a Thorlabs motorised stage with the Kinesis library?", [], "refuse"),
 ("oos-rigol", "What SCPI command reads channel 1 voltage on a Rigol DS1054Z?", [], "refuse"),
 ("oos-matplotlib", "How do I plot my waveform with matplotlib?", [], "refuse"),
 ("oos-fft", "Write me a Python function that computes an FFT of my trace.", [], "refuse"),
 ("oos-pinout", "What is the pinout of a GPIB cable?", [], "refuse"),
 ("oos-gpio", "How do I configure the GPIO pins on a Raspberry Pi?", [], "refuse"),
 ("oos-webfw", "Which Python web framework is best for a lab dashboard?", [], "refuse"),
 ("oos-calibrate", "How do I calibrate the power meter's wavelength correction?", [], "refuse"),
 # instrument tool
 ("tool-alive", "Is the power meter responding? Which model is it?", [], [["PM100USB"]]),
 ("tool-reading", "Give me the live reading from the PM100.", [], [[r"123\.4"]]),
 ("tool-firmware", "What firmware version is the power meter running?", [], [[r"1\.7\.0"]]),
]
with open("heldout.jsonl", "w", encoding="utf-8") as f:
    for qid, q, gold, must in Q:
        kind = "refuse" if must == "refuse" else ("tool" if qid.startswith("tool") else "doc")
        f.write(json.dumps({"id": qid, "kind": kind, "question": q, "gold": gold, "must": [] if kind == "refuse" else must}) + "\n")
print(len(Q))
