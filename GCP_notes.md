```
pip install google-cloud-compute
```
PROJECT_ID can be found in https://console.cloud.google.com/  

While creating the instance:

Under GPU tab,
- Click "Change"
- In the "Operating System" dropdown, select "Deep Learning on Linux"  
  (Python 3.10 - cuda 12.1)

Under Firewall tab, allow HTTP/HTTPS traffic if we want to access web services from the instance.

To see the instance id, click on instance name.


Starting the instance finished in 21.4 seconds  
Stopping the instance finished in 5.92 seconds

Getting instance info finished in 0.41 seconds

Check:

```
nvidia-smi
```


---

If we came across "Pending kernel upgrade", to disable it:

vim /etc/needrestart/needrestart.conf
then uncomment this line

#$nrconf{kernelhints} = -1;

Or just replace them in one line:

sed -i "s/#\$nrconf{kernelhints} = -1;/\$nrconf{kernelhints} = -1;/g" /etc/needrestart/needrestart.conf

---

<h2> Spin up ollama </h2>


- SSH into the instance:
```
  gcloud compute ssh --zone "zone" "instance_name" --project "project_id"
```

- Update the system: 
```
   sudo apt update && sudo apt upgrade -y
```

<h3>Install ollama</h3>

```
 curl -fsSL https://ollama.com/install.sh | sh
```

```
ollama serve
```

```
ollama pull tinyllama
```


<h3>Installing with Docker:</h3>

```
  sudo apt-get install docker.io
```
```
  sudo docker run -d -v
  ollamaModels:/root/.ollama -p 11434:11434
  --name ollama ollama/ollama
```



Test ollama
```
ollama serve
ollama pull tinyllama
```

```
curl -X POST http://localhost:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "tinyllama",
  "prompt": "Hello",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": 10
  }
}'
```


<h3>Test ollama from outside</h3>

Create a firewall rule to allow 11434:
```
gcloud compute firewall-rules create allow-ollama --allow tcp:11434 --target-tags=ollama-server
```


To add this firewall rule to the instance:
- From web:
  - At the top of instance details page, click "Edit"
  - Click in the "Network tags" field and type "ollama-server"
  - Scroll to the bottom and "Save"

- From CLI
```
gcloud compute instances add-tags [instance_name] --tags ollama-server --zone [zone]
```

- To delete the rule:
```
gcloud compute firewall-rules delete allow-ollama
```

This should be enough but if it's not:

- SSH to the instance
```
vim .bashrc
```
```
export OLLAMA_HOST=0.0.0.0:11434
```
```
source .bashrc
```
```
sudo service ollama stop
ollama serve
```


```
curl -X POST http://<external_ip>:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "tinyllama",
  "prompt": "Hello",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": 10
  }
}'
```

```
time curl -X POST http://34.32.208.131:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "aya:35b",
  "prompt": "Please translate the following text into French. Follow these guidelines: \n1. Maintain the original layout and formatting.\n2. Translate all text accurately without omitting any part of the content.\n3. Preserve the tone and style of the original text.\n4. Do not include any additional comments, notes, or explanations in the output; provide only the translated text.\n\nHere is the text to be translated:\n\nHello, how are you?",
  "stream": false
}'
```
time for above command:  
real	0m4,261s  
user	0m0,007s  
sys 	0m0,006s  
i have run this several times and the time is generally around ~4.2-4.3s

```
time curl -X POST http://34.32.208.131:11434/api/generate -H "Content-Type: application/json" -d '{
  "model": "aya:35b",
  "prompt": "Please translate the following text into French. Follow these guidelines: \n1. Maintain the original layout and formatting.\n2. Translate all text accurately without omitting any part of the content.\n3. Preserve the tone and style of the original text.\n4. Do not include any additional comments, notes, or explanations in the output; provide only the translated text.\n\nHere is the text to be translated:\n\nWhen all the processes are done, the service returns a list of SegmentBox elements with some determined order. To figure out this order, we are mostly relying on Poppler. In addition to this, we are also getting help from the types of the segments.\n\nDuring the PDF to XML conversion, Poppler determines an initial reading order for each token it creates. These tokens are typically lines of text, but it depends on Popplers heuristics. When we extract a segment, it usually consists of multiple tokens. Therefore, for each segment on the page, we calculate an average reading order by averaging the reading orders of the tokens within that segment. We then sort the segments based on this average reading order. However, this process is not solely dependent on Poppler, we also consider the types of segments. First, we place the header segments at the beginning and sort them among themselves. Next, we sort the remaining segments, excluding footers and footnotes, which are positioned at the end of the output. Occasionally, we encounter segments like pictures that might not contain text. Since Poppler cannot assign a reading order to these non-text segments, we process them after sorting all segments with content. To determine their reading order, we rely on the reading order of the nearest non-empty segment, using distance as a criterion.",
  "stream": false
}'
```
time for above command:
real	2m25,564s
user	0m0,006s
sys	0m0,006s

the first time when i run the above command from terminal, it did not give an answer and after some time it unload the model from gpu  
when i run it from code, i get the answer in:
Response finished in 147.76 seconds

There is a value in ollama to unload the model if it's not in use. This value is OLLAMA_KEEP_ALIVE and as default it's set to "5m".  
Every time we use the model, this time resets to 5 minutes.

To change ollama's model unload time:
```
vim .bashrc
```
```
export OLLAMA_KEEP_ALIVE="10m"
```
```
source .bashrc
```
```
sudo service ollama stop
ollama serve
```






- When I try to start the instance that is already stopping (status becomes STOPPING), it continued stopping and gave no error.  
Also it did not start after termination.

- When I try to stop the instance when it is in STAGING status, it continued starting and gave no error.
Also it did not stop after starting.

- When I try to get a translation when the server is shutting down (when status is STOPPING), I was able to get the answers for some time.
  Then, it starts to give RemoteProtocolError. Both happens when the status is STOPPING.

- For no GPU available problem, I saw that people recommend using reservations: https://console.cloud.google.com/compute/reservations
  What I understand is, you have to pay for it even if the instance is not in use (So you have to pay for like it's running 24/7).

- After starting the instance, we might need to stop ollama and restart it again. There might be a problem related to the connection refused.
