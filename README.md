# Tienda Telegram

Tienda Telegram es un bot de Telegram para gestionar un pequeño catálogo de productos digitales con pagos a través de PayPal o Binance. Los archivos de base de datos y configuración se mantienen en el directorio `data`.

## Instalación

1. Clona este repositorio y entra en la carpeta del proyecto.
2. (Opcional) Crea un entorno virtual de Python con `python -m venv venv` y actívalo.
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Copia el archivo `.env.example` a `.env` (o crea uno nuevo) e incluye tu `TELEGRAM_BOT_TOKEN` y el `TELEGRAM_ADMIN_ID` que se usarán en `config.py`.

## Uso

Antes de iniciar el bot por primera vez se debe crear la estructura de la base de datos. Ejecuta:

```bash
python init_db.py
```

Esto crea las carpetas y la base de datos en `data/`.

Luego puedes iniciar el bot con:

```bash
python main.py
```

El bot mostrará mensajes de depuración y podrás configurarlo enviando `/start` desde la cuenta de administrador.

## Licencia

Este proyecto se distribuye sin una licencia explícita.

