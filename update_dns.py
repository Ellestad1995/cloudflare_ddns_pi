#!/usr/local/bin/python3
import requests
import json

# Change apiKey, myDomain, emailAddress and ddns
apiKey = "xxxxxxxxxxxxxxxx"
myDomain = "example.com"
emailAddress = "mail@example.com"
ddns = "proxy.example.com" # subdomain to be updated

baseUrl = "https://api.cloudflare.com/client/v4/"
cfIp = "" # The ip cloudflare has for the ddns - this is updated by the script
header ={ "X-Auth-Email" : emailAddress, "X-Auth-Key" : apiKey, "Content-Type" : "application/json" }


# Get public ip address of network
r = requests.get('https://ipinfo.io/ip')
ip = (r.text).rstrip()
#print(ip)

# Get the zone id
baseUrl += "zones/"
parameters = {'name':myDomain}
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
        print("Could not get zoneid")
        exit(1);

# Get the record id of the domain

payload = {'type':'A', 'name':ddns}
baseUrl += "dns_records/"
s = requests.get(baseUrl, headers = header, params = payload )
if s.status_code == requests.codes.ok:
    #print(s.url)
    json_obj = json.loads(s.text)
    if json_obj["success"] == True:
        #print(json.dumps(json_obj, indent=4, sort_keys=True))
        # Check if result contains no data
        if len(json_obj["result"]) > 0:
            #print("Result length is above 0")
            cfIdentifier = json_obj["result"][0]["id"]
            cfIp = json_obj["result"][0]["content"]
            baseUrl += cfIdentifier
            #print(cfIdentifier)
        else:
            # Means the record doesn't exist - need to create it
            #print("Creating dns record")
            create_dns_record_payload = json.dumps({'type':'A', 'name':ddns, 'content':ip, 'proxied':False, 'ttl':120, 'priority':10})
            create_dns_record_req = requests.post(baseUrl, headers = header, data = create_dns_record_payload)
            if create_dns_record_req.ok == requests.codes.ok :
                # Successfully created domain
                print(create_dns_record_req.text)
                exit()
            else:
                # Could not create dns record
                print("Could not create dns record ")
                #print(create_dns_record_req.url)
                #print(create_dns_record_req.text)
                exit(1)
else:
    exit(1)


# Update record with new ip
# Only update if ip address is different
if cfIp == ip:
    print("Ip is the same. No need to update")
    exit()

print("Updating dns record")
update_payload = {'type':'A', 'name':ddns,'content':ip, 'proxied':True}
updateReq = requests.put(baseUrl, headers = header, params = update_payload)
if updateReq.status_code == requests.codes.ok:
    # request was successfull
    response = json.loads(updateReq.text)
    if response["success"] == True:
        # Update was successfull
        print("Update was successfull")
    else:
        print("Update failed")
else:
    print("Update request failed")
    exit(1)

exit()
