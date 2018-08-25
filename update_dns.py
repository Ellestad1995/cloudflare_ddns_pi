#!/usr/local/bin/python3

import requests
import json
import sys

# Change apiKey, myDomain, emailAddress and ddns
apiKey = "xxxxxxxxxxxxxxxx"
myDomain = "example.com"
emailAddress = "mail@example.com"
ddns = "proxy.example.com" # subdomain to be updated

baseUrl = "https://api.cloudflare.com/client/v4/"
cfIp = "" # The ip cloudflare has for the ddns - this is updated by the script
header ={ "X-Auth-Email" : emailAddress, "X-Auth-Key" : apiKey, "Content-Type" : "application/json" }

debug = true # Enable debugging to print data

def printUsage():
    print("Usage is: " + sys.agv[0] + "<path/to/records.json> or <domain>")
    print("Currently only supports reading records from file")

def getGlobalIp():
    # Get public ip address of network
    r = requests.get('https://ipinfo.io/ip')
    ip = (r.text).rstrip()
    if(debug):
        print(ip)
    return ip

def readRecordsFile():
    try:
        with open(sys.argv[1],"r") as file:
            content = file.read()
            json_data = json.loads(content)
            file.close()
            return json_data
    except:
        print("Could not read file")


def main():
    if len(sys.argv != 2):
        printUsage()
        sys.exit(0)

    globalIP = getGlobalIp()
    records = readRecordsFile()

    for domain in len(records):
        if debug:
            print("Working on: " + records[domain])
        baseUrl = "https://api.cloudflare.com/client/v4/"
        if debug:
            print("domain: " + records[domain]["domain"])

        # Try to the zone id for the domain
        # If this fails we need to end the script
        try:
            getZoneFor(records[domain]["domain"])
        except as e:
            if hasattr(e, 'message'):
                print(e.message)
                sys.exit(1)
            else:
                print(e)

        # Loop over all the domains
        for d in records[domain]["records"]:
            record = records[domain]["records"][d]
            ddns = record["name"]

            if debug:
                print("Working on " + ddns)

            cloudFId, cloudFIpaddr = ""

            try:
                cloudFId, cloudFIpaddr = getIdFor(ddns)
            except as e:
                if debug:
                    print(e)
            if cloudFId == "" && cloudFIpaddr == "":
                # Creating new record
                try:
                    createRecordFor(domain = ddns, type=record["type"], content=globalIP, ttl=120, proxied=record["proxied"])
                except as e:
                    print(e.message)
            else:
                # Already exist update the existing

                if cloudFIpaddr == globalIP:
                    # No need to update if ip isn't changed
                    if debug:
                        print("global ip addr didn't change. Dont update")
                else:
                    try:
                        updateRecordFor(domain = ddns, type=record["type"], content=globalIP, ttl=120, proxied=record["proxied"])
                    except as e:
                        print(e.message)
    sys.exit(0)

def getZoneFor(domain):
    # Get the zone id
    baseUrl += "zones/"
    parameters = {'name':domain}
    zoneReq = requests.get(url= baseUrl, headers= header, params= parameters)

    if zoneReq.status_code == requests.codes.ok:
        # Determine if request was successfull
        response = json.loads(zoneReq.text)
        if response["success"] == True && len(response["result"] > 0):
            zoneId = response["result"][0]["id"]
            # Update the baseurl with zoneId
            baseUrl += zoneId
            baseUrl += "/"
        else:
            if debug:
                print("Could not get zoneid")
            raise Exception("Could not get zoneid")

# Get the record id of the domain
def getIdFor(domain):
    payload = {'type':'A', 'name':domain}
    baseUrl += "dns_records/"
    s = requests.get(baseUrl, headers = header, params = payload )
    if s.status_code == requests.codes.ok:
        if debug:
            print(s.url)
        json_obj = json.loads(s.text)
        if json_obj["success"] == True:
            if debug:
                print(json.dumps(json_obj, indent=4, sort_keys=True))
            # Check if result contains no data
            if len(json_obj["result"]) > 0:
                cfIdentifier = json_obj["result"][0]["id"]
                cfIp = json_obj["result"][0]["content"]
                #baseUrl += cfIdentifier
                if debug:
                    print(cfIdentifier)
                return cfIdentifier, cfIp
            else:
                raise Exception("Record for domain " + domain + "does not exist yet")
                # Means the record doesn't exist - need to create it
                #print("Creating dns record")
    else:
        raise Exception("Request failed")

def createRecordFor(domain, type, content, ttl, proxied):
    if debug:
        print("Creating record for" + domain)

    create_dns_record_payload = json.dumps({'type':type, 'name':domain, 'content':content, 'proxied':proxied, 'ttl':ttl, 'priority':10})
    create_dns_record_req = requests.post(baseUrl, headers = header, data = create_dns_record_payload)
    if create_dns_record_req.ok == requests.codes.ok :
        # Successfully created domain
        if debug:
            print(create_dns_record_req.text)
    else:
        # Could not create dns record
        if debug:
            print("Could not create dns record ")
            print(create_dns_record_req.url)
            print(create_dns_record_req.text)
        raise Exception("Could not create dns record for " + domain + " at: " + content)


def updateRecordFor(domain, type, content, ttl, proxied):
    if debug:
        print("Update record " + domain + "with ip: " + ipaddr)

    update_payload = {'type':type, 'name':domain,'content':content, 'proxied':proxied}
    updateReq = requests.put(baseUrl, headers = header, params = update_payload)
    if updateReq.status_code == requests.codes.ok:
        # request was successfull
        response = json.loads(updateReq.text)
        if response["success"] == True:
            # Update was successfull
            if debug:
                print("Update on " + domain + "was successfull")
        else:
            if debug:
                print("Update on " + domain + "failed")
    else:
        raise Exception("Request failed. Network may be down")


if __name__ == "__main__":
    main()
    sys.exit(0)
