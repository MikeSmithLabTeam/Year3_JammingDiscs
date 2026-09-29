import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path

# Set active environment name: "Phys4038" or "Project"
TARGET_ENV_NAME = "Project"


def get_env_path(env_name: str) -> tuple[pathlib.Path, pathlib.Path]:
    """Returns the base venv path and cache directory path for the given environment name."""
    if platform.system() == "Windows":
        base = pathlib.Path(os.environ.get("LOCALAPPDATA", "C:/Temp")) / "uv_envs"
        local_cache = pathlib.Path(os.environ.get("LOCALAPPDATA", "C:/Temp")) / "uv" / "cache"
    else:
        base = pathlib.Path.home() / ".cache" / "uv_envs"
        local_cache = pathlib.Path.home() / ".cache" / "uv" / "cache"

    return base / env_name, local_cache


def get_jupyter_kernel_dir(kernel_name: str) -> pathlib.Path:
    """Returns the path where Jupyter stores global kernel specs for the user."""
    if platform.system() == "Windows":
        return pathlib.Path(os.environ.get("APPDATA", "")) / "jupyter" / "kernels" / kernel_name.lower()
    elif platform.system() == "Darwin":
        return pathlib.Path.home() / "Library" / "Jupyter" / "kernels" / kernel_name.lower()
    else:
        return pathlib.Path.home() / ".local" / "share" / "jupyter" / "kernels" / kernel_name.lower()


def unregister_jupyter_kernel(kernel_name: str) -> None:
    """Completely removes the Jupyter kernel spec from the user's system."""
    kernel_dir = get_jupyter_kernel_dir(kernel_name)
    
    subprocess.run(
        [sys.executable, "-m", "jupyter", "kernelspec", "remove", kernel_name.lower(), "-f"],
        capture_output=True,
        text=True,
    )

    if kernel_dir.exists():
        try:
            shutil.rmtree(kernel_dir)
            print(f"    Removed Jupyter kernel directory: {kernel_dir}")
        except OSError as e:
            print(f"⚠️ Warning: Could not delete kernel spec directory: {e}")
    else:
        print(f"    Unregistered Jupyter kernel spec '{kernel_name.lower()}'.")


def perform_reset(env_name: str) -> None:
    """Executes environment, cache, configuration, and kernel teardown."""
    print(f"\n==========================================================")
    print(f" 🧹 Executing Environment Reset for: '{env_name}'")
    print(f"==========================================================\n")

    # 1. Clear local VS Code configuration directory
    vscode_dir = pathlib.Path.cwd() / ".vscode"
    if vscode_dir.exists():
        print(f" [1/3] Removing VS Code workspace config: {vscode_dir}")
        try:
            shutil.rmtree(vscode_dir)
        except OSError as e:
            print(f"⚠️ Warning: Failed to remove .vscode directory: {e}")
    else:
        print(" [1/3] No .vscode directory found to remove.")

    # 2. Unregister global Jupyter kernel specification
    print(f" [2/3] Unregistering Jupyter kernel spec for '{env_name}'...")
    unregister_jupyter_kernel(env_name)

    # 3. Purge target environment folder and local uv cache
    safe_path, local_cache = get_env_path(env_name)

    if safe_path.exists():
        print(f" [3/3] Purging virtual environment folder: {safe_path}")
        for attempt in range(3):
            try:
                shutil.rmtree(safe_path)
                break
            except OSError:
                time.sleep(0.5)

        if safe_path.exists() and platform.system() == "Windows":
            try:
                subprocess.run(
                    ["cmd", "/c", "rmdir", "/s", "/q", str(safe_path)],
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                print("⚠️ Error: Could not completely remove environment folder. Files may be locked by VS Code or a running Python process.")
                sys.exit(1)
    else:
        print(f" [3/3] Virtual environment folder does not exist at {safe_path}.")

    if local_cache.exists():
        print(f"       Clearing local uv cache: {local_cache}")
        try:
            shutil.rmtree(local_cache)
        except OSError:
            pass

    print("\n Reset complete. Rebuilding environment...\n")


def verify_environment(new_python_path: str | pathlib.Path) -> None:
    """Verifies that key packages import successfully using the specified Python executable."""
    packages = ["numpy", "pandas", "matplotlib", "scipy", "ipykernel"]
    python_exe = pathlib.Path(new_python_path)

    code = f"""packages = {packages!r}
for pkg in packages:
    __import__(pkg)
"""

    result = subprocess.run(
        [str(python_exe), "-c", code],
        capture_output=True,
        text=True,
    )

    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RESET = "\033[0m"

    if result.returncode != 0:
        warning_msg = (
            f"Failed to import required packages using {python_exe}.\n"
            f"Error output:\n{result.stderr.strip()}"
        )
        print(f"{YELLOW}⚠️ Warning: {warning_msg}{RESET}")
        warnings.warn(warning_msg, UserWarning, stacklevel=2)
        return

    print(
        f"{GREEN} Success! All packages ({', '.join(packages)}) imported correctly.{RESET}"
    )


def register_jupyter_kernel(python_exe: pathlib.Path, kernel_name: str) -> None:
    """Registers the environment as a Jupyter kernel using the environment's ipykernel."""
    print(" Registering Jupyter kernel...")

    check_ipykernel = subprocess.run(
        [str(python_exe), "-c", "import ipykernel"],
        capture_output=True,
    )

    if check_ipykernel.returncode != 0:
        print("⚠️ Warning: ipykernel is not installed in the target environment.")
        print("   Ensure 'ipykernel' is listed under dependencies in pyproject.toml.")
        return

    result = subprocess.run(
        [
            str(python_exe),
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            kernel_name.lower(),
            "--display-name",
            f"Python ({kernel_name})",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("⚠️ Warning: Failed to register Jupyter kernel.")
        print(f"Error output:\n{result.stderr.strip()}")


def upsert_setting(json_str: str, key: str, value: object) -> str:
    """Safely updates or injects a key into a JSON string, keeping formatting balanced."""
    val_str = json.dumps(value)

    pattern = re.compile(
        r'("' + re.escape(key) + r'"\s*:\s*)(\[[^\]]*\]|"(?:\\.|[^"\\])*"|true|false|null|-?\d+(?:\.\d+)?)',
        re.IGNORECASE,
    )

    if pattern.search(json_str):
        val_str_escaped = val_str.replace("\\", "\\\\")
        return pattern.sub(r"\g<1>" + val_str_escaped, json_str, count=1)

    json_str_trimmed = json_str.rstrip()
    if json_str_trimmed.endswith("}"):
        before = json_str_trimmed[:-1].rstrip()
        if not before.endswith(",") and not before.endswith("{"):
            before += ","
        return before + f'\n  "{key}": {val_str}\n}}\n'

    try:
        data = json.loads(json_str)
        data[key] = value
        return json.dumps(data, indent=2)
    except json.JSONDecodeError:
        return json_str


def configure_vscode_settings(new_python_path: pathlib.Path) -> None:
    """Safely updates .vscode/settings.json without removing existing comments or settings."""
    vscode_dir = pathlib.Path.cwd() / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    settings_path = vscode_dir / "settings.json"

    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            settings_content = f.read()
    else:
        settings_content = "{\n}"

    envs_parent_dir = new_python_path.parent.parent.parent.as_posix()
    settings_content = upsert_setting(
        settings_content, "python.venvFolders", [envs_parent_dir]
    )
    settings_content = upsert_setting(
        settings_content, "python.defaultInterpreterPath", new_python_path.as_posix()
    )
    settings_content = upsert_setting(
        settings_content, "python.terminal.activateEnvironment", True
    )

    if platform.system() == "Windows":
        settings_content = upsert_setting(
            settings_content, "terminal.integrated.defaultProfile.windows", "Command Prompt"
        )
    else:
        settings_content = upsert_setting(
            settings_content, "terminal.integrated.defaultProfile.linux", "bash"
        )

    # Note: jupyter.preferredJupyterKernel removed to prevent VS Code kernel selection bugs

    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(settings_content)


def launch_vscode() -> None:
    """Launches VS Code in the current working directory."""
    print("\nOpening workspace in VS Code...")
    if platform.system() == "Windows":
        subprocess.run(["cmd", "/c", "code", "."], check=False)
    else:
        subprocess.run(["code", "."], check=False)


def run():
    env_name = TARGET_ENV_NAME

    if len(sys.argv) > 1 and sys.argv[1].lower().strip("-") == "reset":
        perform_reset(env_name)

    safe_path, local_cache = get_env_path(env_name)
    global_env_exists = safe_path.exists() and (safe_path / "pyvenv.cfg").exists()

    if global_env_exists:
        print(f"Using existing global venv at: {safe_path}")
    else:
        print(f"Creating fresh venv at: {safe_path}")
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["uv", "venv", "--allow-existing", str(safe_path)], check=True)

    env = os.environ.copy()
    env["UV_PROJECT_ENVIRONMENT"] = str(safe_path)
    env["UV_LINK_MODE"] = "copy"

    local_cache.mkdir(parents=True, exist_ok=True)
    env["UV_CACHE_DIR"] = str(local_cache)

    print(f"Syncing dependencies for environment '{env_name}'...")
    subprocess.run(
        [
            "uv",
            "sync",
            "--project",
            str(pathlib.Path.cwd()),
        ],
        env=env,
        check=True,
    )

    if platform.system() == "Windows":
        new_python_path = safe_path.joinpath(Path("Scripts")).joinpath(Path("python.exe"))
        new_activate_path = safe_path.joinpath(Path("Scripts")).joinpath(Path("activate"))
    else:
        new_python_path = safe_path.joinpath(Path("bin")).joinpath(Path("python"))
        new_activate_path = safe_path.joinpath(Path("bin")).joinpath(Path("activate"))

    print("=======================================================================")
    print("\n Performing environment checks...\n")
    verify_environment(new_python_path)

    print("\n Regenerating Jupyter kernel & VS Code configuration...\n")
    register_jupyter_kernel(new_python_path, env_name)
    configure_vscode_settings(new_python_path)

    CYAN = "\033[36m"
    GREEN = "\033[32m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    print("\n\n==========================================================\n")
    print(f"{BOLD}{GREEN}Setup Complete!{RESET}\n")
    print(f"{BOLD}Target Environment:{RESET} {new_python_path.as_posix()}")
    print(f" - In notebooks: click {CYAN}'Select Kernel'{RESET} -> {CYAN}'Jupyter Kernel...'{RESET}")
    print(f" - Choose {CYAN}'Python ({env_name})'{RESET} from the top of the list.")
    print(f"{BOLD}Direct Terminal Activation:{RESET} Copy and paste: {CYAN}{new_activate_path.as_posix()}{RESET}")
    print(f"{BOLD}Running Python Script:{RESET} Press {CYAN}Ctrl + Shift + P{RESET} ({CYAN}Cmd + Shift + P{RESET} on Mac)")
    print(f"    -> Select {CYAN}'Python: Select Interpreter'{RESET}")
    print(f"    -> Choose {CYAN}'{TARGET_ENV_NAME}'{RESET}")
    print("\n==========================================================")

    if platform.system() == "Windows":
        input("Press Enter to launch VS Code...")
        launch_vscode()
    else:
        print("You can now open the folder in VS Code...")


if __name__ == "__main__":
    run()