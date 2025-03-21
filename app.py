from flask import Flask, request, redirect, url_for, render_template, session
import boto3
from botocore.exceptions import NoCredentialsError
import secrets


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
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': filename}, ExpiresIn=3600)
        return redirect(url)
    except NoCredentialsError:
        return "Invalid credentials", 401
    except Exception as e:
        return str(e), 500

# Lambda handler
#def handler(event, context):
#       return response(app, event, context)
