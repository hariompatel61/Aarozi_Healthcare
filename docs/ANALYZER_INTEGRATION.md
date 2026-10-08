# Analyzer Integration

Run analyzer connectors locally near the instruments. Do not expose analyzers directly to the public internet.

Adapter layer supports protocol-specific drivers such as ASTM/HL7/serial/TCP/file drops where the analyzer documentation supports them.

Pipeline:
receive -> validate -> persist raw message -> parse -> map machine code -> match patient/sample -> validate -> enqueue result -> technician review -> approval -> report.
