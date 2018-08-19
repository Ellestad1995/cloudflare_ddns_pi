# Updating Cloudflare dns record when WAN has dynamic ip
Script written in Python3 for updating dns records at Cloudflare using their api.

It currently only supports updating one ddns at a time.
You can modify this to include all subdomains that has ddns.

## My setup

Router -> Raspberry Pi -> LAN

Raspberry Pi has the script set up in crontab to run every hour.
The Pi works as a proxy server so I can access LAN when not at home.

The script doesn't update anything if the ip hasn't changed.
