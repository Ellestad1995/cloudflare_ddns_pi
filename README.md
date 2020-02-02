# Updating Cloudflare dns record when WAN has dynamic ip
Script is written in Python3 for updating dns records at Cloudflare using their api.

Uses a json file hosted on a private gist on github.

The script authenticates to github to retrieve the newest `dns_records` gist and updates the entries on Cloudflare.

## Setup 

1. gist
Create a private gist on Github to host the file.

Name `dns_records`

Example:
```json
{
  "dns_records": [
    {
      "domain": "nivlheim.cloud",
      "records": [
        {
          "type": "A",
          "name": "bifrost.nivlheim.cloud",
          "content": "",
          "ttl": "1",
          "proxied": true
        },
        {
          "type": "A",
          "name": "plex.nivlheim.cloud",
          "content": "",
          "ttl": "1",
          "proxied": true
        }
      ]
    },
    {
      "domain": "joaprint.xyz",
      "records": [
        {
          "type": "A",
          "name": "www.joaprint.xyz",
          "content": "",
          "ttl": "1",
          "proxied": true
        },
        {
          "type": "A",
          "name": "plex.joaprint.xyz",
          "content": "",
          "ttl": "1",
          "proxied": true
        }
      ]
    }
  ]
}
```

2. Setup systemd or task scheduler

Systemd or windows task scheduler is used to run the docker container on a schedule. The task also updates the project files.

```systemd
[Unit]
Description=Executes mystuff
After=default.target docker_network_apps.service
Requires=default.target docker_network_apps.service

[Service]
Type=oneshot
User=root
ExecStartPre=/usr/bin/docker pull mystuff:stable
ExecStartPre=-/bin/bash -c "/usr/bin/docker rm -f mystuffcontainer 2>/dev/null"
ExecStart=/bin/bash -c "/usr/bin/docker run --name mystuffcontainer mystuff:stable mystuff"
```

```systemd
[Unit]
Description=My stuff runs at 00:10 sharp.

[Timer]
OnCalendar=00:10:00

[Install]
WantedBy=multi-user.target
```

3. Setup the docker project

