#!/usr/local/bin/python3
import requests
import json
import sys
import os
##########################################
# Debug setting
##########################################
debug = True # Enable debugging to print data
##########################################

##########################################
# Github access token
# Set the variables here or set them as environmental variables and they will be read in later 
##########################################
GHPersonalAccessToken = ""
GHDNSRecordsGistUrl = ""
GHAuthHeader = {'Authorization': 'token ' + GHPersonalAccessToken}
##########################################

##########################################
# Cloudflare API token
# Set the variables here or set them as environmental variables and they will be read in later
##########################################
CFAPIToken = ""
CFAuthHeader ={"Authorization" : "Bearer " + CFAPIToken, "Content-Type" : "application/json" }
CFAPIBaseEndpointUrl = "https://api.cloudflare.com/client/v4/"
##########################################

##########################################
# Global variables
##########################################
dnsRecords = None # Should be a json object later on
getGlobalIpUrl = 'https://ipinfo.io/ip'


def checkPrerequisites():
    global GHPersonalAccessToken
    global GHDNSRecordsGistUrl
    global CFAPIToken
    global CFEmailAddress
    didFaile = False
    if GHPersonalAccessToken == '':
        if os.environ.get('GHPERSONALACCESSTOKEN') is not None:
            GHPersonalAccessToken = os.environ['GHPERSONALACCESSTOKEN']
        else:
            if debug:
                print("Missing 'GHPERSONALACCESSTOKEN' environmental variable")
            didFaile = True

    if GHDNSRecordsGistUrl == '':
       if os.environ.get('GHDNSRECORDSGISTURL') is not None:
            GHDNSRecordsGistUrl = os.environ['GHDNSRECORDSGISTURL']
        else:
            if debug:
                print("Missing 'GHDNSRECORDSGISTURL' environmental variable")
            didFaile = True

    if CFAPIToken == '':
        if os.environ.get('CFAPITOKEN') is not None:
            CFAPIToken = os.environ.get('CFAPITOKEN')
        else:
            if debug:
                print("Missing 'CFAPITOKEN' environmental variable")
            didFaile = True

    if didFaile:
        return False
    else:
        return True
    

"""
getDnsRecordsGist

Get the gist stored on github.

"""
def getDnsRecordsGist():
    global dnsRecords
    r = requests.get(GHDNSRecordsGistUrl, headers=GHAuthHeader)
    if r.status_code == requests.codes.ok:
        dnsRecords = json.loads(r.content)
        if debug:
            print(json.dumps(dnsRecords, indent=2))
        return True
    else:
        if debug:
            print('Could not get connection to ' + GHDNSRecordsGistUrl)
            print(r.status_code)
            print(r.text)
    return False


"""
getGlobalIp

Get global address for network
"""
def getGlobalIp():
    r = requests.get(getGlobalIpUrl)
    if r.status_code == requests.codes.ok:
        ip = (r.text).rstrip()
        if(debug):
            print(ip)
        return ip
    else:
        if(debug):
            print('Could not get public ip address')
            print(r.status_code)
            print(r.text)
    return ''

def main():
    global dnsRecords
    global CFAPIBaseEndpointUrl

    globalIP = getGlobalIp()
    if(globalIP == ''):
        print('Abort: Public ip could not be retrieved')
        sys.exit(1)

    if(getDnsRecordsGist() is not True):
        if(debug):
            print('Abort: DNS records file could not be retrieved')
        sys.exit(1)

    dnsrec = dnsRecords['dns_records']
    
    for domain in dnsrec:

        
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

        # Loop over all the subdomains
        for record in domain["records"]:
            record_name = record["name"]

            if debug:
                print("Working on " + record_name)

            CF_Record_Id = "" # Cloudflare Record Id - The id retrieved from Cloudflare
            CF_Record_IpAddr = "" # Cloudflare Record ip address - The ip address Cloudflare currently has

            try:
                CF_Record_Id, CF_Record_IpAddr = getIdFor(domain=record_name, inZone=zoneid)
            except Exception as e:
                if debug:
                    print(e)

            if CF_Record_Id == "" and CF_Record_IpAddr == "":
                # Creating new record since the record doesn't exists yet. Happens if we specify a new subdomain/record in the gist
                try:
                    createRecordFor(domain = record_name, inZone=zoneid, type=record["type"], content=globalIP, ttl=120, proxied=record["proxied"])
                except Exception as e:
                    print(e)
            else:
                # Already exist update the existing
                if CF_Record_IpAddr == globalIP:
                    # No need to update if ip isn't changed
                    if debug:
                        print("global ip addr didn't change for " + record_name + ". Dont update")
                else:
                    try:
                        updateRecordFor(domain = record_name, id = CF_Record_Id, inZone=zoneid, type=record["type"], content=globalIP, ttl=120, proxied=record["proxied"])
                    except Exception as e:
                        print(e)

"""
getZoneFor(domain)

Get the zone for a given domain name.
"""
def getZoneFor(domain):
    if debug:
        print("\ngetZoneFor(" + domain + ")\n")
    # Get the zone id
    global CFAPIBaseEndpointUrl
    listZoncesUrl = CFAPIBaseEndpointUrl
    listZoncesUrl += "zones/"
    parameters = {'name':domain}
    zoneReq = requests.get(url= listZoncesUrl, headers= CFAuthHeader, params= parameters)

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
                print(json.dumps(response, indent=2))
            raise Exception("Could not get zoneid")
    else:
        if debug:
            print("Could not get zone for " + domain)
            print(zoneReq.text)
            raise Exception("Could not get zoneid")

# Get the record id of the domain
def getIdFor(domain, inZone):
    if debug:
        print("\ngetIdFor(" + domain + ")")

    global CFAPIBaseEndpointUrl
    url = CFAPIBaseEndpointUrl
    url += 'zones/' + inZone + '/dns_records/'

    payload = {'type':'A', 'name':domain}

    s = requests.get(url, headers = CFAuthHeader, params = payload )
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
    global CFAPIBaseEndpointUrl
    url = CFAPIBaseEndpointUrl
    url += 'zones/'+ inZone + '/dns_records/'
    if debug:
        print("\nCreating record for " + domain + "\n")

    create_dns_record_payload = json.dumps({'type':type, 'name':domain, 'content':content, 'proxied':proxied, 'ttl':ttl, 'priority':10})
    create_dns_record_req = requests.post(url, headers = CFAuthHeader, data = create_dns_record_payload)

    response = json.loads(create_dns_record_req.text)
    if response["success"] == True:
        if debug:
            print("\nRecord for " + domain + " created successfully\n")
            print("Details:\n\n" + json.dumps(response["result"], indent=2))
    else: # Could not create dns record
        if debug:
            print("\n**Could not create dns record**\n")
            print(create_dns_record_req.url)
            print(create_dns_record_req.text)
        raise Exception("\nCould not create dns record for " + domain + " at: " + content + "\n")


def updateRecordFor(domain, id, inZone, type, content, ttl, proxied):
    global CFAPIBaseEndpointUrl
    url = CFAPIBaseEndpointUrl
    url += 'zones/'+ inZone + '/dns_records/' + id + '/'
    if debug:
        print("\nUpdate record " + domain + "with ip: " + content + "\n")

    update_payload = {'type':type, 'name':domain,'content':content, 'proxied':proxied}
    updateReq = requests.put(CFAPIBaseEndpointUrl, headers = CFAuthHeader, params = update_payload)
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
    if not checkPrerequisites():
        sys.exit(1)
    main()
    sys.exit(0)
