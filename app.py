from flask import Flask, request, redirect, url_for, render_template, session, send_file, make_response
import boto3
from botocore.exceptions import NoCredentialsError
import secrets
from io import BytesIO
from PIL import Image, ImageOps
from contextlib import closing
import os
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

    # Validate input
    if '../' in filename or not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        abort(400)

    # Setup
    bucket = session['BUCKET']
    auth_key = session['AUTH_KEY']
    access_key, secret_key = auth_key.split(':')
    width = min(int(request.args.get('w', '400')), 1000)

    try:
        with closing(boto3.client('s3', 
                     aws_access_key_id=access_key,
                     aws_secret_access_key=secret_key)) as s3:
            
            # Get image
            response = s3.get_object(Bucket=bucket, Key=filename)
            if response['ContentLength'] > 10_000_000:  # 10MB limit
                return redirect(url_for('view', filename=filename))
            
            try:
                # Process image
                img = Image.open(BytesIO(response['Body'].read()))
                img = ImageOps.exif_transpose(img)
                
                # Resize
                ratio = width / float(img.size[0])
                new_height = int(float(img.size[1]) * ratio)
                img.thumbnail((width, new_height), Image.Resampling.LANCZOS)
                
                # Save to cache
                with BytesIO() as output:
                    img.save(output, format='JPEG', quality=85, optimize=True, progressive=True)
                    output.seek(0)
                    
                    response = make_response(send_file(output, mimetype='image/jpeg'))
                    response.headers['Cache-Control'] = 'public, max-age=31536000'
                    return response
                    
            finally:
                if 'img' in locals():
                    img.close()
                    
    except Exception as e:
        print(f"Thumbnail generation failed: {str(e)}")
        #logging.error(f"Thumbnail error: {str(e)}")
        # Fallback to original image
        s3 = boto3.client('s3',
                         aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key)
        url = s3.generate_presigned_url('get_object',
                                      Params={'Bucket': bucket, 'Key': filename},
                                      ExpiresIn=3600)
        return redirect(url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
