#!/usr/local/bin/python3

import requests
import json
import sys

##
# Change apiKey, myDomain, emailAddress and ddns
##
apiKey = ""
emailAddress = ""

header ={ "X-Auth-Email" : emailAddress, "X-Auth-Key" : apiKey, "Content-Type" : "application/json" }
baseUrl = "https://api.cloudflare.com/client/v4/"

debug = True # Enable debugging to print data

def printUsage():
    print("Usage is: " + sys.argv[0] + "<path/to/records.json> or <domain>")
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

    globalIP = getGlobalIp()
    records = readRecordsFile()
    global baseUrl

    for domain in records:
        if debug:
            print("Started on: " + json.dumps(domain))
        baseUrl = "https://api.cloudflare.com/client/v4/"
        if debug:
            print("\n\ndomain: " + domain["domain"] + "\n\n")

        ##
        #Zone id is unique for each domain, perhaps
        ##
        zoneid = ""
        # Try to the zone id for the domain
        # If this fails we need to end the script
        try:
            zoneid = getZoneFor(domain["domain"])
        except Exception as e:
            print(e)
            print("\nFailed to get zone for: " + domain["domain"] + "\n")
            sys.exit(1)

        # Loop over all the domains
        for d in domain["records"]:
            ddns = d["name"]

            if debug:
                print("Working on " + ddns)

            cloudFId = ""
            cloudFIpaddr = ""

            try:
                cloudFId, cloudFIpaddr = getIdFor(domain=ddns, inZone=zoneid)
            except Exception as e:
                if debug:
                    print(e)

            if cloudFId == "" and cloudFIpaddr == "":
                # Creating new record
                try:
                    createRecordFor(domain = ddns, inZone=zoneid, type=d["type"], content=globalIP, ttl=120, proxied=d["proxied"])
                except Exception as e:
                    print(e)
            else:
                # Already exist update the existing
                if cloudFIpaddr == globalIP:
                    # No need to update if ip isn't changed
                    if debug:
                        print("global ip addr didn't change. Dont update")
                else:
                    try:
                        updateRecordFor(domain = ddns, id = cloudFId, inZone=zoneid, type=d["type"], content=globalIP, ttl=120, proxied=d["proxied"])
                    except Exception as e:
                        print(e)


def getZoneFor(domain):
    if debug:
        print("\ngetZoneFor(" + domain + ")\n")
    # Get the zone id
    global baseUrl
    url = baseUrl
    url += "zones/"
    parameters = {'name':domain}
    zoneReq = requests.get(url= url, headers= header, params= parameters)

    if zoneReq.status_code == requests.codes.ok:
        # Determine if request was successfull
        response = json.loads(zoneReq.text)
        if response["success"] == True and len(response["result"]) > 0:
            zoneId = response["result"][0]["id"]
            if debug:
                print("Zone for " + domain + " is: " + zoneId)
            return zoneId
        else:
            if debug:
                print("Could not get zoneid")
            raise Exception("Could not get zoneid")

# Get the record id of the domain
def getIdFor(domain, inZone):
    if debug:
        print("\ngetIdFor(" + domain + ")")

    global baseUrl
    url = baseUrl
    url += 'zones/' + inZone + '/dns_records/'

    payload = {'type':'A', 'name':domain}

    s = requests.get(url, headers = header, params = payload )
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

                if debug:
                    print(cfIdentifier)
                return cfIdentifier, cfIp
            else:
                raise Exception("\nRecord for domain " + domain + " does not exist yet\n")
                # Means the record doesn't exist - need to create it
                #print("Creating dns record")
    else:
        raise Exception("Request failed")

def createRecordFor(domain, inZone, type, content, ttl, proxied):
    global baseUrl
    url = baseUrl
    url += 'zones/'+ inZone + '/dns_records/'
    if debug:
        print("\nCreating record for " + domain + "\n")

    create_dns_record_payload = json.dumps({'type':type, 'name':domain, 'content':content, 'proxied':proxied, 'ttl':ttl, 'priority':10})
    create_dns_record_req = requests.post(url, headers = header, data = create_dns_record_payload)

    response = json.loads(create_dns_record_req.text)
    if response["success"] == True:
        if debug:
            print("\nRecord for " + domain + " created successfully\n")
            print("Details:\n\n" + json.dumps(response["result"]))
    else: # Could not create dns record
        if debug:
            print("\n**Could not create dns record**\n")
            print(create_dns_record_req.url)
            print(create_dns_record_req.text)
        raise Exception("\nCould not create dns record for " + domain + " at: " + content + "\n")


def updateRecordFor(domain, id, type, content, ttl, proxied):
    global baseUrl
    url = baseUrl
    url += 'zones/'+ inZone + '/dns_records/' + id + '/'
    if debug:
        print("\nUpdate record " + domain + "with ip: " + ipaddr + "\n")

    update_payload = {'type':type, 'name':domain,'content':content, 'proxied':proxied}
    updateReq = requests.put(baseUrl, headers = header, params = update_payload)
    if updateReq.status_code == requests.codes.ok:
        # request was successfull
        response = json.loads(updateReq.text)
        if response["success"] == True:
            # Update was successfull
            if debug:
                print("\nUpdate on " + domain + "was successfull\n")
        else:
            if debug:
                print("\nUpdate on " + domain + "failed\n")
    else:
        raise Exception("\nRequest failed. Network may be down\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        printUsage()
        sys.exit(0)
    main()
    sys.exit(0)
