import subprocess

with open("requirements.txt", "r") as f:
    lines = f.readlines()

skip_pkgs = {"Brotli", "cffi", "cryptography", "weasyprint", "cairocffi", "psycopg2-binary", "pango", "zopfli"}

for line in lines:
    line = line.strip()
    if not line or line.startswith("#"): continue
    
    pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0]
    if pkg_name in skip_pkgs:
        print(f"Skipping {pkg_name}")
        continue
    
    # install using pip
    cmd = ["pip", "install", pkg_name]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Done.")
