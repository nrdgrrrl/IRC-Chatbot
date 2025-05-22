# IRC Server Docker Setup

This directory contains the necessary files to run an IRC server in a Docker container. The setup is configured to work with the IRC Chatbot project.

## Features

- Runs InspIRCd IRC server in a container
- Pre-configured for local development
- Persistent storage for server data
- Easy to set up and run

## Prerequisites

- Docker
- Docker Compose Plugin (included with Docker Desktop or install with `sudo apt install docker-compose-plugin`)

## Quick Start

1. Build and start the server:
```bash
docker compose up -d
```

2. The IRC server will be available at:
   - Host: localhost
   - Port: 6667
   - SSL Port: 6697

## Configuration

The default configuration in `inspircd.conf` is set up for local development with:
- Server name: irc.localhost
- Network name: LocalNet
- Default channels: #general, #help
- No password required for local connections

## Usage with IRC Chatbot

This server is configured to work with the [IRC Chatbot](https://github.com/nrdgrrrl/IRC-Chatbot) project. To use it:

1. Start the IRC server:
```bash
cd ircserver-docker
docker compose up -d
```

2. Update your bot's configuration to use this server:
```json
{
    "server": "localhost",
    "port": 6667,
    "channels": ["#general"],
    "nickname": "your_bot_name"
}
```

## Connecting to the Server

### Using an IRC Client
- Server: localhost
- Port: 6667 (plain) or 6697 (SSL)
- No password required for local connections

### Using the IRC Chatbot
The bot will automatically connect using the configuration provided in your bot's config file.

## Troubleshooting

1. **Server not starting**
   - Check logs: `docker compose logs`
   - Verify ports 6667 and 6697 are not in use
   - Check system resources

2. **Connection issues**
   - Verify the server is running: `docker compose ps`
   - Check if ports are properly exposed: `docker compose port irc 6667`
   - Verify your client/bot configuration

## License

This setup is part of the IRC Chatbot project and is licensed under the MIT License. 