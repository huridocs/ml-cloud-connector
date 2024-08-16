curl -fsSL https://ollama.com/install.sh | sh
sudo service ollama stop
sudo OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve &
apt install python3-pip -y
apt install cron -y
apt install make -y
apt install python3.10-venv -y
apt install python3.11-venv -y
apt install python3.12-venv -y
pip install --upgrade pip
echo "'start_detached:
	sudo service ollama stop
	OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve &'" | sudo tee "/opt/Makefile" > /dev/null
chmod +x /opt/Makefile
gcloud auth login
gcloud compute firewall-rules create allow-ollama --allow tcp:11434 --target-tags=ollama-server
INSTANCE_NAME=$(curl http://metadata.google.internal/computeMetadata/v1/instance/hostname -H Metadata-Flavor:Google | cut -d . -f1)
ZONE=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | awk -F'/' '{print $NF}')
gcloud compute instances add-tags "$INSTANCE_NAME" --tags ollama-server --zone "$ZONE"
ollama pull aya:35b