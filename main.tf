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

data "coder_workspace" "me" {}

# INTERACTIVE INTERFACE: Using the guide's bool type for a toggle [cite: 13]
data "coder_parameter" "gpu_enabled" {
  name         = "gpu_enabled"
  display_name = "Enable GPU Support?"
  type         = "bool"      # [cite: 13]
  default      = "false"     # [cite: 32, 72]
  order        = 1           # Places this at the top of the form [cite: 111, 113]
  mutable      = true        # Allows users to toggle it on restart [cite: 139]
}

resource "coder_agent" "main" {
  arch           = "amd64"
  os             = "linux"
  # This matches your verified internal path /workspace/app/app.py
  startup_script = "python3 /workspace/app/app.py"

  display_apps {
    vscode          = true
    port_forward_6d = true
  }
}

resource "docker_image" "biocascade_image" {
  name = "coder-biocascade"
  build {
    context = "."
  }
}

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count
  image = docker_image.biocascade_image.name
  name  = "coder-${data.coder_workspace.me.owner}-${data.coder_workspace.me.name}"
  
  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost/i", "localhost")]
  env        = ["CODER_AGENT_TOKEN=${coder_agent.main.token}"]
}