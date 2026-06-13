# 🛡️ File Encryptor: Multi-Level Security Tool

A **Python-based desktop application** for **secure file encryption and decryption**, built as a **Data Structures mini-project**.  
It demonstrates the integration of **core data structures** with **modern cryptography** to build a practical, high-security tool.

---

## 🚀 Key Features and Academic Focus

| Feature | Data Structure | Purpose |
| :--- | :--- | :--- |
| **Integrity Check** | **Merkle Tree** | Verifies data integrity after encryption. |
| **File Structure** | **Hash Map / Dictionary** | Stores metadata like salt, size, and encryption level. |
| **Block Handling** | **List / Array** | Handles file chunking and quick access. |
| **Audio Visualizer (WIP)** | **Numpy Array** | Planned for analyzing encrypted audio distortion. |

---

## 🔐 Encryption Levels

| Level | Name | Description | Security |
| :--- | :--- | :--- | :--- |
| **Level 1** | **General (Easy)** | Basic password-based encryption using XOR/Byte Shift logic. | PBKDF2 + XOR |
| **Level 2** | **AES (Medium)** | Strong AES-256 GCM encryption for real-world use. | AES-256 GCM |
| **Level 3** | **RSA + AES (Hard)** | Hybrid encryption — RSA secures AES key. | RSA OAEP + AES GCM |

---

## ⚙️ Installation and Setup

### **Step 1: Install Dependencies**

Open your terminal or PowerShell in the project root (`FileEncryptor/`) and run:

```bash
pip install -r requirements.txt
```

*(If you don’t have the file, manually install via `pip install PyQt5 cryptography numpy pydub`.)*

---

## 🪶 Step-by-Step Usage Guide

### 🔹 **Level 1: General (Easy)**
1. Run:
   ```bash
   py -m src.gui
   ```
2. Select **General (Easy)** → Enter a password → Choose file → **Encrypt**.  
3. For decryption, use the same password.

---

### 🔸 **Level 2: AES (Medium)**
1. Launch GUI and select **AES (Medium)**.  
2. Enter a strong password → Select file → **Encrypt**.  
3. Use the same password to decrypt.

---

### 🔺 **Level 3: RSA + AES (Hard)**

#### **Generate RSA Keys**
```bash
python -c "from src.keyutils import generate_keys; generate_keys()"
```
Generates:
- `keys/public_key.pem` → Share this  
- `keys/private_key.pem` → Keep this private  

#### **Encrypt**
1. Select **RSA + AES (Hard)**.  
2. Load recipient’s `public_key.pem`.  
3. **Leave Password field empty.**  
4. Select file → **Encrypt**.

#### **Decrypt**
1. Select **RSA + AES (Hard)** again.  
2. Keep password field **empty**.  
3. Choose encrypted file → Load your `private_key.pem` → **Decrypt**.

---

## 🧰 Tech Stack

- **Language:** Python  
- **Framework:** PyQt5  
- **Libraries:** `cryptography`, `numpy`, `pydub`, `hashlib`, `os`, `sys`  
- **OS:** Windows / Linux / macOS  

---

## 📁 Project Structure

```
FileEncryptor/
│
├── src/
│   ├── gui.py              # Main GUI launcher
│   ├── encryptor.py        # Core encryption/decryption logic
│   ├── keyutils.py         # RSA key generation utilities
│   ├── integrity.py        # Merkle tree and integrity verification
│   └── utils.py            # Helper and file management functions
│
├── keys/                   # Generated RSA key files
├── README.md
└── requirements.txt
```

---

## ✨ Authors

- **Sandeep:** Core encryption & file handling (List/Array)  
- **Chaturvedi:** Hybrid cryptography & key management (Dictionary)  
- **Neelesh:** GUI & integrity verification (Merkle Tree)  
- **Ganesh:** AES encryption & audio visualization (Array/Numpy)  

---

> _"Security isn’t just about locking files — it’s about designing trust into every bit."_  
> — **File Encryptor Development Team**
