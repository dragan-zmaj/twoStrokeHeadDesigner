# Combustion Head Designer - Environment Setup

This document covers the prerequisites and setup commands needed to run the Combustion Head Designer on Windows 11 using WSL2, Docker, and FreeCAD.

# Prerequisites
- Windows 11 operating system
- Ubuntu distribution installed from Microsoft Store with WSL2
- Docker Desktop
- FreeCAD docker Client

### Step 1: WSL2 Installation
- install ubuntu from microsoft store
https://apps.microsoft.com/detail/9PDXGNCFSCZV?hl=en-us&gl=RS&ocid=pdpshare
# powershell
# Check WSL version
wsl -l -v

# Ensure WSL2 is default (if not already)
wsl --set-default-version 2

# If Ubuntu shows version 1, convert it:
wsl --set-version Ubuntu 2

### Step 2: Install Docker Desktop
- Download Docker Desktop for Windows (AMD64) from docker.com
- Run the installer
- Important: Check "Use WSL 2 instead of Hyper-V" during installation
- Restart your PC when prompted

### Step 3: Configure Docker Desktop for WSL
- Launch Docker Desktop
- Go to Settings → Resources → WSL Integration
- Enable "Enable integration with my default WSL distro"
- Enable integration for Ubuntu
- Click "Apply & Restart"

### Step 4: Verify Docker in Ubuntu Terminal
- Open Ubuntu terminal

docker --version

docker run hello-world

### Step 5: Pull the FreeCAD Docker Image

docker pull amrit3701/freecad-cli:latest

### Step 6: Run FreeCAD

docker run --rm amrit3701/freecad-cli:latest FreeCADCmd --version
docker run -it amrit3701/freecad-cli:latest bash

### Step 7: Run your script
# this should be run from inside git repo in WSL2 environment
docker run --rm -v "$PWD":/workspace -w /workspace amrit3701/freecad-cli:latest FreeCADCmd your_script.py

