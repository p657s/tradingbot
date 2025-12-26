from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot funcionando ✅"

@app.route('/health')
def health():
    return {"status": "ok"}

def run_bot():
    """Ejecuta el bot en un thread separado"""
    os.system('python main.py')

if __name__ == '__main__':
    # Iniciar bot en thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Iniciar servidor web
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
```

Agregar a `requirements.txt`:
```
flask
