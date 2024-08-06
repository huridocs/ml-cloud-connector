# ml-cloud-connector

<h2>Setup the Server</h2>

```
git clone https://github.com/huridocs/ml-cloud-connector.git
cd ml-cloud-connector
chmod +x setup.sh
sudo ./setup.sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```



[x] Start instance if it is paused
[x] Shutdown instance when not used
    [x] Add a script to stop instance
[x] Check if instance is accessible for endpoints
[ ] Check if post start script works
[x] Use connector in translation service
    [x] Cache ip to avoid extra time
    [x] Default to localhost when no variables
    [x] Get ip should start server if stopped
    [ ] Write tests
[ ] Check OVH security to avoid extra charges
    [ ] Use VPN ? 

