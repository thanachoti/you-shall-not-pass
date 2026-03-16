import subprocess
from flask import Flask, request, jsonify
import ctypes
import os

app = Flask(__name__)

# --- Configuration: Master Firewall Rule Names ---
# These rules must be created manually once before running the script.
MASTER_RULE_IN = "Graylog_Master_Block_IN"
MASTER_RULE_OUT = "Graylog_Master_Block_OUT"

def is_admin():
    """Checks if the script is running with Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_current_ips(rule_name):
    """
    Retrieves the current list of blocked IPs from a specific Firewall rule.
    Uses PowerShell to extract the 'RemoteAddress' property.
    """
    try:
        # PowerShell command to fetch existing RemoteAddress list
        cmd = f"powershell -Command \"(Get-NetFirewallRule -DisplayName '{rule_name}' | Get-NetFirewallAddressFilter).RemoteAddress\""
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        ips = result.stdout.strip()
        return ips if ips else ""
    except Exception as e:
        print(f"Error fetching existing IPs: {e}")
        return ""

def update_firewall(attacker_ip):
    """
    Updates the Master Rule by appending the new attacker IP to the existing list.
    This method utilizes Rule Consolidation for better system performance.
    """
    try:
        # 1. Fetch the current blocked IP list
        current_ips = get_current_ips(MASTER_RULE_IN)

        # 2. Check for duplication to prevent redundant updates
        if attacker_ip in current_ips.split(','):
            return f"IP {attacker_ip} is already blocked."

        # 3. Append the new IP (Comma-separated format)
        if not current_ips or current_ips == "Any" or current_ips == "":
            updated_ips = attacker_ip
        else:
            updated_ips = f"{current_ips},{attacker_ip}"

        # 4. Apply the updated list back to both INBOUND and OUTBOUND Master Rules
        # This uses 'Set-NetFirewallRule' which updates the existing object instead of creating a new one.
        for rule in [MASTER_RULE_IN, MASTER_RULE_OUT]:
            set_cmd = f"powershell -Command \"Set-NetFirewallRule -DisplayName '{rule}' -RemoteAddress '{updated_ips}'\""
            subprocess.run(set_cmd, shell=True, check=True)
        
        return f"Successfully updated Master Rule with IP: {attacker_ip}"

    except Exception as e:
        return f"Firewall Update Error: {str(e)}"

@app.route('/block', methods=['POST'])
def block_ip():
    """Webhook endpoint that receives alerts from Graylog."""
    data = request.json
    print("\n" + "="*50)
    print("📢 Incoming Graylog Alert Detected")
    
    attacker_ip = None
    # Iterate through the Graylog backlog to find the 'attacker_ip' field
    for item in data.get('backlog', []):
        ip = item.get('fields', {}).get('attacker_ip')
        if ip:
            attacker_ip = ip
            break

    if attacker_ip:
        print(f"🚨 TARGET IDENTIFIED: {attacker_ip}")
        # Execute the optimized firewall update logic
        status_msg = update_firewall(attacker_ip)
        print(f"✅ Status: {status_msg}")
        return jsonify({
            "status": "success", 
            "ip": attacker_ip, 
            "detail": status_msg
        }), 200
    else:
        print("⚠️ Warning: No valid IP address found in request data.")
        return jsonify({"status": "error", "message": "IP not found"}), 400

if __name__ == '__main__':
    # Initial privilege check before starting the Flask server
    if is_admin():
        print(f"🛡️ Privilege Level: ADMINISTRATOR")
        print(f"⚙️ Monitoring Master Rules: {MASTER_RULE_IN} / {MASTER_RULE_OUT}")
        print("🚀 Webhook Server active on port 5000...")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("🛑 ACCESS DENIED: This script must be run as an Administrator.")
        print("Please restart your terminal (CMD/PowerShell) with 'Run as Administrator'.")