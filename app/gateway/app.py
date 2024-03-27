# app.py
from flask import Flask, request, render_template, send_file, redirect, url_for
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


@app.route('/upload_video', methods=['POST'])
def upload_video():
    video_file = request.files['video']
    client_ip = request.remote_addr
    video_name = video_file.filename
    print(video_name)
    # Store video in GridFS
    video_id = fs.put(video_file)
    
    # Add task to RabbitMQ queue
    channel.basic_publish(exchange='', routing_key='video_queue', body=f'{str(video_id)},{client_ip}')

    # Add video to client_videos_collection
    client_videos_collection.update_one(
        {'client_ip': client_ip},
        {'$push': {'videos': {'video_id': str(video_id),'video_name': video_name, 'audio_id': None}}}, 
        upsert=True
    )
    
    return render_template('upload_success.html', client_audios=f'/client_audios')


@app.route('/download_audio/<audio_id>', methods=['GET'])
def download_audio(audio_id):
    print("in download audio")
    client_ip = request.remote_addr
    client_videos = client_videos_collection.find_one({"client_ip": client_ip})
    if client_videos:
        videos = client_videos.get('videos', [])
        for video in videos:
            if video.get('audio_id') == audio_id:
                audio_file = fs.get(ObjectId(audio_id))
                audio_data = audio_file.read()
                return send_file(io.BytesIO(audio_data), mimetype='audio/mp3', as_attachment=True, download_name=f'audio_{audio_id}.mp3')
    
    # If audio_id not found for the client, redirect to get_client_audios
    return redirect(url_for('get_client_audios'))


@app.route('/client_audios', methods=['GET'])
def get_client_audios():
    # Retrieve all audio records associated with the client's IP address
    client_ip = request.remote_addr
    client_videos = client_videos_collection.find_one({'client_ip': client_ip})
    audio_links = []
    if client_videos:
        videos = client_videos.get('videos', [])
        for video in videos:
            audio_id = video.get('audio_id')
            video_name = video.get('video_name')
            audio_links.append({
                'video_name': video_name,
                'audio_id': audio_id
            })
    audio_links.reverse()

    return render_template('client_audios.html', audio_links=audio_links)


@app.route('/')
def upload_form():
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0',port='5001')






    

























