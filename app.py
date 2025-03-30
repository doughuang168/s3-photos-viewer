from flask import Flask, request, redirect, url_for, render_template, session, send_file, make_response
import boto3
from botocore.exceptions import NoCredentialsError
import secrets
from io import BytesIO
from PIL import Image, ImageOps
from contextlib import closing
import os
import hashlib
#import logging


app = Flask(__name__)
app.secret_key = secrets.token_hex(24) 


# Landing page route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Store the BUCKET and AUTH_KEY in the session
        session['BUCKET'] = request.form['bucket']
        session['AUTH_KEY'] = request.form['auth_key']
        return redirect(url_for('index'))
    return render_template('login.html')

# Main route to list S3 content
@app.route('/index')
@app.route('/index/<path:prefix>')
def index(prefix=''):
    # Check if BUCKET and AUTH_KEY are in the session
    if 'BUCKET' not in session or 'AUTH_KEY' not in session:
        return redirect(url_for('login'))

    bucket = session['BUCKET']
    auth_key = session['AUTH_KEY']
    access_key, secret_key = auth_key.split(':')

    # Initialize the S3 client
    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    try:
        # List objects and folders (prefixes) in the bucket
        response = s3.list_objects_v2(Bucket=bucket, Delimiter='/', Prefix=prefix)

        # Extract folders (common prefixes)
        folders = []
        if 'CommonPrefixes' in response:
            folders = [prefix['Prefix'] for prefix in response['CommonPrefixes']]

        # Extract files
        files = []
        if 'Contents' in response:
            files = [obj['Key'] for obj in response['Contents'] if not obj['Key'].endswith('/')]

    except NoCredentialsError:
        return "Invalid credentials", 401
    except Exception as e:
        return str(e), 500

    return render_template('index.html', bucket=bucket, prefix=prefix, folders=folders, files=files)

# Route to view an image
@app.route('/view/<path:filename>')
def view(filename):
    if 'BUCKET' not in session or 'AUTH_KEY' not in session:
        return redirect(url_for('login'))

    bucket = session['BUCKET']
    auth_key = session['AUTH_KEY']
    access_key, secret_key = auth_key.split(':')

    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    try:
        url = s3.generate_presigned_url('get_object', 
                                      Params={'Bucket': bucket, 'Key': filename}, 
                                      ExpiresIn=3600)
        return redirect(url)
    except NoCredentialsError:
        return "Invalid credentials", 401
    except Exception as e:
        return str(e), 500


@app.route('/thumbnail/<path:filename>')
def thumbnail(filename):
    if 'BUCKET' not in session or 'AUTH_KEY' not in session:
        return redirect(url_for('login'))


    bucket = session['BUCKET']
    auth_key = session['AUTH_KEY']
    access_key, secret_key = auth_key.split(':')

    width = request.args.get('w', default='400')
    try:
        width = min(int(width), 1000)
    except ValueError:
        width = 400

    # Create cache key
    cache_key = hashlib.md5(f"{filename}-{width}".encode()).hexdigest()
    cache_dir = "/app/thumbnail_cache"  # Mount this volume in Docker

    # Check cache
    cache_path = os.path.join(cache_dir, f"{cache_key}.jpg")
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return send_file(f, mimetype='image/jpeg')

    s3 = boto3.client('s3',
                     aws_access_key_id=access_key,
                     aws_secret_access_key=secret_key)

    try:
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            url = s3.generate_presigned_url('get_object',
                                          Params={'Bucket': bucket, 'Key': filename},
                                          ExpiresIn=3600)
            return redirect(url)

        # Get image and handle orientation
        response = s3.get_object(Bucket=bucket, Key=filename)
        img = Image.open(BytesIO(response['Body'].read()))

        # Fix orientation
        img = ImageOps.exif_transpose(img)

        # Resize maintaining aspect ratio
        original_width, original_height = img.size
        ratio = width / float(original_width)
        new_height = int(float(original_height) * ratio)

        img.thumbnail((width, new_height), Image.Resampling.LANCZOS)

        # Save as progressive JPEG
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85, optimize=True, progressive=True)
        img_byte_arr.seek(0)

        # Save to cache
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(img_byte_arr.getvalue())

        #return send_file(img_byte_arr, mimetype='image/jpeg')
        response = send_file(img_byte_arr, mimetype='image/jpeg')
        response.headers['Cache-Control'] = 'public, max-age=31536000'
        return response

    except Exception as e:
        print(f"Thumbnail generation failed: {str(e)}")
        url = s3.generate_presigned_url('get_object',
                                      Params={'Bucket': bucket, 'Key': filename},
                                      ExpiresIn=3600)
        return redirect(url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
