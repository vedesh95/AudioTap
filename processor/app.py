# Import necessary libraries
from flask import Flask, request, render_template
from gridfs import GridFS, NoFile
import pika
import os
from bson import ObjectId
import moviepy.editor
from flask_pymongo import PyMongo

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


# Define function to convert video to audio
def convert_video_to_audio(video_data, audio_path):
    # Write video data to a temporary file
    video_temp_path = '/tmp/temp_video.mp4'
    with open(video_temp_path, 'wb') as f:
        f.write(video_data)

    video_clip = moviepy.editor.VideoFileClip(video_temp_path)
    # Extract audio from the video clip
    audio_clip = video_clip.audio
    # Write the audio clip to the specified audio file
    audio_clip.write_audiofile(audio_path)
    # Close the video clip
    video_clip.close()
    print("Video converted to audio successfully!")
    # Remove temporary video file
    os.remove(video_temp_path)


# Define function to process video messages from the queue
def process_video(ch, method, properties, body):
    video_id, client_ip = body.decode().split(',')
    print(f"Processing video for IP: {client_ip}")
    try:
        # Retrieve video from GridFS using _id
        video_id_object = ObjectId(video_id)
        video_file = fs.get(video_id_object)
        data = video_file.read()

        # Convert video to audio and save to db
        audio_path = f'/tmp/{video_id}.mp3'
        convert_video_to_audio(data, audio_path)

        # Store the association between IP address and video ID in MongoDB
        client_videos_collection.insert_one({"ip_address": client_ip, "video_id": video_id})

        print("Audio file will be downloaded automatically")
    except Exception as e:
        print("Error processing video:", e)

    # Acknowledge message
    ch.basic_ack(delivery_tag=method.delivery_tag)


# Set up consumer to listen for messages from video_queue
channel.basic_consume(queue='video_queue', on_message_callback=process_video)


print("Waiting for messages. To exit press CTRL+C")
# Start consuming messages from the queue
channel.start_consuming()
