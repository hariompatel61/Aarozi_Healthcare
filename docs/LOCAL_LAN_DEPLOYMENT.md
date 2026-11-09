# Aarozi Healthcare — Local LAN & On-Premises Master PC Deployment

**Recommended Default for 95% of Indian Diagnostic Laboratories**

---

## 1. Network Topology

```
+---------------------------------------------------------------------------------+
|                       DIAGNOSTIC LABORATORY LOCAL NETWORK                       |
+---------------------------------------------------------------------------------+
                                       │
                [ Gigabit Ethernet Switch / Lab Wi-Fi Router ]
                 (Local Subnet: 192.168.1.X — No Internet Needed)
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
┌───────────────┐              ┌───────────────┐              ┌───────────────┐
│ RECEPTION DESK│              │ BIOCHEMISTRY  │              │ DOCTOR CABIN  │
│ Patient Reg & │              │ Mindray / Erba│              │ Sign-Off Desk │
│ Billing (F2)  │              │ Analyzer Feed │              │ Verification  │
│ 192.168.1.101 │              │ 192.168.1.102 │              │ 192.168.1.103 │
└───────────────┘              └───────────────┘              └───────────────┘
                                       │
                                       ▼
                     ┌───────────────────────────────────┐
                     │   LABORATORY MASTER SERVER PC     │
                     │   Static IP: 192.168.1.50         │
                     │   Port: 8000                      │
                     │   AaroziHealthcareServer.exe      │
                     │   dev_aarozi.db (SQLite Database) │
                     │   RS-232 Serial Port (Analyzers)  │
                     │   External USB Backup Drive       │
                     └───────────────────────────────────┘
```

---

## 2. Server PC Requirements

- **Processor:** Intel Core i5 (10th Gen or newer) or AMD Ryzen 5.
- **RAM:** 16 GB DDR4/DDR5.
- **Storage:** 512 GB NVMe SSD (fast random reads for SQLite & reports).
- **Operating System:** Windows 10 Pro or Windows 11 Pro 64-bit.
- **Power:** 600VA+ UPS battery backup (protects against sudden voltage drops).

---

## 3. Step-by-Step Laboratory Setup

### Step 1: Assign a Static Local IP to Master PC
1. Open Windows **Settings &rarr; Network &amp; Internet &rarr; Ethernet**.
2. Set IP assignment to **Manual**:
   - IP address: `192.168.1.50`
   - Subnet mask: `255.255.255.0`
   - Gateway: `192.168.1.1`

### Step 2: Install Aarozi Healthcare
1. Run `AaroziHealthcare-Setup-v1.0.0.exe` as Administrator.
2. The setup wizard copies all components, creates desktop shortcuts, and automatically adds the inbound Windows Firewall rule for TCP port 8000.
3. Place `aarozi_license.lic` on the desktop.

### Step 3: Launch and Activate
1. Double-click the **Aarozi Healthcare** desktop shortcut.
2. Google Chrome or Microsoft Edge opens automatically to:
   `http://localhost:8000`
3. Navigate to **Settings &rarr; System Licensing**.
4. Click **Import License**, select the `.lic` file, and verify all modules are active!

### Step 4: Connect Client Workstations
On any other computer in the lab (reception, phlebotomy, doctor cabin):
1. Open Google Chrome.
2. Navigate to: `http://192.168.1.50:8000`
3. Bookmark the URL for instant 1-click access.

