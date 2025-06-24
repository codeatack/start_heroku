import os
import subprocess
import sys
import pathlib
import urllib.request
import time
import argparse

CONFIG_FILE = pathlib.Path(__file__).parent / 'config'

def get_saved_directory():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_directory(directory):
    with open(CONFIG_FILE, 'w') as f:
        f.write(str(directory))

def download_requirements_files():
    try:
        req_path = pathlib.Path('requirements.txt')
        opt_req_path = pathlib.Path('optional_requirements.txt')
        urllib.request.urlretrieve("https://raw.githubusercontent.com/codeatack/Heroku/refs/heads/master/requirements.txt", req_path)
        print(f"Downloaded requirements.txt to {req_path}")
        urllib.request.urlretrieve("https://raw.githubusercontent.com/codeatack/Heroku/refs/heads/master/optional_requirements.txt", opt_req_path)
        print(f"Downloaded optional_requirements.txt to {opt_req_path}")
        return req_path, opt_req_path
    except Exception as e:
        print(f"Error downloading requirements files: {str(e)}")
        return None, None

def install_python_dependencies():
    try:
        req_path, opt_req_path = download_requirements_files()
        if not req_path or not opt_req_path:
            return False
        cmd = ['python3.10', '-m', 'pip', 'install', '--no-warn-script-location', '--no-cache-dir', '-U', '-r', str(opt_req_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to install optional_requirements.txt: {result.stderr}")
            return False
        print("Successfully installed optional_requirements.txt")
        cmd = ['python3.10', '-m', 'pip', 'install', '--no-warn-script-location', '--no-cache-dir', '-U', '-r', str(req_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Failed to install requirements.txt: {result.stderr}")
            return False
        print("Successfully installed requirements.txt")
        for file_path in [req_path, opt_req_path]:
            if file_path.exists():
                file_path.unlink()
                print(f"Removed {file_path}")
        return True
    except Exception as e:
        print(f"Error installing Python dependencies: {str(e)}")
        return False

def install_dependencies():
    try:
        cmd = (
            "apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y "
            "build-essential curl ffmpeg neofetch gcc git libavcodec-dev libavdevice-dev "
            "libavformat-dev libavutil-dev libcairo2 libmagic1 libswscale-dev openssl "
            "python3.10 python3.10-dev python3-pip wkhtmltopdf"
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("System dependencies installed successfully")
        else:
            print("Failed to install system dependencies:")
            print(result.stderr)
            return False
        if not install_python_dependencies():
            return False
        return True
    except Exception as e:
        print(f"Error installing dependencies: {str(e)}")
        return False

def configure_git():
    try:
        subprocess.run(['git', 'remote', 'remove', 'origin'], check=False, capture_output=True, text=True)
        subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/coddrago/Heroku'], check=True, capture_output=True, text=True)
        subprocess.run(['git', 'fetch', 'origin'], check=True, capture_output=True, text=True)
        subprocess.run(['git', 'reset', '--hard', 'origin/master'], check=True, capture_output=True, text=True)
        print("Git repository configured successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error configuring git repository: {e.stderr}")
    except Exception as e:
        print(f"Error configuring git repository: {str(e)}")

def rollback_to_commit():
    try:
        subprocess.run(['git', 'fetch', 'origin'], check=True, capture_output=True, text=True)
        subprocess.run(['git', 'reset', '--hard', '884f82a412d10eb68a6ec79f2ec7acc28c8ea4f1'], check=True, capture_output=True, text=True)
        print("Successfully rolled back to commit 884f82a412d10eb68a6ec79f2ec7acc28c8ea4f1")
    except subprocess.CalledProcessError as e:
        print(f"Error rolling back to commit: {e.stderr}")
    except Exception as e:
        print(f"Error rolling back to commit: {str(e)}")

def download_proxypass(target_dir):
    proxypass_path = pathlib.Path(target_dir) / 'heroku' / 'web' / 'proxypass.py'
    url = "https://raw.githubusercontent.com/codeatack/Heroku/refs/heads/master/heroku/web/proxypass.py"
    try:
        if proxypass_path.exists():
            proxypass_path.unlink()
            print(f"Removed file {proxypass_path}")
        proxypass_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, proxypass_path)
        print(f"Downloaded new proxypass.py to {proxypass_path}")
    except Exception as e:
        print(f"Error downloading proxypass.py: {str(e)}")

def run_heroku(port=None):
    attempt = 0
    max_attempts = 3
    while attempt < max_attempts:
        try:
            if 'LAVHOST' in os.environ and os.environ['LAVHOST']:
                cmd = ['/usr/bin/python3.10', '-m', 'heroku']
            else:
                cmd = ['python3.10', '-m', 'heroku']
            if '--root' in sys.argv:
                cmd.append('--root')
            if port:
                cmd.extend(['--port', str(port)])
            print(f"Executing command: {' '.join(cmd)} (Attempt {attempt + 1}/{max_attempts})")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in process.stdout:
                print(line, end='', flush=True)
            return_code = process.wait()
            if return_code == 0:
                print("Heroku completed successfully")
                return return_code
            else:
                print(f"Heroku failed with code {return_code}, trying with --root...")
                if '--root' not in sys.argv:
                    if 'LAVHOST' in os.environ and os.environ['LAVHOST']:
                        cmd = ['/usr/bin/python3.10', '-m', 'heroku', '--root']
                    else:
                        cmd = ['python3.10', '-m', 'heroku', '--root']
                    if port:
                        cmd.extend(['--port', str(port)])
                    print(f"Executing command: {' '.join(cmd)} (Attempt {attempt + 1}/{max_attempts})")
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    for line in process.stdout:
                        print(line, end='', flush=True)
                    return_code = process.wait()
                    if return_code == 0:
                        print("Heroku completed successfully with --root")
                        return return_code
            attempt += 1
            if attempt < max_attempts:
                print(f"Heroku failed with code {return_code}, restarting in 1 seconds...")
                time.sleep(1)
            else:
                print(f"Failed to start Heroku after {max_attempts} attempts. Rolling back to commit 884f82a412d10eb68a6ec79f2ec7acc28c8ea4f1...")
                rollback_to_commit()
                print("Exiting due to repeated failures.")
                sys.exit(1)
        except Exception as e:
            print(f"Error running heroku: {str(e)}")
            attempt += 1
            if attempt < max_attempts:
                print(f"Restarting in 1 seconds... (Attempt {attempt}/{max_attempts})")
                time.sleep(1)
            else:
                print(f"Failed to start Heroku after {max_attempts} attempts. Rolling back to commit 884f82a412d10eb68a6ec79f2ec7acc28c8ea4f1...")
                rollback_to_commit()
                print("Exiting due to repeated failures.")
                sys.exit(1)

def run_hikka():
    parser = argparse.ArgumentParser(description='Run Heroku with configuration')
    parser.add_argument('--port', type=int, help='Port for Heroku')
    parser.add_argument('--root', action='store_true', help='Run Heroku with --root')
    parser.add_argument('--del-conf', action='store_true', help='Delete configuration file')
    args = parser.parse_args()
    try:
        if args.del_conf and CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            print(f"Deleted configuration file {CONFIG_FILE}")
        saved_dir = get_saved_directory()
        if not saved_dir:
            configure_git()
            os.chdir('..')
            saved_dir = pathlib.Path.cwd().resolve()
            print("First run: attempting to install dependencies...")
            install_dependencies()
            save_directory(saved_dir)
            print(f"Configuration created: saved directory {saved_dir}")
            return
        web_dir = pathlib.Path(saved_dir) / 'heroku' / 'web'
        download_proxypass(saved_dir)
        if 'NO_PROXY' not in os.environ:
            os.environ['NO_PROXY'] = ''
            print("Environment variable NO_PROXY set to empty")
        os.chdir(saved_dir)
        print(f"Starting Heroku in directory {saved_dir}...")
        run_heroku(port=args.port)
    except FileNotFoundError:
        print("Error: Could not navigate to target directory")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    run_hikka()
