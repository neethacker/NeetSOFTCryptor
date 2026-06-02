import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from cryptor import CryptorEngine, generate_loader_code


def find_python() -> str:
    """Находит путь к python.exe в системе."""
    python_exe = shutil.which('python') or shutil.which('python3')
    if python_exe:
        return python_exe
    possible_paths = [
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
        rf"C:\Users\{os.getenv('USERNAME')}\AppData\Local\Programs\Python\Python313\python.exe",
        rf"C:\Users\{os.getenv('USERNAME')}\AppData\Local\Programs\Python\Python312\python.exe",
        rf"C:\Users\{os.getenv('USERNAME')}\AppData\Local\Programs\Python\Python311\python.exe",
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    raise RuntimeError("Python не найден. Установите Python и добавьте в PATH.")


def check_pyinstaller(python_exe: str):
    """Проверяет, установлен ли PyInstaller."""
    result = subprocess.run([python_exe, '-m', 'pip', 'show', 'pyinstaller'],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("PyInstaller не установлен. Выполните: pip install pyinstaller")


def compile_pyinstaller_external(script_path: Path, work_dir: Path, output_name: str,
                                 console: bool = False, icon: str = None) -> Path:
    """Запускает PyInstaller через внешний Python."""
    python_exe = find_python()
    check_pyinstaller(python_exe)

    dist_dir = work_dir / 'dist'
    build_dir = work_dir / 'build'
    spec_dir = work_dir

    args = [
        python_exe, '-m', 'PyInstaller',
        '--onefile',
        '--distpath', str(dist_dir),
        '--workpath', str(build_dir),
        '--specpath', str(spec_dir),
        '--name', output_name,
        '--clean',
    ]
    if not console:
        args.append('--noconsole')
    if icon and os.path.isfile(icon):
        args.extend(['--icon', icon])

    hidden_imports = ['json', 'base64', 'ctypes', 'threading', 'time', 'random', 'tempfile', 'subprocess', 'os', 'sys']
    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')

    args.append(str(script_path))

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"PyInstaller ошибка (код {result.returncode})\n{result.stderr}")

    exe_path = dist_dir / f"{output_name}.exe"
    if not exe_path.exists():
        raise RuntimeError(f"Не найден выходной файл: {exe_path}")
    return exe_path


def build_crypted(user_exe_path: str, output_name: str, icon_path: str = None, work_dir: str = None) -> str:
    """Основная функция: шифрует один EXE и упаковывает в загрузчик."""
    if work_dir is None:
        work_dir = tempfile.mkdtemp()
    work_dir = Path(work_dir)

    # Копируем пользовательский EXE
    user_file = work_dir / "input.exe"
    shutil.copy2(user_exe_path, user_file)
    user_data = user_file.read_bytes()

    # Шифруем
    crypt_config = {'encryption_algo': 'XOR'}
    cryptor = CryptorEngine(crypt_config)
    enc_data, meta = cryptor.encrypt(user_data)

    # Генерируем загрузчик (только для этого одного файла)
    loader_code = generate_loader_code(enc_data, meta, "input.exe")
    loader_py = work_dir / 'loader.py'
    loader_py.write_text(loader_code, encoding='utf-8')

    # Компилируем в EXE
    final_exe = compile_pyinstaller_external(loader_py, work_dir, output_name,
                                             console=False, icon=icon_path)

    # Копируем результат в папку с программой
    if getattr(sys, 'frozen', False):
        dest_dir = Path(sys.executable).parent
    else:
        dest_dir = Path(__file__).parent
    dest_path = dest_dir / f"{output_name}.exe"
    shutil.copy2(final_exe, dest_path)
    return str(dest_path)
