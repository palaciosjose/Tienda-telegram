# Tienda Telegram

Tienda Telegram es un bot de Telegram para gestionar un pequeño catálogo de productos digitales con pagos a través de PayPal o Binance. Los archivos de base de datos y configuración se mantienen en el directorio `data`.

## Instalación

1. Clona este repositorio y entra en la carpeta del proyecto.
2. (Opcional) Crea un entorno virtual de Python con `python -m venv venv` y actívalo.
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Copia el archivo `.env.example` a `.env` (o crea uno nuevo).  El
   archivo de ejemplo incluye los campos `TELEGRAM_BOT_TOKEN` y
   `TELEGRAM_ADMIN_ID` como referencia, así que sólo debes reemplazar sus
   valores con tus credenciales.  Si utilizarás el sistema de publicidad,
   **debes** definir `TELEGRAM_TOKEN` con el token (o los tokens separados
   por comas) que empleará `advertising_cron.py`; el script fallará si no
   se configura esta variable.

   Puedes modificar la frecuencia de consulta al servidor de Telegram
   estableciendo las variables opcionales `POLL_INTERVAL`, `POLL_TIMEOUT`
   y `LONG_POLLING_TIMEOUT`.  Si no las defines, el bot utiliza los valores
   por defecto `8`, `25` y `20` segundos respectivamente.

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

Al iniciar, el proceso guarda su ID en `data/bot.pid` para evitar ejecuciones
duplicadas.  Si el archivo existe y corresponde a un proceso activo, el bot se
detendrá con una advertencia.  El archivo se elimina automáticamente al cerrar
el bot.

El bot mostrará mensajes de depuración y podrás configurarlo enviando `/start` desde la cuenta de administrador.

## Suscripciones

El proyecto incluye un sistema básico de **productos por suscripción**. Las tablas
`subscription_products` y `user_subscriptions` se crean automáticamente al
ejecutar `init_db.py`. A partir de esta versión se añaden índices en la fecha de
vencimiento para consultas más rápidas y se amplían los niveles de notificación
por defecto a `30,15,7,1` días.

Con el módulo `subscriptions.py` puedes:

1. Registrar nuevos planes con `add_subscription_product()` indicando duración,
   periodo de gracia y niveles de notificación.
2. Crear suscripciones para los usuarios con `create_user_subscription()` una
   vez que se complete un pago.
3. Ejecutar `check_subscriptions()` de forma diaria (por ejemplo mediante cron)
   para enviar recordatorios, renovar automáticamente si está configurado y
   suspender las suscripciones vencidas.
4. Cancelar suscripciones con `cancel_subscription()` y consultar todas las de
   un usuario mediante `get_user_subscriptions()`.
5. Consultar vencimientos próximos con `get_upcoming_subscriptions()` para
   mostrar un dashboard o generar reportes.

Para ejecutar el proceso diario de forma sencilla puedes programar `subscription_cron.py` con tu gestor de tareas preferido:

```bash
python subscription_cron.py
```

## Marketing/Advertising

El sistema incluye un módulo de **marketing automatizado** para enviar
campañas a distintos grupos de Telegram o WhatsApp. Todas las tablas
necesarias (`campaigns`, `campaign_schedules`, `target_groups`, etc.) se
crean automáticamente cuando ejecutas `init_db.py`, por lo que no requiere
una configuración extra.

Para mantener activo el envío automático ejecuta `advertising_cron.py` de
forma periódica o déjalo en segundo plano mediante un servicio `systemd` o
una entrada de `cron`:

```bash
python advertising_cron.py
```

Desde el panel de administración aparecerá una nueva opción **📢 Marketing**
con comandos para gestionar campañas:

- `🎯 Nueva campaña` para registrar una campaña.
- `📋 Ver campañas` para listar las existentes.
- `⏰ Programar envíos` para definir los horarios.
- `🎯 Gestionar grupos` para administrar los grupos objetivo.
- `📊 Estadísticas hoy` para consultar el resumen diario.
- `⚙️ Configuración` para ajustes adicionales.
- `▶️ Envío manual` para disparar un envío inmediato.

`advertising_cron.py` obtiene los tokens a utilizar desde la variable de entorno
`TELEGRAM_TOKEN`.  Puedes indicar varios tokens separados por comas si
necesitas repartir la carga entre diferentes bots.  Si la variable no está
definida el script terminará con un error.

## Pruebas

Para ejecutar las pruebas automatizadas instala las dependencias y luego ejecuta:

```bash
pytest
```

## Licencia

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).

