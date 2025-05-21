# IRC Server Docker Setup

This directory contains the necessary files to run an IRC server using Docker. The server is configured to work with the IRC Chatbot project.

## Features

- Uses ngIRCd, a lightweight IRC server
- Pre-configured for bot interactions
- Easy to set up and run
- Configurable through environment variables

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. Build and start the server:
```bash
docker-compose up -d
```

2. The IRC server will be available at:
   - Host: localhost (or your machine's IP)
   - Port: 6667
   - Channel: #bots

## Configuration

### Server Settings

The server is configured through `ngircd.conf`. Key settings include:

- Server name: irc.local
- Channel: #bots
- Max connections: 20
- No password required for basic access

### Customization

You can customize the server by:

1. Modifying `ngircd.conf`:
   - Change server name
   - Add operator passwords
   - Modify channel settings
   - Adjust connection limits

2. Updating `ngircd.motd`:
   - Customize the welcome message

3. Adjusting `docker-compose.yml`:
   - Change port mappings
   - Modify container settings

## Security Notes

- The default configuration is for development/testing
- For production use:
   - Enable operator passwords
   - Restrict IP access
   - Use SSL/TLS
   - Set appropriate connection limits

## Usage with IRC Chatbot

This server is configured to work with the [IRC Chatbot](https://github.com/nrdgrrrl/IRC-Chatbot) project. To use it:

1. Start the IRC server:
```bash
cd ircserver-docker
docker-compose up -d
```

2. Update your bot's configuration to use this server:
```json
{
    "irc": {
        "server": "localhost",
        "port": 6667,
        "channel": "#bots"
    }
}
```

## Troubleshooting

1. **Can't connect to server**
   - Check if the container is running: `docker ps`
   - Verify port 6667 is not in use
   - Check firewall settings

2. **Server not starting**
   - Check logs: `docker-compose logs`
   - Verify configuration files
   - Check port availability

## License

This setup is part of the IRC Chatbot project and is licensed under the MIT License. 