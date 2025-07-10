<b>Siemens S7 PLC Monitoring for Zabbix</b>

This repository provides a custom Python script and a Zabbix template for comprehensive monitoring of Siemens S7 PLCs. The solution leverages both nmap (with s7-info1.nse) and python-snap7 to gather detailed information about the PLC's hardware, CPU state, and error logs, integrating these insights into Zabbix for robust industrial automation monitoring.

Table of Contents:

1. iso_tsap_s7.py Script
2. Zabbix Template
3. Requirements
4. Installation
5. Monitored Items
6. Triggers
7. Graphs
8. Dashboards


iso_tsap_s7.py Script

The iso_tsap_s7.py script is a custom Python tool designed to extract various operational and diagnostic parameters from Siemens S7 PLCs. It combines two main methods for data acquisition: nmap with the s7-info1.nse script and the python-snap7 library.

Script Functionality

The iso_tsap_s7.py script performs the following key operations:

- Nmap (s7-info1.nse) Integration:
    Uses nmap to run the s7-info1.nse script against the target PLC's IP address on port 102 (ISO-TSAP).
    Parses nmap's output to extract high-level information such as:
        Module: PLC module type.
        Basic Hardware: Basic hardware configuration details.
        Version: Firmware version.
        Last Error: The last recorded error code (if available via nmap).
        CPU State: Current CPU operating state (e.g., RUN, STOP).
- python-snap7 Library Integration:
    Connects to the PLC using the python-snap7 library.
    Retrieves more detailed diagnostic information directly from the PLC, including:
        CPU State: Confirms the CPU's operational state.
        Last Error: Detailed last error information from the PLC's diagnostic buffer.
        Module: Confirms module details.
- Data Consolidation: Merges the information obtained from both nmap and snap7 into a single dictionary.
- Metric Extraction: Based on the command-line argument (metric), it returns a specific piece of information (e.g., 'module', 'cpu_state', 'last_error', 'basic_hardware', 'version').
- JSON Output (for LLD/Debugging): Supports an all_json metric to output all collected data in a formatted JSON string, useful for Low-Level Discovery (LLD) or debugging.
- Error Handling: Includes mechanisms to catch connection errors, nmap execution failures, and issues during snap7 communication, returning informative error messages.
- Traceback Limiting: Disables full traceback printing (sys.tracebacklimit = 0) to prevent excessively long error messages in Zabbix logs.

Script Usage:
The script is designed to be executed by the Zabbix agent as a UserParameter or ExternalCheck.

python3 iso_tsap_s7.py <ip_address> <metric>

Parameters:

  <ip_address>: The IP address of the Siemens S7 PLC.

  <metric>: The specific data point to retrieve. Supported metrics include:

  module
  basic_hardware
  version
  cpu_state
  last_error
  all_json (for debugging/LLD, outputs all data as JSON)

Example:
python3 /etc/zabbix/scripts/iso_tsap_s7.py 192.168.10.1 cpu_state

Zabbix Template:
The Iso-Tsap_S7_Siemens S7 PLC.xml template integrates the data collected by the iso_tsap_s7.py script into Zabbix. It defines items, triggers, and graphs to monitor the critical aspects of Siemens S7 PLCs.

Requirements:
Zabbix Server (version 7.0 or higher recommended)
Zabbix Agent (on the machine that will execute the Python script and connect to PLCs)
Python 3 installed on the Zabbix Agent host.
python-snap7 library installed on the Zabbix Agent host:

    pip install python-snap7
    
nmap installed on the Zabbix Agent host.
s7-info1.nse Nmap script present in the Nmap scripts directory (e.g., /usr/local/share/nmap/scripts/).
Siemens S7 PLC accessible via network from the Zabbix Agent host (Port 102/TCP must be open on the PLC).

Installation:
Script Installation

  Place the script: Copy the iso_tsap_s7.py script to a directory accessible by the Zabbix agent, e.g., /etc/zabbix/scripts/.

  Set permissions: Ensure the script has execute permissions:
  
    chmod +x /etc/zabbix/scripts/iso_tsap_s7.py

Verify Nmap script path: Ensure that s7-info1.nse is correctly located (e.g., /usr/local/share/nmap/scripts/s7-info1.nse) as referenced in the iso_tsap_s7.py script. If its location differs, update the nmap_command list within the Python script accordingly.

Zabbix Agent UserParameter Configuration

Add the following lines to your Zabbix agent configuration file (zabbix_agentd.conf or a file in zabbix_agentd.d/):
Ini, TOML

UserParameter=s7_zabbix_monitor.py[*],/usr/bin/python3 /etc/zabbix/scripts/iso_tsap_s7.py "$1" "$2"

  Note: Adjust the python3 command path (/usr/bin/python3) and script path (/etc/zabbix/scripts/) to match your system's configuration.

  Restart Zabbix Agent:
    sudo systemctl restart zabbix-agent

Template Installation:

Download Template: Download the Iso-Tsap_S7_Siemens S7 PLC.xml file from this repository.
Import into Zabbix:
    Navigate to Configuration -> Templates in your Zabbix frontend.
    Click Import in the top right corner.
    Click Browse and select the Iso-Tsap_S7_Siemens S7 PLC.xml file.
    Click Import.

Host Configuration:

- Create/Select Host: Go to Configuration -> Hosts. Create a new host or select an existing one representing your Siemens S7 PLC.
- Add Zabbix Agent Interface: Ensure the host has a Zabbix Agent interface configured, pointing to the IP address of the machine where the iso_tsap_s7.py script is running.
- Link Template:
    - Go to the Templates tab of the host configuration.
    - In the Link new templates section, search for Monitoring Siemens S7 PLC and select it.
    - Click Add, then click Update on the host configuration page.
- Host IP (for Script Argument): The template uses the {HOST.CONN} macro, which defaults to the host's primary Zabbix Agent interface IP address. Ensure this IP is the one the Zabbix agent uses to connect to the PLC.

Monitored Items:
The template defines the following items to collect data from the Siemens S7 PLC:

- S7 Basic Hardware: s7_zabbix_monitor.py["{HOST.CONN}", "basic_hardware"] (Type: External check, Value type: Text, Updates every 1 hour)
- S7 CPU State: s7_zabbix_monitor.py["{HOST.CONN}", "cpu_state"] (Type: External check, Value type: Text, Updates every 1 minute)
- S7 Last Error Code: s7_zabbix_monitor.py["{HOST.CONN}", "last_error"] (Type: External check, Value type: Numeric (unsigned), Updates every 1 minute)
- S7 Module: s7_zabbix_monitor.py["{HOST.CONN}", "module"] (Type: External check, Value type: Text, Updates every 1 hour)
- S7 Version: s7_zabbix_monitor.py["{HOST.CONN}", "version"] (Type: External check, Value type: Text, Updates every 1 hour)

Triggers:
The template includes triggers to alert on important changes or issues with the PLC:

- S7 PLC: Hardware configuration has changed: Triggers if the "S7 Basic Hardware" or "S7 Module" item values change (Priority: WARNING, Manual close: YES).
- S7 PLC: CPU State is not RUN: Triggers if the "S7 CPU State" is not "RUN" (Priority: HIGH).
- S7 PLC: Last Error Code ({ITEM.LASTVALUE}): Triggers if "S7 Last Error Code" is not 0 (indicating an error) (Priority: WARNING).
- S7 PLC: No data for 5 minutes: Triggers if "S7 CPU State" or "S7 Last Error Code" hasn't received data for 5 minutes (Priority: DISASTER).

Graphs:
The template provides a graph for visualizing error codes:

- S7 Last Error Code: Displays the "S7 Last Error Code" over time.

Dashboards:
The template includes a basic dashboard for a quick overview of the PLC status:

S7 PLC Overview:
- CPU State: Displays the current CPU state.
- Last Error Code: Shows the last error code.
- Module: Displays the PLC module type.
- Hardware Config: Shows the basic hardware configuration.
- Firmware Version: Displays the firmware version.
