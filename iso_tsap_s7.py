#!/usr/bin/env python3

import sys
import snap7
from snap7.util import *
import subprocess
import json

# Wyłącz limit śledzenia błędów, aby Zabbix nie otrzymywał zbyt długich komunikatów w przypadku błędu
sys.tracebacklimit = 0

def get_s7_info_nmap(ip_address):
    """
    Pobiera informacje o module, sprzęcie i wersji za pomocą nmap s7-info1.nse.
    """
    try:
        # Pamiętaj, aby ścieżka do skryptu Nmap była poprawna!
        # Na podstawie Twojego `ls -la | grep s7`, uzywamy s7-info1.nse
        nmap_command = [
            "nmap", "-script", "/usr/local/share/nmap/scripts/s7-info1.nse",
            "-p", "102", ip_address
        ]
        result = subprocess.run(nmap_command, capture_output=True, text=True, check=True)
        output = result.stdout

        info = {}
        for line in output.splitlines():
            if "Module:" in line:
                info['Module'] = line.split("Module:")[1].strip()
            elif "Basic Hardware:" in line:
                info['Basic Hardware'] = line.split("Basic Hardware:")[1].strip()
            elif "Version:" in line:
                info['Version'] = line.split("Version:")[1].strip()
        return info
    except subprocess.CalledProcessError as e:
        # W przypadku błędu wykonania nmap, zwracamy słownik z informacją o błędzie
        return {"error": f"nmap execution failed: {e.stderr.strip()}"}
    except FileNotFoundError:
        # W przypadku braku nmap lub skryptu s7-info1.nse
        return {"error": "nmap or s7-info1.nse script not found. Make sure nmap is installed and s7-info1.nse is in the correct path."}
    except Exception as e:
        # Inne nieoczekiwane błędy
        return {"error": f"An unexpected error occurred during nmap processing: {e}"}

def get_s7_plc_status(ip_address):
    """
    Pobiera stan CPU i ostatni błąd za pomocą snap7.
    """
    plc = snap7.client.Client()
    try:
        # IP, rack (zazwyczaj 0), slot (zazwyczaj 0), port (domyślnie 102)
        plc.connect(ip_address, 0, 0, 102)
        if plc.get_connected():
            state = plc.get_cpu_state()
            error = plc.get_last_error()
            return {
                "CPU State": str(state), # Konwertujemy obiekt S7CpuStatus do stringa
                "Last Error": error
            }
        else:
            return {"error": "! connection failed"}
    except Exception as e:
        # Błędy połączenia lub pobierania danych przez snap7
        return {"error": f"Snap7 connection or data retrieval failed: {e}"}
    finally:
        # Ważne: zawsze rozłączaj się, aby zwolnić zasoby
        if plc.get_connected():
            plc.disconnect() # <--- POPRAWIONA LINIA: zmieniono z plc.disconnected()

def main():
    # Skrypt wymaga adresu IP i nazwy metryki jako argumentów
    if len(sys.argv) < 3:
        print("Użycie: s7_zabbix_monitor.py <IP_ADDRESS> <METRIC>", file=sys.stderr)
        print("Dostępne metryki: module, basic_hardware, version, cpu_state, last_error, all_json", file=sys.stderr)
        sys.exit(1)

    ip_address = sys.argv[1] # Pierwszy argument to adres IP
    metric = sys.argv[2].lower() # Drugi argument to nazwa metryki (np. 'cpu_state')

    # Pobieramy wszystkie dane z obu źródeł
    nmap_data = get_s7_info_nmap(ip_address)
    snap7_data = get_s7_plc_status(ip_address)

    # Łączymy wyniki obu słowników
    all_data = {**nmap_data, **snap7_data}

    result = None
    # Sprawdzamy, którą metrykę użytkownik zażądał
    if metric == 'module':
        result = all_data.get('Module', 'N/A')
    elif metric == 'basic_hardware':
        result = all_data.get('Basic Hardware', 'N/A')
    elif metric == 'version':
        result = all_data.get('Version', 'N/A')
    elif metric == 'cpu_state': # <--- POPRAWIONA LINIA: zmieniono z metic na metric
        result = all_data.get('CPU State', 'N/A')
    elif metric == 'last_error':
        result = all_data.get('Last Error', 'N/A')
    elif metric == 'all_json': # Opcja na zwrócenie wszystkiego w JSON (dla LLD lub testów)
        print(json.dumps(all_data, indent=2)) # Drukujemy sformatowany JSON
        sys.exit(0)
    else:
        print(f"Nieznana metryka: {metric}", file=sys.stderr)
        sys.exit(1)

    # Obsługa błędów i braków danych
    if isinstance(result, str) and ("error" in result.lower() or result == 'N/A'):
        # Jeśli wynik zawiera "error" lub jest "N/A", drukujemy na stderr i wychodzimy z błędem
        print(f"Error or data not available for {metric}: {result}", file=sys.stderr)
        sys.exit(1)
    else:
        # W przeciwnym razie drukujemy wynik na stdout (co Zabbix odczyta) i wychodzimy sukcesem
        print(result)
        sys.exit(0)

if __name__ == "__main__":
    main()