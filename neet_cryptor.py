import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
import traceback

# Перенаправление ошибок в файл (для отладки)
if getattr(sys, 'frozen', False):
    log_path = Path(sys.executable).parent / "error.log"
else:
    log_path = Path(__file__).parent / "error.log"
sys.stderr = open(log_path, "w", encoding="utf-8")
sys.stdout = open(log_path, "a", encoding="utf-8")


# ----- ЗАЩИТА: анти-отладка и анти-VM -----
def anti_debug():
    try:
        import ctypes
        if ctypes.windll.kernel32.IsDebuggerPresent():
            sys.exit(0)
    except:
        pass


def anti_vm():
    try:
        import psutil
        vm_procs = ['vbox', 'vmware', 'qemu', 'sandbox', 'virtualbox']
        for proc in psutil.process_iter(['name']):
            name = proc.info['name'].lower()
            if any(vm in name for vm in vm_procs):
                sys.exit(0)
    except:
        pass


anti_debug()
anti_vm()
# ------------------------------------------

from build_engine_cryptor import build_crypted

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class NeetCryptorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Neet Cryptor")
        self.geometry("600x600")
        self.resizable(False, False)

        self.input_path = ctk.StringVar()
        self.output_name = ctk.StringVar(value="protected")
        self.icon_path = ctk.StringVar()

        self._create_widgets()
        self._check_requirements()

    def _check_requirements(self):
        """Проверяет наличие Python и PyInstaller, выводит предупреждение."""
        try:
            python_exe = shutil.which('python') or shutil.which('python3')
            if not python_exe:
                raise Exception("Python не найден")
            result = subprocess.run([python_exe, '-m', 'pip', 'show', 'pyinstaller'],
                                    capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("PyInstaller не установлен")
        except Exception as e:
            self.log("[!] ВНИМАНИЕ: Для работы Neet Cryptor требуется Python и PyInstaller.")
            self.log("[!] Установите Python с https://python.org, затем выполните:")
            self.log("    pip install pyinstaller psutil customtkinter")
            self.log("[!] После этого перезапустите программу.")

    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self, corner_radius=10)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(main_frame, text="Neet Cryptor", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(main_frame, text="Защита исполняемых файлов", font=ctk.CTkFont(size=12)).pack(pady=(0, 20))

        ctk.CTkLabel(main_frame, text="Исходный EXE файл:").pack(anchor="w", padx=10)
        input_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkEntry(input_frame, textvariable=self.input_path, placeholder_text="Выберите EXE файл...").pack(
            side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkButton(input_frame, text="Обзор", width=80, command=self._browse_input).pack(side="right")

        ctk.CTkLabel(main_frame, text="Имя выходного файла (без .exe):").pack(anchor="w", padx=10, pady=(15, 0))
        ctk.CTkEntry(main_frame, textvariable=self.output_name, placeholder_text="protected").pack(fill="x", padx=10,
                                                                                                   pady=5)

        ctk.CTkLabel(main_frame, text="Иконка (.ico, необязательно):").pack(anchor="w", padx=10, pady=(15, 0))
        icon_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        icon_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkEntry(icon_frame, textvariable=self.icon_path, placeholder_text=r"C:\путь\к\icon.ico").pack(side="left",
                                                                                                           expand=True,
                                                                                                           fill="x",
                                                                                                           padx=(0, 10))
        ctk.CTkButton(icon_frame, text="Обзор", width=80, command=self._browse_icon).pack(side="right")

        self.process_btn = ctk.CTkButton(main_frame, text="ЗАЩИТИТЬ ФАЙЛ", command=self._process, height=40,
                                         font=ctk.CTkFont(size=14, weight="bold"))
        self.process_btn.pack(pady=20, padx=10, fill="x")

        ctk.CTkLabel(main_frame, text="Лог:", anchor="w").pack(fill="x", padx=10)
        self.log_text = ctk.CTkTextbox(main_frame, height=180, wrap="word")
        self.log_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

    def _browse_input(self):
        path = filedialog.askopenfilename(title="Выберите EXE файл", filetypes=[("Executable", "*.exe")])
        if path:
            self.input_path.set(path)

    def _browse_icon(self):
        path = filedialog.askopenfilename(title="Выберите иконку", filetypes=[("Icon", "*.ico")])
        if path:
            self.icon_path.set(path)

    def log(self, msg):
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.update()

    def _process(self):
        input_file = self.input_path.get().strip()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Ошибка", "Выберите корректный EXE файл.")
            return

        output_name = self.output_name.get().strip()
        if not output_name:
            output_name = "protected"
        icon = self.icon_path.get().strip()
        if icon and not os.path.exists(icon):
            icon = None

        self.process_btn.configure(state="disabled", text="ОБРАБОТКА...")
        self.log("Начало обработки...")
        self.log(f"Исходный файл: {input_file}")
        self.log(f"Выходной файл: {output_name}.exe")

        work_dir = tempfile.mkdtemp()
        try:
            result_path = build_crypted(input_file, output_name, icon, work_dir)
            self.log(f"Готово! Файл сохранён: {result_path}")
            messagebox.showinfo("Успех", f"Файл успешно обработан:\n{result_path}")
        except Exception as e:
            error_text = f"Ошибка: {str(e)}\n{traceback.format_exc()}"
            self.log(error_text)
            with open(Path(sys.executable).parent / "error.log", "a", encoding="utf-8") as f:
                f.write(error_text + "\n")
            messagebox.showerror("Ошибка", str(e))
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
            self.process_btn.configure(state="normal", text="ЗАЩИТИТЬ ФАЙЛ")


if __name__ == "__main__":
    app = NeetCryptorApp()
    app.mainloop()
