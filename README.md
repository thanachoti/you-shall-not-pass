Brute Force Attack Detection & Automated Response System
This project demonstrates a proactive security workflow to detect and mitigate Brute Force Attacks in real-time. It integrates log management, automated incident response, and attack simulation to create a complete security loop.

🛠 Core Components
Graylog (SIEM): Centralized log management used for monitoring system logs and triggering alerts via Webhooks.

Python Script (Incident Response): A Flask-based webhook receiver that automatically creates Windows Firewall rules to block attacker IPs.

Kali Linux (Hydra): Used for simulating brute force attacks to test the system's effectiveness.

Docker: Used to simplify the deployment of the Graylog infrastructure.

Getting Started
Follow these steps to set up the environment and test the system.

1. Infrastructure Setup
First, deploy the Graylog stack using Docker:

# Clone this repository
git clone https://github.com/thanachoti/you-shall-not-pass.git

# Start the Graylog stack
docker-compose up -d

2. Log Collection (Optional)
If your target machine is not sending logs to Graylog, you need to install and configure NXLog on the client-side to forward Windows Event Logs (or other logs) to Graylog.

3. Automated Blocking Script
Ensure you have Python installed on your Windows machine, then run the response script with Administrator privileges:

4. Configuration
- Graylog: Configure an Input (e.g., GELF or Syslog) to receive logs.

- Alerting: Create an Alert Condition in Graylog (e.g., detect multiple failed login attempts).

- Webhook: Set up a Notification in Graylog using the HTTP Webhook type, pointing to http://<your-ip>:5000/block.

Simulation & Testing
To verify the system, use Hydra on Kali Linux to simulate a brute force attack. We have provided a specific wordlist for this purpose:

- Locate the file: password for testing Brute Force.

- Run the attack from Kali Linux:
# Example Hydra command (adjust to your target service)
hydra -l admin -P "password for testing Brute Force" <target-ip> <protocol>