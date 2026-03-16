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

# 1. GPU Toggle (Boolean)
data "coder_parameter" "gpu_enabled" {
  name         = "gpu_enabled"
  display_name = "Enable GPU Support?"
  type         = "bool"
  default      = "false"
  order        = 1
  mutable      = true
}

# 2. Analysis Mode (Dropdown Menu)
data "coder_parameter" "analysis_mode" {
  name         = "analysis_mode"
  display_name = "BioCascade Analysis Mode"
  description  = "Select the depth of the AI diagnostic report"
  type         = "string"
  default      = "standard"
  order        = 2
  mutable      = true

  option {
    name  = "Standard Report"
    value = "standard"
  }

  option {
    name  = "Deep Clinical Scan (Slower)"
    value = "deep"
  }
}

resource "coder_agent" "main" {
  arch           = "amd64"
  os             = "linux"
  startup_script = "python3 /workspace/app/app.py"

  display_apps {
    vscode = true
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
  name  = "coder-${data.coder_workspace.me.id}"
  
  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost/i", "localhost")]
  env        = ["CODER_AGENT_TOKEN=${coder_agent.main.token}"]
}