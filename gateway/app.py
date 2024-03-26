# app.py
from flask import Flask, request, render_template, send_file
from flask_pymongo import PyMongo
from gridfs import GridFS, NoFile
import pika
import os
from bson import ObjectId
import moviepy.editor
import io

app = Flask(__name__)

# MongoDB setup
app.config["MONGO_URI"] = "mongodb://localhost:27017/video_audio"
mongo = PyMongo(app)
fs = GridFS(mongo.db)
# MongoDB collection to store IP-video associations
client_videos_collection = mongo.db.client_videos

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='video_queue', durable=True)
channel.queue_declare(queue='audio_queue', durable=True)


@app.route('/upload_video', methods=['POST'])
def upload_video():
    video_file = request.files['video']
    client_ip = request.remote_addr
    # Store video in GridFS
    video_id = fs.put(video_file)
    
    # Add task to RabbitMQ queue
    channel.basic_publish(exchange='', routing_key='video_queue', body=f'{str(video_id)},{client_ip}')
    
    return render_template('upload_success.html', audio_url=f'/download_audio')


@app.route('/download_audio', methods=['GET'])
def download_audio():
    client_ip = request.remote_addr
    client_video = client_videos_collection.find_one({"ip_address": client_ip})
    if client_video:
        video_id = client_video["video_id"]
        audio_file = fs.get(ObjectId(video_id))
        audio_data = audio_file.read()
        # Remove the record from client_videos_collection
        client_videos_collection.delete_one({'video_id': video_id})
        return send_file(io.BytesIO(audio_data), mimetype='audio/mp3', as_attachment=True, download_name='audio.mp3')
    else:
        return 'No audio available for download'


@app.route('/')
def upload_form():
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5001')






    

























