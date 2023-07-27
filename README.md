# serverless_remote_shell
## Warning:
No encryption is performed. Use at your own risk.
## description:
Imagine the situation:
You are providing tech support. You want to connect to client, but you're not going to explain steps to setup sshd. This serverless remote shell will help you.
## Installation (on your computer)
1. install python3
2. install pip
3. install aiohttp
```
python3 -m pip install aiohttp
```
4. clone this repo
```
git clone https://github.com/sudo-gera/serverless_remote_shell
```
## Connecting to your friend:
1. go to cloned directory:
```
cd serverless_remote_shell
```
2. start server on your computer:
```
python3 remote-server.py [port]
```
3. determine how to make http requests from your friend to you
- tips:
  - get your ip address from `ifconfig | grep inet | grep 192.168`
  - use ngrok or something similar if your friend is far from you
4. run on your friend's computer:
```
curl -s http://[your ip]:[port] | bash
```
5. server will print url. copy it.
5. on your computer in new terminal tab run command:
```
python3 remote.py [url from ]
```
