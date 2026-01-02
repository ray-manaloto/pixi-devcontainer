This is the **"Remote-First" Architecture**.

Since your Mac (ARM64) and Remote Server (AMD64/EPYC) have different architectures, the "Smartest Sync" is actually **Zero Sync**. Syncing thousands of C++ header files and build artifacts via rsync or mutagen is slow and error-prone.

Instead, we use **VS Code Remote \- SSH**. Your source code stays on the NVMe drive of your Remote Server. Your Mac acts as a "Thin Client" that sends keystrokes and receives UI updates.

### **1\. The Strategy**

1. **Host:** The Dev Container runs on your **Remote Ubuntu Server**.  
2. **User:** We use common-utils to map the Container User to your **Remote Host User**.  
3. **Auth:** We use **SSH Agent Forwarding** to pass your Mac's keys through the Remote Server and into the Container.  
4. **Layering:** The Base Image is "Bare Minimum" (CI). The Dev Container installs "Interactive Tools" (GDB, Starship) on top.

### ---

**2\. Update Pixi Configuration (pixi.toml)**

Your CI image is minimal. We need a dev feature for interactive tools (debuggers, shells) that are only installed when the Dev Container starts.

Ini, TOML

\# ... existing config ...

\# \--- Feature: Interactive Dev Tools \---  
\# These are NOT in the Docker Image. They are installed at runtime.  
\[feature.dev.dependencies\]  
gdb \= "\*"                \# Debugger  
lcov \= "\*"               \# Coverage  
clang-tools \= "\*"        \# clang-format, clang-tidy  
starship \= "\*"           \# Nice Shell Prompt  
bat \= "\*"                \# Better 'cat'  
ripgrep \= "\*"            \# Better 'grep'  
direnv \= "\*"             \# Auto-load .envrc

\[environments\]  
\# The environment specifically for the Dev Container  
dev\_container \= \["stable", "dev", "automation"\]

### ---

**3\. The Dev Container Config (.devcontainer/devcontainer.json)**

This file tells the Remote Server how to launch your environment.

**Key "Smart" Features:**

* **User Mapping:** common-utils maps vscode (internal) to ubuntu (external). You own the files you touch.  
* **SSH Integration:** sshd runs *inside* the container, allowing CLion/Gateway to connect directly.  
* **Env Hydration:** We use a Python one-liner to restore the Pixi environment (since Dev Containers override ENTRYPOINT).

JSON

{  
  "name": "C++ EPYC Zen3 Dev",  
  // 1\. Reference the CI Image (Bare Minimum)  
  "image": "ghcr.io/my-org/cpp-matrix:focal-stable-latest",

  // 2\. User Mapping (The Permission Fix)  
  // Maps 'vscode' inside to Your Remote User (UID 1000\) outside.  
  "remoteUser": "vscode",  
  "updateRemoteUserUID": true,

  // 3\. Dev Container Features (Best Practice)  
  "features": {  
    // A. Identity Management  
    "ghcr.io/devcontainers/features/common-utils:2": {  
      "username": "vscode",  
      "userUid": "automatic",  
      "userGid": "automatic",  
      "installZsh": true  
    },  
    // B. SSH Server (Required for CLion/Gateway)  
    "ghcr.io/devcontainers/features/sshd:1": {  
      "version": "latest"  
    },  
    // C. Git & SSH Config Support  
    "ghcr.io/devcontainers/features/git:1": {}  
  },

  // 4\. Runtime Privileges  
  "runArgs": \[  
    // Allow GDB/LLDB to attach to processes  
    "--cap-add=SYS\_PTRACE",  
    "--security-opt", "seccomp=unconfined",  
    // Use Host Networking (Best performance for Distributed C++ builds)  
    "--network=host"  
  \],

  // 5\. Mounts (SSH Agent Forwarding)  
  // This binds your Mac's SSH Agent (forwarded to the remote) into the container.  
  "mounts": \[  
    "source=${localEnv:SSH\_AUTH\_SOCK},target=/ssh-agent,type=bind,consistency=cached"  
  \],  
  "containerEnv": {  
    "SSH\_AUTH\_SOCK": "/ssh-agent"  
  },

  // 6\. Lifecycle Hooks  
  // A. Install Interactive Tools (Layering 'dev' on top of 'stable')  
  "onCreateCommand": "pixi install \-e dev\_container",

  // B. Restore Frozen Environment  
  // The DevContainer overrides the Docker ENTRYPOINT, so we manually  
  // source the JSON env we generated in the Dockerfile.  
  "postCreateCommand": "python3 \-c \\"import json; d=json.load(open('/app/pixi\_env.json')); print('\\\\n'.join(\[f'export {k}=\\\\\\"{v}\\\\\\"' for k,v in d.items()\]))\\" \> \~/.env\_vars && echo 'source \~/.env\_vars' \>\> \~/.zshrc",

  // 7\. IDE Customizations  
  "customizations": {  
    "vscode": {  
      "extensions": \[  
        "ms-vscode.cpptools",  
        "ms-vscode.cmake-tools",  
        "tamasfe.even-better-toml",  
        "vadimcn.vscode-lldb",  
        "charliermarsh.ruff"  
      \],  
      "settings": {  
        "terminal.integrated.defaultProfile.linux": "zsh",  
        "python.defaultInterpreterPath": "/app/python\_runtime"  
      }  
    }  
  }  
}

### ---

**4\. The Workflow (Mac → Remote → Container)**

#### **Step 1: Configure "Double Hop" SSH**

To let the container use your Mac's keys (e.g., for GitHub), you must enable **Agent Forwarding**.

**File:** \~/.ssh/config (On your Mac)

Code snippet

Host my-epyc-server  
    HostName 192.168.1.100   \# Your Remote Server IP  
    User ubuntu              \# Your Remote User  
    IdentityFile \~/.ssh/id\_ed25519  
    ForwardAgent yes         \# \<--- CRITICAL: Tunnels keys to Remote

#### **Step 2: VS Code (The "Smart Sync")**

1. **Connect:** Open VS Code on Mac → Click Remote Icon → **Connect to Host** → my-epyc-server.  
2. **Clone:** Open the terminal (Ctrl+\`) *in VS Code*. It is now running on the Remote Server.  
   Bash  
   git clone git@github.com:my-org/cpp-project.git

3. **Open:** File → Open Folder → Select \~/cpp-project (on the remote).  
4. **Reopen:** VS Code detects .devcontainer. Click **"Reopen in Container"**.

**Result:**

* You edit on Mac.  
* Files are on the Remote NVMe.  
* Compilation happens in Docker on the Remote CPU.  
* git push uses your Mac's keys.

#### **Step 3: CLion (JetBrains Gateway)**

1. Open **JetBrains Gateway** on Mac.  
2. Connect to my-epyc-server via SSH.  
3. Select **"New Dev Container"**.  
4. Point to the Git Repo on the server.  
5. Gateway will install the backend *inside* the container and stream the UI to your Mac.

#### **Step 4: CLI (Headless)**

If you just want a shell from your Mac terminal:

Bash

\# SSH to Remote  
ssh my-epyc-server

\# Enter Container  
cd cpp-project  
pixi run devcontainer up \--workspace-folder .  
pixi run devcontainer exec \--workspace-folder . zsh

### ---

**5\. Alternative: "Physical Sync" (Mutagen)**

If you **absolutely must** have the source files on your Mac's hard drive (e.g., for offline viewing or using Mac-only tools), use **Mutagen**. It is the only tool fast enough for C++.

**Warning:** This uses significant CPU to watch files and may lag with large C++ build trees.

1. **Install:** brew install mutagen-io/mutagen/mutagen  
2. **Create Config (mutagen.yml):**  
   YAML  
   sync:  
     defaults:  
       mode: "two-way-safe"  
       ignore:  
         paths: \["build/", ".pixi/", ".git/"\]  
     dev:  
       alpha: "./"  
       beta: "user@my-epyc-server:\~/workspace/cpp-project"

3. **Start:** mutagen sync monitor  
4. **Connect:** Point VS Code Remote-SSH to the *remote* folder, not the local one.