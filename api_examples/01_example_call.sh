
# Full documentation here:
# https://support.quobyte.com/docs/16/latest/api_new.html

# do a simple "get_configuration"
curl -s -u user:password http://my.quobyte.api-server.com:7860 -d @getSystemConfig.json	 | jq .

# get device overview
curl -s -u user:password http://my.quobyte.api-server.com:7860 -d @getDeviceList.json | jq .result.device_list.devices[]

# get quota (the first quota set in an unstructured data pool)
curl -s -u user:password http://my.quobyte.api-server.com:7860 -d @getQuota.json | jq .result.quotas[0]

# get volume names
curl -s -u user:passowrd http://my.quobyte.api-server.com:7860 -d @getVolume.json | jq .result.volume[].name
