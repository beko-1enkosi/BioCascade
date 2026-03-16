# 1. SETUP: Tell Terraform which plugins to use
terraform {
  required_providers {
    coder = {
      source = "coder/coder"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

# 2. DATA: Get user and workspace info
data "coder_workspace" "me" {}

# 3. INTERFACE: The Interactive Parameter (The "Toggle")
data "coder_parameter" "gpu_enabled" {
  name         = "gpu_enabled"
  display_name = "Enable GPU Support?"
  type         = "bool"
  default      = "false"
  order        = 1
}

# 4. AGENT: The "Soul" of the workspace (where VS Code lives)
resource "coder_agent" "main" {
  arch           = "amd64"
  os             = "linux"
  # This matches the /workspace/app/app.py path we found in your Exec check!
  startup_script = "python3 /workspace/app/app.py"

  # Adds a button in the Coder UI to open your app
  display_apps {
    vscode          = true
    port_forward_6d = true
  }
}

# 5. IMAGE: Build your Dockerfile locally
resource "docker_image" "biocascade_image" {
  name = "coder-biocascade"
  build {
    context = "."
  }
}

# 6. CONTAINER: The live workspace
resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count
  image = docker_image.biocascade_image.name
  
  # Uses the user's name to keep the container unique
  name  = "coder-${data.coder_workspace.me.owner}-${data.coder_workspace.me.name}"
  
  # Connects the container to the Coder dashboard
  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost/i", "localhost")]
  env        = ["CODER_AGENT_TOKEN=${coder_agent.main.token}"]
  
  # Keeps the container from shutting down immediately
  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }
}