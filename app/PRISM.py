#############################################################
# PRISM (Proactive Remote Inspection and Server Management) #
# Version: 1.0                                              #
# Author: BinaryBifrost                                     #
# Website: https://frostbyte.ai                             #
#############################################################

import os
import time
import subprocess
import requests
import logging
import json
from dotenv import load_dotenv

load_dotenv()

HOST_IPs            = os.getenv('HOST_IPs').replace(" ", "").split(',')
IDRAC_IPs           = os.getenv('IDRAC_IPs').replace(" ", "").split(',')
IDRAC_USERs         = os.getenv('IDRAC_USERs').replace(" ", "").split(',')
IDRAC_PASSWORDs     = os.getenv('IDRAC_PASSWORDs').replace(" ", "").split(',')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Check if only one username and password are given.
if len(IDRAC_USERs) == 1 and len(IDRAC_PASSWORDs) == 1:
    IDRAC_USERs     = IDRAC_USERs * len(IDRAC_IPs)
    IDRAC_PASSWORDs = IDRAC_PASSWORDs * len(IDRAC_IPs)

# Function to sanitize IPs (remove first 3 octets)
def sanitize_ip(ip):
    return '.' + ip.split('.')[-1]

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler('PRISM.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

logger = setup_logging()

def is_host_reachable(ip):
    try:
        output = subprocess.check_output("ping -c 1 " + ip, shell=True)
        if '1 packets transmitted, 1 received' in output.decode('utf-8'):
            return True
        else:
            return False
    except Exception:
        return False

def is_ipmi_reachable(idrac_ip, idrac_user, idrac_password):
    cmd = f"ipmitool -I lanplus -H {idrac_ip} -U {idrac_user} -P {idrac_password} lan print"
    try:
        output = subprocess.check_output(cmd, shell=True)
        if 'IP Address' in output.decode('utf-8'):
            return True
        else:
            return False
    except Exception as e:
        print(f"IPMI connection failed. Error: {str(e)}")
        return False

def power_cycle_idrac(idrac_ip, idrac_user, idrac_password):
    cmd = f"ipmitool -I lanplus -H {idrac_ip} -U {idrac_user} -P {idrac_password} power cycle"
    try:
        subprocess.check_output(cmd, shell=True)
        logger.info(f"Power cycle command sent to iDRAC with IP ending in: {sanitize_ip(idrac_ip)}")
        send_discord_message(f"Power Cycle", f"Command successfully sent to iDRAC with IP ending in: {sanitize_ip(idrac_ip)}", "success")
    except Exception as e:
        logger.error(f"Failed to send power cycle command to iDRAC at {sanitize_ip(idrac_ip)}. Error: {str(e)}")
        send_discord_message(f"Power Cycle", f"Failed to send command to iDRAC with IP ending in: {sanitize_ip(idrac_ip)}. Error: {str(e)}", "error")

def send_discord_message(title, description, status):
    color = 65280 if status == "success" else 16711680
    emoji = ":white_check_mark:" if status == "success" else ":x:"
    data = {
        "embeds": [
            {
                "title": emoji + " " + title + " " + emoji,
                "description": description,
                "color": color,
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)
        logger.info(f"Sent message to Discord: {description}")
    except Exception as e:
        logger.error(f"Failed to send message to Discord. Error: {str(e)}")

if __name__ == "__main__":
    logger.info("Initial status check...")

    status_messages = []
    overall_status = "success"

    for HOST_IP, IDRAC_IP, IDRAC_USER, IDRAC_PASSWORD in zip(HOST_IPs, IDRAC_IPs, IDRAC_USERs, IDRAC_PASSWORDs):
        host_status  = "PASS" if is_host_reachable(HOST_IP) else "FAIL"
        idrac_status = "PASS" if is_host_reachable(IDRAC_IP) else "FAIL"
        ipmi_status  = "PASS" if is_ipmi_reachable(IDRAC_IP, IDRAC_USER, IDRAC_PASSWORD) else "FAIL"

        status_messages.append(
            f"\n**Host with IP ending in:** {sanitize_ip(HOST_IP)} - {host_status}\n"
            f"**iDRAC with IP ending in:** {sanitize_ip(IDRAC_IP)} - {idrac_status}\n"
            f"**IPMI:** {ipmi_status}"
        )

        if host_status == "FAIL" or idrac_status == "FAIL" or ipmi_status == "FAIL":
            overall_status = "error"

    status_report = "\n\n".join(status_messages)
    status_report += "\n\nPRISM by BinaryBifrost loaded successfully!"

    send_discord_message("Initial status check completed", status_report, overall_status)

    logger.info("Starting to monitor the hosts...")

    while True:
        time.sleep(60)
        for HOST_IP, IDRAC_IP, IDRAC_USER, IDRAC_PASSWORD in zip(HOST_IPs, IDRAC_IPs, IDRAC_USERs, IDRAC_PASSWORDs):
            for _ in range(3):
                if is_host_reachable(HOST_IP):
                    break
                time.sleep(30)
            else:
                logger.warning(f"Host with IP ending in {sanitize_ip(HOST_IP)} is down. Sending power cycle command to iDRAC...")
                send_discord_message("Host is Down", f"Host with IP ending in {sanitize_ip(HOST_IP)} is down. Sending power cycle command to iDRAC...", "warning")
                power_cycle_idrac(IDRAC_IP, IDRAC_USER, IDRAC_PASSWORD)

                while True:  # wait until the host is back online
                    time.sleep(120)
                    if is_host_reachable(HOST_IP):
                        logger.info(f"Host with IP ending in {sanitize_ip(HOST_IP)} is back online after power cycle.")
                        send_discord_message("Host Status", f"Host with IP ending in {sanitize_ip(HOST_IP)} is back online after power cycle.", "success")
                        break
                    #else: # For more verbose updates / logging
                    #    logger.error(f"Host with IP ending in {sanitize_ip(HOST_IP)} is still down after power cycle.")
                    #    send_discord_message("Host Status", f"Host with IP ending in {sanitize_ip(HOST_IP)} is still down after power cycle.", "error")
