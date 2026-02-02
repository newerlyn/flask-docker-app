from flask import Flask, jsonify, request, render_template, send_file
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Настройки приложения через переменные окружения
PORT = int(os.environ.get('PORT', 8000))
APP_NAME = os.environ.get('APP_NAME', 'Flask Docker App')
DEBUG_MODE = os.environ.get('DEBUG', 'False').lower() == 'true'

# Директория для загрузки файлов
UPLOAD_FOLDER = '/app/storage'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json'}

# Создаем директорию, если ее нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Конфигурация Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Файл для логов
LOG_FILE = os.path.join(UPLOAD_FOLDER, 'app_log.json')

def allowed_file(filename):
    """Проверяем разрешенные расширения файлов"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_request(endpoint, method, ip_address):
    """Логируем запросы в JSON файл"""
    try:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'ip': ip_address,
            'app_name': APP_NAME,
            'port': PORT
        }
        
        # Читаем существующие логи
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Добавляем новую запись
        logs.append(log_entry)
        
        # Сохраняем (ограничиваем 100 последних записей)
        with open(LOG_FILE, 'w') as f:
            json.dump(logs[-100:], f, indent=2)
            
    except Exception as e:
        print(f"Logging error: {e}")

@app.route('/')
def home():
    """Главная страница с информацией о приложении"""
    log_request('/', 'GET', request.remote_addr)
    
    info = {
        'app_name': APP_NAME,
        'version': '1.0.0',
        'status': 'running',
        'port': PORT,
        'debug_mode': DEBUG_MODE,
        'storage_path': app.config['UPLOAD_FOLDER'],
        'endpoints': [
            {'path': '/', 'methods': ['GET'], 'description': 'Главная страница'},
            {'path': '/health', 'methods': ['GET'], 'description': 'Проверка здоровья'},
            {'path': '/upload', 'methods': ['POST'], 'description': 'Загрузка файла'},
            {'path': '/files', 'methods': ['GET'], 'description': 'Список файлов'},
            {'path': '/download/<filename>', 'methods': ['GET'], 'description': 'Скачать файл'},
            {'path': '/logs', 'methods': ['GET'], 'description': 'Посмотреть логи'},
            {'path': '/env', 'methods': ['GET'], 'description': 'Переменные окружения'}
        ]
    }
    
    return jsonify(info)

@app.route('/health')
def health_check():
    """Проверка здоровья приложения"""
    log_request('/health', 'GET', request.remote_addr)
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': APP_NAME,
        'storage_accessible': os.path.exists(UPLOAD_FOLDER),
        'disk_usage': {
            'storage_path': UPLOAD_FOLDER,
            'file_count': len(os.listdir(UPLOAD_FOLDER)) if os.path.exists(UPLOAD_FOLDER) else 0
        }
    }
    
    return jsonify(health_status)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Загрузка файла на сервер"""
    log_request('/upload', 'POST', request.remote_addr)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Сохраняем файл
        file.save(filepath)
        
        # Получаем информацию о файле
        file_info = {
            'filename': filename,
            'size': os.path.getsize(filepath),
            'upload_time': datetime.now().isoformat(),
            'path': filepath
        }
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': file_info
        })
    
    return jsonify({'error': 'File type not allowed. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS)}), 400

@app.route('/files', methods=['GET'])
def list_files():
    """Получение списка всех файлов"""
    log_request('/files', 'GET', request.remote_addr)
    
    try:
        files = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
        
        return jsonify({
            'count': len(files),
            'files': files,
            'storage_path': app.config['UPLOAD_FOLDER']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Скачивание файла"""
    log_request(f'/download/{filename}', 'GET', request.remote_addr)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    if not os.path.isfile(filepath):
        return jsonify({'error': 'Not a file'}), 400
    
    return send_file(filepath, as_attachment=True)

@app.route('/logs', methods=['GET'])
def view_logs():
    """Просмотр логов приложения"""
    log_request('/logs', 'GET', request.remote_addr)
    
    if not os.path.exists(LOG_FILE):
        return jsonify({'message': 'No logs yet', 'logs': []})
    
    try:
        with open(LOG_FILE, 'r') as f:
            logs = json.load(f)
        
        return jsonify({
            'total_entries': len(logs),
            'logs': logs[-20:]  # Последние 20 записей
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/env', methods=['GET'])
def show_env():
    """Показать переменные окружения (без секретов)"""
    log_request('/env', 'GET', request.remote_addr)
    
    env_vars = {
        'PORT': PORT,
        'APP_NAME': APP_NAME,
        'DEBUG_MODE': DEBUG_MODE,
        'UPLOAD_FOLDER': UPLOAD_FOLDER,
        'PYTHON_VERSION': os.environ.get('PYTHON_VERSION', 'Unknown'),
        'HOSTNAME': os.environ.get('HOSTNAME', 'Unknown'),
        'IN_DOCKER': os.environ.get('IN_DOCKER', 'False')
    }
    
    return jsonify(env_vars)

@app.errorhandler(404)
def not_found(error):
    """Обработка 404 ошибки"""
    return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработка 500 ошибки"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print(f"🚀 Starting {APP_NAME} on port {PORT}")
    print(f"📁 Storage folder: {UPLOAD_FOLDER}")
    print(f"🔧 Debug mode: {DEBUG_MODE}")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',  # Принимаем соединения со всех интерфейсов
        port=PORT,
        debug=DEBUG_MODE
    )
