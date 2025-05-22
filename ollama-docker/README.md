# Ollama Docker Setup

This directory contains the necessary files to run Ollama in a Docker container. The setup is configured to work with the IRC Chatbot project.

## Features

- Runs Ollama API server in a container
- Pre-configured for CPU usage
- Persistent storage for models
- Easy to set up and run
- Configurable for GPU support

## Prerequisites

- Docker
- Docker Compose Plugin (included with Docker Desktop or install with `sudo apt install docker-compose-plugin`)
- (Optional) NVIDIA GPU with drivers and nvidia-docker2 for GPU support

## Quick Start

1. Build and start the server:
```bash
docker compose up -d
```

2. Pull the default model (tinyllama):
```bash
docker exec -it ollama-server ollama pull tinyllama
```

3. The Ollama API will be available at:
   - Host: localhost
   - Port: 11434
   - API URL: http://localhost:11434/api/generate

## Configuration

### CPU Configuration (Default)

The default `docker-compose.yml` is configured for CPU usage with:
- 4 CPU cores maximum
- 2 CPU cores minimum
- Persistent storage for models
- No GPU requirements

### GPU Configuration

To enable GPU support:

1. Install NVIDIA drivers and nvidia-docker2:
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. Modify `docker-compose.yml` to add GPU support:
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-server
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

3. Restart the container:
```bash
docker compose down
docker compose up -d
```

## Available Models

The following models are recommended for the IRC Chatbot:

1. **tinyllama** (Default, CPU-friendly):
```bash
docker exec -it ollama-server ollama pull tinyllama
```

2. **mistral** (Better quality, needs more resources):
```bash
docker exec -it ollama-server ollama pull mistral
```

3. **llama2** (High quality, needs significant resources):
```bash
docker exec -it ollama-server ollama pull llama2
```

## Usage with IRC Chatbot

This server is configured to work with the [IRC Chatbot](https://github.com/nrdgrrrl/IRC-Chatbot) project. To use it:

1. Start the Ollama server:
```bash
cd ollama-docker
docker compose up -d
```

2. Update your bot's configuration to use this server:
```json
{
    "ollama": {
        "url": "http://localhost:11434/api/generate"
    }
}
```

## Resource Management

### CPU Usage
- Default configuration uses 2-4 CPU cores
- Adjust the `cpus` limits in `docker-compose.yml` based on your system
- Monitor CPU usage: `docker stats ollama-server`

### Memory Usage
- tinyllama: ~2GB RAM
- mistral: ~4GB RAM
- llama2: ~8GB RAM

### GPU Usage (if enabled)
- Monitor GPU usage: `nvidia-smi`
- Adjust model selection based on your GPU memory

## Troubleshooting

1. **Server not starting**
   - Check logs: `docker compose logs`
   - Verify port 11434 is not in use
   - Check system resources

2. **Model loading issues**
   - Check available disk space
   - Verify internet connection
   - Check model compatibility

3. **GPU issues**
   - Verify NVIDIA drivers: `nvidia-smi`
   - Check nvidia-docker installation
   - Verify GPU memory availability

## License

This setup is part of the IRC Chatbot project and is licensed under the MIT License. 