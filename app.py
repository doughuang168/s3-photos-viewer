import os
import boto3
from flask import Flask, render_template_string, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Parse environment variables
bucket_name = os.getenv('BUCKET')
auth_key = os.getenv('AUTH_KEY')

if not bucket_name or not auth_key:
    raise ValueError("Missing required environment variables")

aws_access_key_id, aws_secret_access_key = auth_key.split(':', 1)

# Initialize S3 client with automatic region detection
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
)

# Get bucket region to ensure valid presigned URLs
try:
    bucket_region = s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
    # US East (N. Virginia) returns None
    if bucket_region is None:
        bucket_region = 'us-east-1'
except Exception as e:
    raise RuntimeError(f"Error getting bucket region: {str(e)}")

# Recreate S3 client with correct region
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=bucket_region
)


def list_objects(prefix=''):
    paginator = s3.get_paginator('list_objects_v2')
    results = []
    folders = set()

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        if 'CommonPrefixes' in page:
            for folder in page['CommonPrefixes']:
                folders.add(folder['Prefix'])

        if 'Contents' in page:
            for obj in page['Contents']:
                if obj['Key'] != prefix and not obj['Key'].endswith('/'):
                    results.append(obj['Key'])

    return sorted(folders) + sorted(results)

@app.route('/')
@app.route('/<path:subpath>')
def index(subpath=''):
    current_path = subpath.rstrip('/')
    prefix = f"{current_path}/" if current_path else ''

    objects = list_objects(prefix)

    items = []
    for obj in objects:
        if obj.endswith('/'):
            clean_path = obj.rstrip('/')
            display_name = clean_path.split('/')[-1] + '/'
            items.append(('folder', display_name, clean_path))
        else:
            file_name = obj.split('/')[-1]
            items.append(('file', file_name, obj))

    breadcrumbs = [{'name': 'Home', 'path': ''}]
    if current_path:
        parts = current_path.split('/')
        for i in range(len(parts)):
            breadcrumbs.append({
                'name': parts[i],
                'path': '/'.join(parts[:i+1])
            })
    return render_template_string(r'''
<!DOCTYPE html>
<html>
<head>
    <title>S3 Browser - {{ bucket_name }}</title>
    <style>
        
        body { font-family: Arial, sans-serif; margin: 20px; }
        .item { padding: 5px; }
        .folder { color: blue; cursor: pointer; }
        .file { color: #666; }
        .breadcrumb { margin-bottom: 20px; }
        .breadcrumb a { text-decoration: none; color: #333; }
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.9);
        }
        .modal-content {
            margin: auto;
            display: block;
            width: 80%;
            max-width: 700px;
            margin-top: 50px;
        }
    </style>
</head>
<body>
    
    <div class="breadcrumb">
        {% for crumb in breadcrumbs %}
            <a href="/{{ crumb.path }}">{{ crumb.name }}</a>
            {% if not loop.last %} &gt; {% endif %}
        {% endfor %}
    </div>

    <h2>{{ current_path if current_path else bucket_name }}</h2>
    
    {% for type, name, full_path in items %}
        <div class="item">
            {% if type == 'folder' %}
                <span class="folder" onclick="window.location.href='/{{ full_path }}'">
                    &#128193; {{ name }}
                </span>
            {% else %}
                <span class="file" onclick='previewImage({{ full_path | tojson | safe }})'>
                    &#128196; {{ name }}
                </span>
            {% endif %}

        </div>
    {% endfor %}


    <div id="imageModal" class="modal">
        <span onclick="document.getElementById('imageModal').style.display='none'"
              style="color: white; position: absolute; right: 20px; top: 10px;
                    font-size: 35px; cursor: pointer;">&times;</span>
        <img class="modal-content" id="modalImage" style="transition: transform 0.2s ease;">
        <button id="rotateButton"
                style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                       background-color: white; border: none; padding: 10px; cursor: pointer;">
            Rotate
        </button>
    </div>


    <script>
        let rotationAngle = 0; // Global variable to track rotation angle

        function previewImage(key) {
            if (!key || key.trim() === '') {
               console.error('Invalid key passed to previewImage:', key);
               alert('No valid key to preview.');
               return;
            }
            console.log('Attempting to preview:', key); 
            const imageExtensions = /\.(jpe?g|png|gif|webp)$/i;
            
            if (imageExtensions.test(key)) {
                const url = `/presigned-url?key=${encodeURIComponent(key)}`; 
                fetch(url)
                    .then(response => {
                        if (!response.ok) throw new Error('Network error');
                        return response.text();
                    })
                    .then(url => {
                        if (!url) throw new Error("Empty URL response from server");
                        document.getElementById('modalImage').src = url;
                        document.getElementById('imageModal').style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Preview failed:', error);
                        alert('Failed to preview the image. Please try again.');
                    });
            } else {
                 console.error('Invalid file type for preview:', key);
            }
        }

        // Attach rotation functionality
        document.getElementById('rotateButton').onclick = function() {
            rotationAngle = (rotationAngle + 90) % 360; // Increment angle by 90 degrees
            const modalImage = document.getElementById('modalImage');
            modalImage.style.transform = `rotate(${rotationAngle}deg)`; // Apply rotation
        };

        window.onclick = function(event) {
            if (event.target.className === 'modal') {
                event.target.style.display = 'none';
            }
        }
        
        //window.onerror = function(message, source, lineno, colno, error) {
        //  console.error('Global error:', message, source, lineno, colno, error);
        //};

    </script>
</body>
</html>
''', bucket_name=bucket_name, items=items, breadcrumbs=breadcrumbs, current_path=current_path)

@app.route('/presigned-url')
def presigned_url():
    key = request.args.get('key')
    if not key:
        print("Error: Missing key")
        return "Error: Missing key", 400
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=3600
        )
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return "Error generating URL", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
