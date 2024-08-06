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

python3 src/ml_cloud_connector/create_post_start_script.py
```

<h2>To do</h2>

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
        [ ] Catch error ovh.exceptions.ResourceConflictError on start or stop
[ ] Check OVH security to avoid extra charges
        [ ] Use VPN ? 


<h2>Stop automatic shutdown</h2>

ps aux  |  grep automatic_shutdown  |  awk '{print $2}'  |  xargs sudo kill -9