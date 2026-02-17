from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import tempfile
import base64

app = Flask(__name__)

TEMP_DIR = tempfile.gettempdir()

@app.route('/')
def home():
    return '''
    <html dir="rtl">
        <head>
            <meta charset="utf-8">
            <title>YouTube Downloader</title>
            <style>
                body { 
                    font-family: Arial; 
                    max-width: 600px; 
                    margin: 50px auto; 
                    padding: 20px;
                    background: #f5f5f5;
                }
                h1 { color: #333; }
                input, textarea { 
                    width: 100%; 
                    padding: 10px; 
                    margin: 10px 0;
                    box-sizing: border-box;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                textarea {
                    height: 100px;
                    font-family: monospace;
                    font-size: 12px;
                }
                button { 
                    padding: 10px 20px; 
                    background: #ff0000; 
                    color: white; 
                    border: none; 
                    cursor: pointer;
                    width: 100%;
                    border-radius: 4px;
                    font-size: 16px;
                }
                button:hover { background: #cc0000; }
                .info {
                    background: #fff3cd;
                    padding: 10px;
                    border-radius: 4px;
                    margin-top: 20px;
                    font-size: 12px;
                    border-left: 4px solid #ffc107;
                }
                .section {
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }
                #result {
                    margin-top: 20px;
                    padding: 10px;
                    background: white;
                    border-radius: 4px;
                }
                .success { color: green; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <h1>🎥 YouTube Video Downloader</h1>
            
            <div>
                <h2>הורדה ישירה</h2>
                <p>הכנס מזהה סרטון או URL מלא:</p>
                <input type="text" id="videoId" placeholder="dQw4w9WgXcQ או https://youtube.com/watch?v=...">
                
                <p>אם רוצה להשתמש בקוקיס (אופציונלי):</p>
                <textarea id="cookies" placeholder="הדבק כאן את תוכן cookies.txt (אם יש)"></textarea>
                
                <button onclick="download()">⬇️ הורד סרטון</button>
                <div id="result"></div>
            </div>
            
            <div class="section">
                <h2>API</h2>
                <p>לשימוש מ-GAS או applications אחרות:</p>
                <code style="background: #f0f0f0; padding: 10px; display: block; border-radius: 4px; overflow-x: auto;">
POST /api/download<br>
Content-Type: application/json<br><br>
{<br>
&nbsp;&nbsp;"video_url": "https://youtube.com/watch?v=...",<br>
&nbsp;&nbsp;"cookies": "# Netscape HTTP Cookie File..."<br>
}
                </code>
            </div>
            
            <div class="info">
                <strong>📋 איך להשיג cookies:</strong><br>
                1. התקן את ההרחבה "Get cookies.txt LOCALLY" מ-Chrome Web Store<br>
                2. כנס ל-YouTube.com עם החשבון שלך<br>
                3. לחץ על ההרחבה וצור Export<br>
                4. הדבק את תוכן הקובץ בשדה למעלה
            </div>
            
            <script>
                function download() {
                    const input = document.getElementById('videoId').value.trim();
                    const cookies = document.getElementById('cookies').value.trim();
                    
                    if (!input) {
                        document.getElementById('result').innerHTML = '<p class="error">❌ אנא הכנס URL או מזהה</p>';
                        return;
                    }
                    
                    document.getElementById('result').innerHTML = '<p class="success">⏳ מוריד...</p>';
                    
                    const params = new URLSearchParams();
                    params.append('v', input);
                    if (cookies) {
                        params.append('cookies', cookies);
                    }
                    
                    window.location.href = '/download?' + params.toString();
                }
                
                document.getElementById('videoId').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') download();
                });
            </script>
        </body>
    </html>
    '''

@app.route('/download')
def download_video():
    video_param = request.args.get('v', '')
    cookies_param = request.args.get('cookies', '')
    
    if not video_param:
        return jsonify({'error': 'חסר פרמטר video ID'}), 400
    
    if 'youtube.com' in video_param or 'youtu.be' in video_param:
        video_url = video_param
    else:
        video_url = f'https://www.youtube.com/watch?v={video_param}'
    
    filename = None
    cookies_file = None
    
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
        
        if cookies_param:
            cookies_file = os.path.join(TEMP_DIR, f'temp_cookies_{os.getpid()}.txt')
            with open(cookies_file, 'w') as f:
                f.write(cookies_param)
            ydl_opts['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'video')
            
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"{title}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': f'שגיאה: {str(e)}'}), 500
    
    finally:
        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
            if cookies_file and os.path.exists(cookies_file):
                os.remove(cookies_file)
        except:
            pass

@app.route('/api/download', methods=['POST'])
def api_download():
    """
    API endpoint לשימוש מ-GAS או applications אחרות
    
    Example request:
    {
        "video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "cookies": "# Netscape HTTP Cookie File..."
    }
    """
    data = request.get_json()
    
    if not data or 'video_url' not in data:
        return jsonify({'error': 'חסר video_url'}), 400
    
    video_url = data['video_url']
    cookies_param = data.get('cookies', '')
    
    filename = None
    cookies_file = None
    
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(TEMP_DIR, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
        }
        
        if cookies_param:
            cookies_file = os.path.join(TEMP_DIR, f'temp_cookies_{os.getpid()}.txt')
            with open(cookies_file, 'w') as f:
                f.write(cookies_param)
            ydl_opts['cookiefile'] = cookies_file
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'video')
        
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                file_content = f.read()
            
            file_base64 = base64.b64encode(file_content).decode('utf-8')
            
            return jsonify({
                'success': True,
                'title': title,
                'filename': f"{title}.mp4",
                'file_base64': file_base64
            })
        else:
            return jsonify({'error': 'קובץ לא נמצא'}), 500
            
    except Exception as e:
        return jsonify({'error': f'שגיאה: {str(e)}'}), 500
    
    finally:
        try:
            if filename and os.path.exists(filename):
                os.remove(filename)
            if cookies_file and os.path.exists(cookies_file):
                os.remove(cookies_file)
        except:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
