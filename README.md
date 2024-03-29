brew install mongodb  
brew install rabbitmq

Setup:  
1. install mongodb, rabbitmq  
2. make video_audio db in mongodb  
3. make client_videos collection in the above db  
4. login to rabbitmq on localhost and make a queue video_queue
5.  go to gateway. activate venv. pip install. then run command - "flask run"
6.  go to processor. activate venv. pip install. then run command - "python3 server.py"
7. you can access on - "http://127.0.0.1:5000"
