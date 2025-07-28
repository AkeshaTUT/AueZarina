# 🔧 Исправление ошибок в Replit

## Проблема с пакетом telegram

Если вы видите ошибку:
```
ImportError: cannot import name 'Bot' from 'telegram'
```

### Решение:

1. **Удалите неправильный пакет telegram:**
   В консоли Replit выполните:
   ```bash
   pip uninstall telegram -y
   ```

2. **Установите правильные зависимости:**
   ```bash
   pip install python-telegram-bot==20.7 requests beautifulsoup4 flask schedule openai
   ```

3. **Или используйте упрощенный requirements:**
   Переименуйте `requirements_replit.txt` в `requirements.txt`:
   ```bash
   mv requirements_replit.txt requirements.txt
   pip install -r requirements.txt
   ```

4. **Перезапустите Repl:**
   - Нажмите Stop
   - Затем Run

## Альтернативное решение

Если проблемы продолжаются, создайте файл `.replit` с содержимым:

```toml
modules = ["python-3.11"]

[nix]
channel = "stable-22_11"

[[ports]]
localPort = 8000
externalPort = 80

[deployment]
run = ["python", "main.py"]
```

## Установка через Poetry (если доступно)

```bash
poetry add python-telegram-bot requests beautifulsoup4 flask schedule openai
```

## Проверка установки

После установки проверьте:
```python
import telegram
print(telegram.__version__)
```

Должна быть версия 20.7 или выше.
