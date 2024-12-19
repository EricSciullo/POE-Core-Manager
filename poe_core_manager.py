import os
import re
import psutil
import logging
from time import sleep
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S"
)
logger = logging.getLogger()

FALLBACK_GAME_PATH = r"C:\Program Files (x86)\Grinding Gear Games\Path of Exile 2"
START_GAME_PATTERN = r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} \d+ [a-fA-F0-9]+ \[INFO Client \d+\] \[ENGINE\] Init$"
START_LOAD_PATTERN = r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} \d+ [a-fA-F0-9]+ \[INFO Client \d+\] \[SHADER\] Delay: OFF$"
END_LOAD_PATTERN = r"^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} \d+ [a-fA-F0-9]+ \[INFO Client \d+\] \[SHADER\] Delay: ON$"

def get_path_of_exile_process():
    """Finds the Path of Exile 2 process."""
    for proc in psutil.process_iter(attrs=["pid", "name", "exe", "cmdline"]):
        try:
            if "PathOfExile" in proc.info["name"] and "Path of Exile 2" in proc.info["cmdline"][0]:
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def wait_for_executable_to_launch():
    """Waits for the Path of Exile 2 process to start."""
    logger.info("Waiting for Path of Exile process to launch before doing anything.")
    while True:
        proc = get_path_of_exile_process()
        if proc and proc.is_running():
            return proc
        sleep(1)

def park_cores(proc):
    """Parks only the first two CPU cores, leaving the rest active."""
    num_cores = os.cpu_count()
    if num_cores is None:
        logger.error("Unable to determine CPU count.")
        return

    # Generate list of active cores excluding the first two
    active_cores = list(range(2, num_cores))
    try:
        proc.cpu_affinity(active_cores)  # Set affinity to exclude the first two cores
        logger.info("Parked first two cores: Active cores are now %s", active_cores)
    except psutil.AccessDenied:
        logger.error("Failed to set processor affinity. Access denied.")
    except psutil.NoSuchProcess:
        logger.error("Process not found to park cores.")

def resume_cores(proc):
    """Restores all CPU cores."""
    num_cores = os.cpu_count()
    if num_cores is None:
        logger.error("Unable to determine CPU count.")
        return
    
    try:
        proc.cpu_affinity(list(range(num_cores)))
        logger.info("Unparked all cores: All %d cores are now active", num_cores)
    except psutil.AccessDenied:
        logger.error("Failed to reset processor affinity. Access denied.")
    except psutil.NoSuchProcess:
        logger.error("Process not found to unpark cores.")


# Main Script
proc = get_path_of_exile_process()
if not proc:
    proc = wait_for_executable_to_launch()
    park_cores(proc)

game_directory = Path(proc.exe()).parent if proc else Path(FALLBACK_GAME_PATH)
client_txt_location = game_directory / "logs" / "client.txt"

logger.info("Reading client data from %s", client_txt_location)

try:
    with open(client_txt_location, "r", encoding="utf-8", errors="ignore") as file:
        file.seek(0, os.SEEK_END)
        while proc.is_running():
            line = file.readline()
            if not line:
                sleep(0.02)
                continue
            
            line = line.strip()
            if len(line) > 256:
                continue

            if re.match(START_LOAD_PATTERN, line) or re.match(START_GAME_PATTERN, line):
                park_cores(proc)
            elif re.match(END_LOAD_PATTERN, line):
                resume_cores(proc)
except FileNotFoundError:
    logger.error("Client.txt not found at %s.", client_txt_location)
except KeyboardInterrupt:
    logger.info("Terminating script.")
except psutil.NoSuchProcess:
    logger.info("Process terminated. Exiting script.")
