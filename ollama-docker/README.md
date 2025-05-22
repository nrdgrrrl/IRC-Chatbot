# Ollama Docker Setup

This directory contains the Docker configuration for running Ollama in a container. Ollama is used to provide AI-powered responses for the IRC chatbot.

## Features

- Runs Ollama API server in a container
- Pre-configured for CPU usage
- Persistent storage for models
- Easy to set up and run
- Configurable for GPU support

## Prerequisites

- Docker and Docker Compose Plugin
- At least 4GB of RAM for the mistral model (2GB for tinyllama)
- CPU with AVX2 support (recommended for better performance)

## Quick Start

1. Build and start the container:
```bash
docker compose up -d
```

2. Pull the desired model:
```bash
# For CPU-friendly usage (2GB RAM)
docker exec -it ollama-server ollama pull tinyllama

# For better quality responses (4GB RAM)
docker exec -it ollama-server ollama pull mistral
```

3. Verify the container is running:
```bash
docker compose ps
```

## Configuration

The Ollama server runs on port 11434 by default. You can modify the port in `docker-compose.yml` if needed.

### Environment Variables

- `OLLAMA_HOST`: Host to bind to (default: 0.0.0.0)
- `OLLAMA_ORIGINS`: Allowed origins for CORS (default: *)
- `OLLAMA_MODELS`: Path to models directory (default: /root/.ollama)

## Available Models

### tinyllama (Default)
- Smallest model (~2GB RAM)
- Fastest response time
- Good for basic conversations
- Best for systems with limited resources

### mistral (Recommended)
- Medium-sized model (~4GB RAM)
- Better response quality
- Good balance of speed and quality
- Works well on modern CPUs

### Other Models
You can pull other models as needed:
```bash
# List available models
docker exec -it ollama-server ollama list

# Pull a specific model
docker exec -it ollama-server ollama pull <model-name>
```

## GPU Support (Optional)

To enable GPU support, you need to:

1. Install NVIDIA drivers on your host system
2. Install NVIDIA Container Toolkit:
```bash
# Add NVIDIA package repositories
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

3. Modify `docker-compose.yml` to add GPU support:
```yaml
services:
  ollama-server:
    # ... existing configuration ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

4. Restart the container:
```bash
docker compose down
docker compose up -d
```

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check Docker logs: `docker compose logs`
   - Ensure port 11434 is not in use
   - Verify you have enough system resources

2. **Model download fails**
   - Check internet connection
   - Verify you have enough disk space
   - Try pulling the model again

3. **Slow responses**
   - Check system resource usage
   - Consider using a smaller model
   - Enable GPU support if available

### Logs

View container logs:
```bash
docker compose logs -f
```

## Security Notes

- The container runs as root by default
- The API is accessible to all hosts (0.0.0.0)
- Consider adding authentication if exposed to the internet

## Maintenance

### Updating Models

To update a model to its latest version:
```bash
docker exec -it ollama-server ollama pull <model-name>
```

### Cleaning Up

To remove unused models and free up space:
```bash
docker exec -it ollama-server ollama rm <model-name>
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details. 