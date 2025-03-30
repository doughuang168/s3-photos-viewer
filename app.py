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
from apscheduler.schedulers.background import BackgroundScheduler

def prune_cache(max_size_mb=1024):
    """Keep cache under specified size"""
    cache_dir = "/app/thumbnail_cache"
    if not os.path.exists(cache_dir):
        return

    files = []
    for f in os.listdir(cache_dir):
        path = os.path.join(cache_dir, f)
        if os.path.isfile(path):
            files.append((path, os.path.getmtime(path)))

    # Sort by oldest first
    files.sort(key=lambda x: x[1])

    total_size = sum(os.path.getsize(f[0]) for f in files)
    max_size = max_size_mb * 1024 * 1024

    while total_size > max_size and files:
        oldest = files.pop(0)
        os.remove(oldest[0])
        total_size -= os.path.getsize(oldest[0])

scheduler = BackgroundScheduler()
scheduler.add_job(prune_cache, 'interval', hours=1)
scheduler.start()


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

    # Validate input
    if '../' in filename or not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        abort(400)

    # Setup
    bucket = session['BUCKET']
    auth_key = session['AUTH_KEY']
    access_key, secret_key = auth_key.split(':')
    width = min(int(request.args.get('w', '400')), 1000)

    # Create cache directory if not exists
    cache_dir = "/app/thumbnail_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create cache key
    cache_key = hashlib.md5(f"{filename}-{width}".encode()).hexdigest()
    cache_path = os.path.join(cache_dir, f"{cache_key}.jpg")

    # Try serving from cache first
    if os.path.exists(cache_path):
        try:
            # Create response with proper caching headers
            response = send_file(
                cache_path,
                mimetype='image/jpeg'
            )
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            return response
        except Exception as e:
            logging.error(f"Cache read error: {str(e)}")
            # Fall through to regeneration

    try:
        # Initialize S3 client
        s3 = boto3.client('s3',
                         aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key)

        # Get original image
        response = s3.get_object(Bucket=bucket, Key=filename)
        if response['ContentLength'] > 10_000_000:  # 10MB limit
            return redirect(url_for('view', filename=filename))

        # Process image
        with BytesIO(response['Body'].read()) as original_buffer:
            with Image.open(original_buffer) as img:
                img = ImageOps.exif_transpose(img)
                
                # Calculate new dimensions
                ratio = width / float(img.size[0])
                new_height = int(float(img.size[1]) * ratio)
                
                # Create thumbnail
                img.thumbnail((width, new_height), Image.Resampling.LANCZOS)
                
                # Save to temporary buffer
                with BytesIO() as output_buffer:
                    img.save(output_buffer, format='JPEG', quality=85, optimize=True, progressive=True)
                    output_buffer.seek(0)
                    
                    # Write to cache (atomic write pattern)
                    temp_cache_path = f"{cache_path}.tmp"
                    try:
                        with open(temp_cache_path, 'wb') as f:
                            f.write(output_buffer.getvalue())
                        os.rename(temp_cache_path, cache_path)  # Atomic operation
                    except Exception as e:
                        logging.error(f"Cache write failed: {str(e)}")
                        if os.path.exists(temp_cache_path):
                            os.remove(temp_cache_path)
                    
                    # Return the image with caching headers
                    output_buffer.seek(0)
                    response = make_response(send_file(
                        output_buffer,
                        mimetype='image/jpeg'
                    ))
                    response.headers['Cache-Control'] = 'public, max-age=31536000'
                    return response

    except Exception as e:
        logging.error(f"Thumbnail generation failed: {str(e)}")
        # Fallback to original image
        try:
            s3 = boto3.client('s3',
                             aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key)
            url = s3.generate_presigned_url('get_object',
                                          Params={'Bucket': bucket, 'Key': filename},
                                          ExpiresIn=3600)
            return redirect(url)
        except Exception as e:
            logging.error(f"Fallback failed: {str(e)}")
            abort(500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
