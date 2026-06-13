import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.encryptor_core import encrypt_file, decrypt_file

import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
QRadioButton, QButtonGroup, QLabel, QLineEdit, QCheckBox, QProgressBar, QHBoxLayout, QMessageBox)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg

from src.encryptor_core import encrypt_file, decrypt_file
# audio_viz not working 
'''
try:
    from src.audio_viz import audio_to_amplitude_array
except ImportError:
    print("Warning: src.audio_viz not found. Audio visualization disabled.")
    def audio_to_amplitude_array(path): return None

'''

# --- HELPER FUNCTIONS FOR CLEAN INPUT ---
def get_clean_password_input(input_text: str) -> str or None:
    """Returns password string, or None if the input is empty or just whitespace."""
    cleaned = input_text.strip()
    return cleaned if cleaned else None

def get_clean_private_key_pass(input_text: str) -> bytes or None:
    """Returns private key password bytes, or None if the input is empty or just whitespace."""
    cleaned = input_text.strip()
    return cleaned.encode('utf-8') if cleaned else None



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binary Encryptor — Project Chaturvedi")
        self.resize(1000, 650)
        layout = QVBoxLayout()
        # file selection
        row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        row.addWidget(self.file_label)
        btn_open = QPushButton("Choose File")
        btn_open.clicked.connect(self.open_file)
        row.addWidget(btn_open)
        layout.addLayout(row)
        # encryption level
        self.r_general = QRadioButton("General (password)")
        self.r_aes = QRadioButton("AES (ephemeral)")
        self.r_rsa = QRadioButton("RSA + AES")
        self.r_aes.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.r_general); group.addButton(self.r_aes); group.addButton(self.r_rsa)
        layout.addWidget(self.r_general); layout.addWidget(self.r_aes); layout.addWidget(self.r_rsa)
        # password & key
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (for General and RSA Private Key)")
        layout.addWidget(self.password_input)
        self.pubkey_path_input = QLineEdit()
        self.pubkey_path_input.setPlaceholderText("Public key PEM (for RSA ENCRYPT) - browse or paste")
        layout.addWidget(self.pubkey_path_input)
        btn_pub = QPushButton("Browse Public Key")
        btn_pub.clicked.connect(self.browse_pubkey)
        layout.addWidget(btn_pub)
        # compression and buttons
        self.compress_check = QCheckBox("Compress (zlib)")
        layout.addWidget(self.compress_check)
        row2 = QHBoxLayout()
        self.encrypt_btn = QPushButton("Encrypt -> produce .bxcrypt")
        self.encrypt_btn.clicked.connect(self.on_encrypt)
        row2.addWidget(self.encrypt_btn)
        self.decrypt_btn = QPushButton("Decrypt")
        self.decrypt_btn.clicked.connect(self.on_decrypt)
        row2.addWidget(self.decrypt_btn)
        layout.addLayout(row2)
        # progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        # waveform area -------removed--------
        '''
        self.graph = pg.PlotWidget(title="Audio waveform (RMS windows)")
        self.graph.setBackground('w')
        layout.addWidget(self.graph, stretch=1)
        '''
        
        self.setLayout(layout)
        self.selected_file = None

        ''' 
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        '''
        

    def show_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.exec_()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select file")
        if path:
            self.file_label.setText(path)
            self.selected_file = path
            # if audio, load waveform -----removed-----
            '''
            try:
                # Check if audio_to_amplitude_array is defined (not the placeholder)
                if 'audio_to_amplitude_array' in globals() and path.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                    self.waveform = audio_to_amplitude_array(path)
                    self.ptr = 0
                    self.graph.clear()
                    self.cur_plot = self.graph.plot(self.waveform, pen=pg.mkPen(width=1))
                    # start animation
                    self.timer.start(100)
                else:
                    self.waveform = None
                    self.graph.clear()
                    self.timer.stop()
            except Exception as e:
                self.show_message("Audio Error", f"Could not load audio visualization: {e}")
                print("Audio load error:", e)
            '''
    def browse_pubkey(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Public Key PEM", filter="PEM Files (*.pem);;All Files (*)")
        if p:
            self.pubkey_path_input.setText(p)

    def on_encrypt(self):
        if not self.selected_file:
            self.show_message("Error", "Please select a file to encrypt.")
            return

        level = 'general' if self.r_general.isChecked() else 'aes' if self.r_aes.isChecked() else 'rsa'
        
        # --- assigning pwd if General OR AES is checked ---
        pwd = None
        if level == 'general' or level == 'aes':
            pwd = get_clean_password_input(self.password_input.text()) #clean password input
        
        # Check for required fields based on level
        if (level == 'general' or level == 'aes') and not pwd:
            self.show_message("Error", "Password is required for the selected encryption level.")
            return

        pub = None
        if level == 'rsa':
            ppath = self.pubkey_path_input.text()
            if not ppath or not os.path.exists(ppath):
                self.show_message("Error", "Public key file required for 'RSA' encryption level.")
                return
            try:
                with open(ppath, 'rb') as f:
                    pub = [f.read()]
            except Exception as e:
                 self.show_message("Error", f"Failed to read public key: {e}")
                 return
        
        # Use Save File Dialog for ENCRYPT output to allow user to name the file
        default_out_name = os.path.basename(self.selected_file) + '.bxcrypt'
        out, _ = QFileDialog.getSaveFileName(self, 'Save Encrypted File', default_out_name, "Encrypted Files (*.bxcrypt);;All Files (*)")
        
        if not out:
            return 

        self.progress.setValue(0)
        try:
            encrypt_file(self.selected_file, out, level=level, password=pwd, rsa_public_pems=pub, compress=self.compress_check.isChecked())
            self.progress.setValue(100)
            self.show_message("Success", f"File successfully encrypted: {out}")
            print("Encrypted ->", out)
        except Exception as e:
            self.progress.setValue(0)
            self.show_message("Encryption Error", f"An error occurred during encryption: {e}")
            print("Encryption error:", e)

    def on_decrypt(self):
        if not self.selected_file:
            self.show_message("Error", "Please select an encrypted file to decrypt.")
            return
        
        if not self.selected_file.lower().endswith('.bxcrypt'):
             self.show_message("Warning", "The selected file does not look like an encrypted container (.bxcrypt).")

        level = 'general' if self.r_general.isChecked() else 'aes' if self.r_aes.isChecked() else 'rsa'
        # --- MUTUALLY EXCLUSIVE PASSWORD LOGIC ---
        input_text = self.password_input.text()
        symmetric_password = None 
        rsa_private_key_password = None 

        if level == 'general' or level == 'aes':
            # Password for Symmetric Key (General/AES)
            symmetric_password = get_clean_password_input(input_text)
            if not symmetric_password:
                self.show_message("Error", "Password is required for decryption.")
                return
        
        elif level == 'rsa':
            # Password for Private Key file (ONLY if the private key file itself is encrypted) -- optional
            rsa_private_key_password = get_clean_private_key_pass(input_text)
        
        privpem = None
        if level == 'rsa':
            privpath, _ = QFileDialog.getOpenFileName(self, "Select Private Key PEM", filter="PEM Files (*.pem);;All Files (*)")
            if not privpath:
                self.show_message("Error", "Private key file required for 'RSA' decryption.")
                return
            try:
                with open(privpath, 'rb') as f:
                    privpem = f.read()
            except Exception as e:
                self.show_message("Error", f"Failed to read private key file: {e}")
                return

        # --- Determine output name and use Save Dialog ---
        default_name = self.selected_file
        if default_name.lower().endswith('.bxcrypt'):
            default_name = default_name[:-len('.bxcrypt')]
        
        out, _ = QFileDialog.getSaveFileName(self, 'Save Decrypted File As', default_name, "All Files (*)")

        if not out:
            return # User cancelled
        
        self.progress.setValue(0)
        try:
            decrypt_file(self.selected_file, out, 
                         password=symmetric_password, 
                         rsa_priv_pem=privpem, 
                         rsa_priv_pass=rsa_private_key_password)
            self.progress.setValue(100)
            self.show_message("Success", f"File successfully decrypted: {out}")
            # --- FINAL STEP: Clear password input after decryption to prevent errors ---
            self.password_input.clear()
            print("Decrypted ->", out)
        except Exception as e:
            self.progress.setValue(0)
            self.show_message("Decryption Error", f"An error occurred during decryption: {e}")
            print("Decrypt error:", e)

    def animate(self):
        # simple scrolling animation for the waveform
        '''
        if self.waveform is None:
            return
        L = len(self.waveform)
        window = 512
        if self.ptr + window > L:
            self.ptr = 0
        view = self.waveform[self.ptr:self.ptr + window]
        self.graph.clear()
        self.graph.plot(view, pen=pg.mkPen(width=2))
        self.ptr += 64
        '''
        pass 
        

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
