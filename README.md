# IRC Chatbot

A modular IRC chatbot that uses Ollama for AI-powered responses. The bot can be configured to use different models and respond to various commands.

## Features

- Modular command system
- AI-powered responses using Ollama
- Configurable through JSON
- Multiple model support (tinyllama, mistral, etc.)
- Docker support for both IRC server and Ollama

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose Plugin (for IRC server and Ollama)
- Git
- (Optional) IRC client for watching the bots interact

## Development Setup

### Setting up a Python Virtual Environment

It's recommended to use a Python virtual environment to manage dependencies. Here's how to set it up:

1. Create a virtual environment:
```bash
# Using venv (built into Python)
python -m venv venv

# Or using virtualenv
pip install virtualenv
virtualenv venv
```

2. Activate the virtual environment:
```bash
# On Linux/macOS
source venv/bin/activate

# On Windows
.\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. When you're done working, you can deactivate the virtual environment:
```bash
deactivate
```

Note: Always activate the virtual environment before running the bot or installing new dependencies.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nrdgrrrl/IRC-Chatbot.git
cd IRC-Chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the IRC server (optional, if you don't have an IRC server):
```bash
cd ircserver-docker
docker compose up -d
```

4. Set up Ollama (optional, if you don't have Ollama running):
```bash
cd ollama-docker
docker compose up -d
# Pull the default model (tinyllama)
docker exec -it ollama-server ollama pull tinyllama
# Or pull the smarter model (mistral)
docker exec -it ollama-server ollama pull mistral
```

## Configuration

1. Copy the example configuration:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your settings:
```json
{
    "irc": {
        "server": "localhost",
        "port": 6667,
        "channel": ["#general"]
    },
    "bot": {
        "name": "your_bot_name",
        "personality": "a friendly and helpful AI assistant",
        "model": "mistral",
        "always_respond_to": "Victoria"
    },
    "ollama": {
        "url": "http://localhost:11434/api/generate",
        "temperature": 0.7,
        "max_tokens": 100
    },
    "logging": {
        "enabled": true,
        "log_dir": "logs"
    },
    "files": {
        "prompt_file": "prompts.json"
    },
    "behavior": {
        "off_topic_chance": 0.12,
        "tone_chance": 0.25,
        "post_delay_seconds": 20,
        "post_delay_jitter": 10,
        "max_concurrent_requests": 1,
        "conversation_history_length": 6
    }
}
```

## Usage

1. Start the bot:
```bash
# Basic usage
python bot.py

# Or with custom personality and model
python bot.py --bot-name BotB --personality "a sarcastic AI who loves dad jokes" --model mistral
```

2. The bot will connect to the IRC server and join the configured channels.

3. Available commands:
   - `!help` - Show available commands
   - `!ask <question>` - Ask the AI a question
   - `!model <name>` - Switch to a different model
   - `!temperature <value>` - Adjust response temperature
   - `!max_tokens <value>` - Adjust maximum response length

### Model Selection

The bot supports multiple models with different characteristics:

1. **tinyllama** (Default, CPU-friendly):
   - Fastest response time
   - Lowest memory usage (~2GB RAM)
   - Good for basic conversations
   - Best for systems with limited resources

2. **mistral** (Recommended, Balanced):
   - Better response quality
   - Moderate memory usage (~4GB RAM)
   - Good balance of speed and quality
   - Works well on modern CPUs

To switch models:
1. Edit `config.json` and change the `model` field
2. Or use the `--model` command-line argument
3. Or use the `!model` command in chat

### Watching the Bots Interact

You can watch the bots interact by connecting to the IRC server using any IRC client. Here are some popular options:

1. **HexChat** (Cross-platform):
   - Download from [hexchat.net](https://hexchat.net/)
   - Connect to server: `localhost`
   - Port: `6667`
   - Join channel: `#general`

2. **mIRC** (Windows):
   - Download from [mirc.com](https://www.mirc.com/)
   - Connect to server: `localhost`
   - Port: `6667`
   - Join channel: `#general`

3. **Textual** (macOS):
   - Download from [textual.app](https://www.codeux.com/textual/)
   - Connect to server: `localhost`
   - Port: `6667`
   - Join channel: `#general`

4. **irssi** (Terminal-based, Linux/macOS):
   ```bash
   # Install irssi
   sudo apt install irssi  # Ubuntu/Debian
   brew install irssi      # macOS

   # Connect to server
   irssi -c localhost -p 6667
   /join #general
   ```

Once connected, you can:
- Watch the bots interact with each other
- Send commands to the bots using the `!` prefix
- Chat with the bots directly
- Monitor their responses and behavior

## Docker Setup

### IRC Server
See [ircserver-docker/README.md](ircserver-docker/README.md) for details.

### Ollama Server
See [ollama-docker/README.md](ollama-docker/README.md) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.