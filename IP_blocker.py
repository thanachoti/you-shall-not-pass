from flask import Flask, request, jsonify
import os
import ctypes

app = Flask(__name__)

# ตรวจสอบว่าเป็น Admin หรือไม่ (เพราะการสั่ง Block Firewall ต้องใช้สิทธิ์ Admin)
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

@app.route('/block', methods=['POST'])
def block_ip():
    data = request.json
    print("\n" + "="*50)
    print("📢 Graylog Alert Received!")
    
    # 1. พยายามดึง IP จากข้อมูลที่ Graylog ส่งมา
    attacker_ip = None
    
    # วนลูปตรวจทุก log ใน backlog จนกว่าจะเจอ IP
    for item in data.get('backlog', []):
        ip = item.get('fields', {}).get('attacker_ip')
        if ip:
            attacker_ip = ip
            break  # เจอ IP แล้วให้หยุดค้นหาทันที

    # 2. ถ้าเจอ IP ให้ทำการ Block ทั้ง Inbound และ Outbound
    if attacker_ip:
        print(f"🚨 TARGET DETECTED: {attacker_ip}")
        
        try:
            # 2A. สั่ง Windows Firewall บล็อก IP นี้ (ขาเข้า - INBOUND)
            rule_name_in = f"Graylog_Block_IN_{attacker_ip}"
            cmd_in = f"netsh advfirewall firewall add rule name=\"{rule_name_in}\" dir=in action=block remoteip={attacker_ip}"
            os.system(cmd_in)
            
            # 2B. สั่ง Windows Firewall บล็อก IP นี้ (ขาออก - OUTBOUND) ป้องกัน Reverse Shell
            rule_name_out = f"Graylog_Block_OUT_{attacker_ip}"
            cmd_out = f"netsh advfirewall firewall add rule name=\"{rule_name_out}\" dir=out action=block remoteip={attacker_ip}"
            os.system(cmd_out)
            
            print(f"✅ SUCCESS: {attacker_ip} has been completely isolated (Inbound & Outbound).")
            print(f"🛠️ Rules Created: {rule_name_out}")
            return jsonify({"status": "isolated", "ip": attacker_ip}), 200
            
        except Exception as e:
            print(f"❌ ERROR while blocking: {e}")
            return str(e), 500
    else:
        # กรณีหา IP ไม่เจอ
        print("⚠️ No IP address found in the alert data.")
        print("Raw Data for Debugging:", data)
        return "IP not found", 200 

if __name__ == '__main__':
    if is_admin():
        print("🛡️ Python Blocker is running with Admin privileges.")
        print("🚀 Listening for Graylog alerts on port 5000...")
        app.run(host='0.0.0.0', port=5000)
    else:
        print("🛑 ERROR: Please run this script as ADMINISTRATOR!")
        print("Right-click on PowerShell/CMD and select 'Run as Administrator'")