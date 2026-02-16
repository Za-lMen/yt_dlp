from flask import Flask, request, jsonify, send_file, redirect
import yt_dlp
import os
import tempfile
from pathlib import Path

app = Flask(__name__)

# תיקייה זמנית לקבצים
TEMP_DIR = tempfile.gettempdir()

@app.route('/')
def home():
    return '''
    <html dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>YouTube Downloader</title>
            <style>
                body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
                input { width: 100%; padding: 10px; margin: 10px 0; }
                button { padding: 10px 20px; background: #ff0000; color: white; border: none; cursor: pointer; }
                button:hover { background: #cc0000; }
            </style>
        </head>
        <body>
            <h1>YouTube Video Downloader</h1>
            <p>הכנס מזהה סרטון או URL מלא:</p>
            <input type="text" id="videoId" placeholder="dQw4w9WgXcQ או https://youtube.com/watch?v=...">
            <button onclick="download()">הורד סרטון</button>
            <div id="result"></div>
            
            <script>
                function download() {
                    const input = document.getElementById('videoId').value;
                    const videoId = input.includes('youtube.com') || input.includes('youtu.be') 
                        ? input 
                        : input;
                    
                    document.getElementById('result').innerHTML = 'מוריד...';
                    window.location.href = '/download?v=' + encodeURIComponent(videoId);
                }
            </script>
        </body>
    </html>
    '''

@app.route('/download')
def download_video():
    video_param = request.args.get('v', '')
    
    if not video_param:
        return jsonify({'error': 'חסר פרמטר video ID'}), 400
    
    # אם זה URL מלא, השתמש בו. אם לא, בנה URL
    if 'youtube.com' in video_param or 'youtu.be' in video_param:
        video_url = video_param
    else:
        video_url = f'https://www.youtube.com/watch?v={video_param}'
    
    try:
        # הגדרות להורדה
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        # הורדת הסרטון
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'video')
            
        # שליחת הקובץ למשתמש
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"{title}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # ניקוי קבצים זמניים (אופציונלי)
        try:
            if 'filename' in locals() and os.path.exists(filename):
                os.remove(filename)
        except:
            pass

@app.route('/info')
def video_info():
    """מחזיר מידע על הסרטון בלי להוריד"""
    video_param = request.args.get('v', '')
    
    if not video_param:
        return jsonify({'error': 'חסר פרמטר video ID'}), 400
    
    if 'youtube.com' in video_param or 'youtu.be' in video_param:
        video_url = video_param
    else:
        video_url = f'https://www.youtube.com/watch?v={video_param}'
    
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
        return jsonify({
            'title': info.get('title'),
            'duration': info.get('duration'),
            'views': info.get('view_count'),
            'author': info.get('uploader'),
            'thumbnail': info.get('thumbnail'),
            'download_url': f'/download?v={video_param}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
