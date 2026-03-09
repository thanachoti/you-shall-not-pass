from flask import Flask, request, jsonify
import os
import ctypes
import subprocess

app = Flask(__name__)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

@app.route('/block', methods=['POST'])
def block_ip():
    # --- Step 1: Receive Data ---
    print("\n" + "="*50)
    print("[STEP 1] 📥 Received Alert data from Graylog")
    data = request.json
    
    # --- Step 2: Analyze Data ---
    print("[STEP 2] 🔍 Searching for attacker_ip from backlog...")
    attacker_ip = None
    backlog = data.get('backlog', [])
    
    for index, item in enumerate(backlog):
        fields = item.get('fields', {})
        ip = fields.get('attacker_ip')
        if ip:
            attacker_ip = ip
            print(f"      🎯 Target found! IP: {attacker_ip} (at list index {index+1})")
            break

    # --- Step 3: Execute Block ---
    if attacker_ip:
        print(f"[STEP 3] 🛡️ Commanding Windows Firewall to block IP: {attacker_ip} (Inbound)")
        
        rule_name = f"Graylog_Auto_Block_{attacker_ip}"
        
        # Prepare the command
        cmd = [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule_name}",
            "dir=in",
            "action=block",
            f"remoteip={attacker_ip}"
        ]
        
        # Run the command and check the result
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"[FINISHED] ✅ Block successful! Created rule name: {rule_name}")
                return jsonify({"status": "success", "ip": attacker_ip}), 200
            else:
                print(f"[ERROR] ❌ Windows Firewall rejected the command: {result.stderr.strip()}")
                return jsonify({"status": "firewall_error"}), 500
                
        except Exception as e:
            print(f"[CRITICAL] ⚠️ Error occurred while running the command: {e}")
            return str(e), 500
    else:
        # --- Case: IP not found ---
        print("[FINISHED] ⚠️ Execution ended: No IP Address found in the received data")
        return jsonify({"status": "no_ip_found"}), 200

if __name__ == '__main__':
    if is_admin():
        print("🚀 [START] Server is ready (Running as Admin)")
        print("📍 Waiting for Webhook on port 5000...")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("🛑 [STOP] Please run the program with Administrator privileges!")