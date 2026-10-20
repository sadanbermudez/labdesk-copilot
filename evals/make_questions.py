"""Source of evals/questions.jsonl. Every gold file and required fact was checked against the 1.16.2 docs text."""
import json
I = "introduction/"
Q = [
 # id, question, gold files, must (each inner list = alternatives, regex, case-insensitive)
 ("list-resources", "How do I see which instruments are connected?", [I+"communication.rst", "index.rst"], [["list_resources"]]),
 ("list-default-filter", "What filter does list_resources use by default, and how do I list every resource?", [I+"communication.rst"], [[r"\?\*::INSTR"], [r"'\?\*'|\"\?\*\"|`\?\*`"]]),
 ("query-what", "What does the query method do?", [I+"communication.rst", "faq/migrating.rst"], [["write"], ["read"]]),
 ("timeout-units", "In what units is the instrument timeout given?", [I+"resources.rst", "faq/migrating.rst"], [["millisecond"]]),
 ("timeout-infinite", "How do I set an infinite timeout?", [I+"resources.rst"], [["None", r"inf", r"del "]]),
 ("timeout-25s", "How do I set a 25 second timeout on my device?", [I+"resources.rst"], [["25000"]]),
 ("baud-default", "What is the default baud rate for serial instruments?", [I+"communication.rst", I+"shell.rst"], [["9600"]]),
 ("baud-set", "How do I change the baud rate of a serial instrument?", [I+"communication.rst"], [["baud_rate"]]),
 ("term-attrs", "My query times out. Which attributes control the termination characters?", [I+"communication.rst", I+"resources.rst"], [["read_termination"], ["write_termination"]]),
 ("term-rs232", "What is the default read termination for RS232?", [I+"resources.rst"], [[r"\\r", "carriage return", r"\bCR\b"]]),
 ("term-common", "What termination characters are common?", [I+"communication.rst"], [[r"\\n", "line feed"], [r"\\r", "carriage return"]]),
 ("query-delay", "How do I add a pause between the write and the read of a query?", [I+"resources.rst", I+"communication.rst", "faq/migrating.rst"], [["query_delay"]]),
 ("send-end", "What does send_end do?", [I+"resources.rst"], [["EOI"]]),
 ("backend-py", "How do I use the pure Python backend instead of NI-VISA?", [I+"configuring.rst", "advanced/backends.rst", I+"getting.rst"], [["@py"]]),
 ("backend-env", "Which environment variable selects the PyVISA backend?", [I+"configuring.rst"], [["PYVISA_LIBRARY"]]),
 ("pyvisarc", "How do I make a VISA library path the default for all my PyVISA programs?", [I+"configuring.rst"], [["pyvisarc"]]),
 ("not-found", "I get 'Could not find VISA library'. What should I check?", ["faq/faq.rst", I+"getting.rst", "faq/getting_nivisa.rst"], [["configur", "pyvisarc"], ["ResourceManager", "VisaLibrary", "path"]]),
 ("bitness", "Does the Python bitness have to match the VISA library?", [I+"getting.rst", "faq/getting_nivisa.rst", "faq/faq.rst"], [["bit"], [r"\bsame\b", r"\bmatch"]]),
 ("dll-paths", "On Windows the VISA dll can't find its dependencies. How do I add extra dll search paths?", [I+"configuring.rst", "faq/faq.rst"], [["dll_extra_paths"]]),
 ("thread-safe", "Is PyVISA thread safe?", ["faq/faq.rst", "faq/migrating.rst"], [[r"1\.6"]]),
 ("logging", "How do I turn on PyVISA's logging to debug my program?", ["faq/faq.rst"], [["log_to_screen"]]),
 ("bug-report", "What should I include when I report a bug?", ["faq/faq.rst"], [["pyvisa-info"]]),
 ("com2", "What resource name do I use for an instrument on COM2?", [I+"names.rst"], [["ASRL2"]]),
 ("socket", "What is the resource name for raw TCP/IP access to port 999 at 1.2.3.4?", [I+"names.rst"], [[r"TCPIP0?::1\.2\.3\.4::999::SOCKET"]]),
 ("lan-device", "What is the default LAN device name in a TCPIP INSTR resource string?", [I+"names.rst"], [["inst0"]]),
 ("case", "Are resource names case sensitive?", [I+"names.rst"], [["insensitive", r"doesn.t matter", r"not case"]]),
 ("ascii-numpy", "How do I get the result of query_ascii_values as a numpy array?", [I+"rvalues.rst"], [["container"]]),
 ("binary-endian", "How do I read big-endian binary data with query_binary_values?", [I+"rvalues.rst"], [["is_big_endian"]]),
 ("binary-noterm", "My binary read times out because the device omits the termination character. What can I do?", [I+"rvalues.rst"], [["expect_termination"]]),
 ("ask-renamed", "My old code uses inst.ask(). What is it called now?", ["faq/migrating.rst"], [[r"\bquery\b"]]),
 ("shell-sim", "How do I start the PyVISA shell with the simulated backend?", [I+"shell.rst"], [[r"-b\s+\S*sim", r"--backend\s+\S*sim"]]),
 ("events-wait", "How do I wait for a service request event?", [I+"event_handling.rst"], [["wait_on_event"]]),
 ("backend-minimum", "What is the minimum set of functions a new backend must implement?", ["advanced/backends.rst"], [["open_default_resource_manager"], ["list_resources"]]),
 # out of scope: correct answer is the refusal sentence
 ("oos-buy", "Which oscilloscope should I buy for my lab?", [], "refuse"),
 ("oos-scpi", "What SCPI command sets the averaging on a Keysight 34465A multimeter?", [], "refuse"),
 ("oos-matlab", "How do I connect to my instrument from MATLAB?", [], "refuse"),
 ("oos-price", "How much does an NI-VISA licence cost?", [], "refuse"),
 ("oos-cooking", "What is a good recipe for paella?", [], "refuse"),
 ("oos-labview", "How do I write a LabVIEW VI to read a GPIB instrument?", [], "refuse"),
 # instrument tool
 ("tool-power", "What does the power meter read right now?", [], [[r"123\.4"], ["mW", "milliwatt"]]),
 ("tool-identity", "Is the power meter connected? What model and serial number is it?", [], [["PM100USB"], ["P2000123"]]),
]
with open("questions.jsonl", "w", encoding="utf-8") as f:
    for qid, q, gold, must in Q:
        kind = "refuse" if must == "refuse" else ("tool" if qid.startswith("tool") else "doc")
        f.write(json.dumps({"id": qid, "kind": kind, "question": q, "gold": gold, "must": [] if kind == "refuse" else must}) + "\n")
print(len(Q))
