# ml-cloud-connector

<h2>Setup the Server</h2>

```
git clone https://github.com/huridocs/ml-cloud-connector.git
cd ml-cloud-connector.git
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
    [ ] Install torch
        pip3 install torch --break-system-packages
        sudo apt install cron
        sudo apt install make
        git clone this repo
        crontab -e
        @reboot /path/to/your/script
    [ ] https://stackoverflow.com/questions/12973777/how-to-run-a-shell-script-at-startup


[ ] Check OVH security to avoid extra charges
    [ ] Use VPN ? 

