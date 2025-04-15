from flask import Flask, request, redirect, url_for, render_template, session, send_file, make_response
import boto3
from botocore.exceptions import NoCredentialsError
import secrets
from io import BytesIO
from PIL import Image, ImageOps
from contextlib import closing
import os
import hashlib
import logging


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

    # Setup
    bucket = session['BUCKET'] 
    thumbnail_bucket = session['BUCKET'] + "-thumbnail"
    auth_key = session['AUTH_KEY']
    access_key, secret_key = auth_key.split(':')
    width = min(int(request.args.get('w', '400')), 1000)


    # Initialize S3 client
    s3 = boto3.client('s3',
                         aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key)

    thumbnail_filename = hashlib.md5(f"{filename}-{width}".encode()).hexdigest()


    try:

      url = s3.generate_presigned_url('get_object',
               Params={'Bucket': thumbnail_bucket, 'Key': thumbnail_filename},
               ExpiresIn=3600)
      return redirect(url)

    except Exception as e:
      logging.error(f"Cache read error: {str(e)}")
      logging.error(f"source bucket : {bucket}")
      logging.error(f"source bucket key: {filename}")
      logging.error(f"Thumbnail bucket: {thumbnail_bucket}")
      logging.error(f"Thumbnail key: {thumbnail_filename}")

      try:
        # Load and open image from S3
        file_byte_string = s3.get_object(Bucket=bucket, Key=filename)[ "Body" ].read()
        img = Image.open(BytesIO(file_byte_string))
        img = ImageOps.exif_transpose(img)

        # Calculate new dimensions
        ratio = width / float(img.size[0])
        new_height = int(float(img.size[1]) * ratio)

        # Create thumbnail
        img.thumbnail((width, new_height), Image.Resampling.LANCZOS)

        # Dump and save image to S3
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True, progressive=True)
        buffer.seek(0)

        print(f"before bucket_key {filename} => thumbnail_filename: {thumbnail_filename}")
        response = make_response(send_file(
                   buffer,
                   mimetype='image/jpeg'
        ))
        print(f"after thumbnail_filename: {thumbnail_filename}")
        response.headers['Cache-Control'] = 'public, max-age=1, No-Store'
        return response

      except Exception as e:
          print(f"Error processing : {str(e)}")
          raise

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=8000)
