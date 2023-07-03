# Proactive Remote Inspection and Server Management

## Overview

PRISM is a Python script for managing and monitoring server environments. It uses a combination of ping, IPMI and iDRAC interfaces to keep track of the server's status. If a server becomes unreachable, PRISM will attempt to bring it back online using the power cycle command via iDRAC. All notable events, including status checks and power cycle commands, are sent to a specified Discord channel through a webhook.

## Prerequisites

- Docker and Docker-compose installed
- Access to the servers via IPMI and iDRAC interfaces
- A Discord channel for notifications (you will need to create a webhook)

## Usage

PRISM runs inside a Docker container and can be controlled using Docker Compose.

## Configuration

Environment variables for PRISM are specified in the `.env` file in the following format:

```
HOST_IPs=192.168.1.10,192.168.1.11
IDRAC_IPs=192.168.2.10,192.168.2.11
IDRAC_USERs=admin
IDRAC_PASSWORDs=secretpassword
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/TOKEN
```

- `HOST_IPs`: A comma-separated list of IPs for the servers you want to monitor.
- `IDRAC_IPs`: A comma-separated list of iDRAC IPs corresponding to the servers. This should match the order of `HOST_IPs`.
- `IDRAC_USERs`: A comma-separated list of iDRAC usernames. If you have the same username for all iDRAC interfaces, you can just specify it once.
- `IDRAC_PASSWORDs`: A comma-separated list of iDRAC passwords. This should match the order of `IDRAC_USERs`.
- `DISCORD_WEBHOOK_URL`: The URL of the Discord webhook where notifications will be sent.

## Starting PRISM

PRISM can be started using Docker Compose:

```bash
docker-compose up -d
```

## Monitoring

Upon startup, PRISM will perform an initial status check for all specified hosts and iDRAC interfaces. It will also attempt to connect using IPMI to each of the iDRAC interfaces. The results of this check will be sent to the specified Discord channel.

Afterwards, PRISM will continuously monitor the status of the hosts, checking each one every minute. If a host becomes unreachable, PRISM will send a power cycle command via the corresponding iDRAC interface and keep monitoring until the host is back online.

The script will log its actions both in the console and a log file named `PRISM.log`.

## Troubleshooting

If PRISM cannot connect to a host or iDRAC interface, or if the power cycle command fails, an error message will be sent to Discord and logged in `PRISM.log`. Please make sure you have properly set up IPMI and iDRAC access, and that the IPMI tool is installed on the host running PRISM.

## License

PRISM is developed by BinaryBifrost. For more information, visit [https://frostbyte.ai](https://frostbyte.ai).

Please note that PRISM is provided "as is", without warranty of any kind, express or implied. In no event shall the authors or copyright holders be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the software or the use or other dealings in the software.
