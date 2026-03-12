# 1. SETUP: These tell Terraform which plugins to use
terraform {
  required_providers {
    coder = {
      source  = "coder/coder"
    }
    docker = {
      source  = "kreuzwerker/docker"
    }
  }
}

# 2. IDENTIFICATION: This tells Coder WHO is clicking the button
data "coder_workspace" "me" {}

# 3. THE INTERFACE: Your "Enable GPU" Toggle
data "coder_parameter" "enable_gpu" {
  name         = "gpu_enabled"
  display_name = "Enable GPU Support?"
  type         = "bool"
  default      = "false"
  order        = 1
}

# 4. THE IMAGE: Telling Coder to use your Dockerfile
resource "docker_image" "biocascade_env" {
  name = "coder-biocascade-setup"
  build {
    context = "." 
  }
}

# 5. THE WORKSPACE: Creating the actual "Cloud Desktop"
resource "docker_container" "workspace" {
  image = docker_image.biocascade_env.name
  # This makes the name unique for every student in the hackathon
  name  = "coder-${data.coder_workspace.me.owner}-${data.coder_workspace.me.name}"
  
  # This is a baby step but IMPORTANT: 
  # It connects the container to the Coder agent so you can see it in your browser
  entrypoint = ["sh", "-c", replace(data.coder_agent.main.init_script, "/localhost/i", "localhost")]
  env        = ["CODER_AGENT_TOKEN=${data.coder_agent.main.token}"]
}

# 6. THE AGENT: This is the "soul" of the workspace
resource "coder_agent" "main" {
  arch           = "amd64"
  os             = "linux"
  startup_script = "python3 /app/app.py"
}