# Tienda Telegram

Tienda Telegram es un bot de Telegram para gestionar un pequeño catálogo de productos digitales con pagos a través de PayPal o Binance. Los archivos de base de datos y configuración se mantienen en el directorio `data`.
Cada producto puede incluir un campo opcional `duración en días` que define su vigencia tras la compra. Las suscripciones como característica independiente dejaron de estar soportadas.

## Instalación

1. Clona este repositorio y entra en la carpeta del proyecto.
2. (Opcional) Crea un entorno virtual de Python con `python -m venv venv` y actívalo.
3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Copia el archivo `.env.example` a `.env` (o crea uno nuevo).  El
   archivo de ejemplo incluye los campos `TELEGRAM_BOT_TOKEN`,
   `TELEGRAM_ADMIN_ID` y `TELEGRAM_TOKEN` como referencia, así que sólo
   debes reemplazar sus valores con tus credenciales.  Las variables
   `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ADMIN_ID` son obligatorias, el bot
   fallará si no se definen. Si utilizarás el
   sistema de publicidad, **debes** definir `TELEGRAM_TOKEN` con el token
   (o los tokens separados por comas) que empleará `advertising_cron.py`;
   el script fallará si no se configura esta variable.

  Para ejecutar el bot mediante **webhook** define en `.env` la
  variable `WEBHOOK_URL` con la dirección pública que recibirá las
  actualizaciones (por ejemplo `https://tu-dominio.com/bot`). También
  puedes ajustar `WEBHOOK_PORT`, `WEBHOOK_LISTEN` y, si usas HTTPS con
  certificados propios, `WEBHOOK_SSL_CERT` y `WEBHOOK_SSL_PRIV`.
  **El bot no iniciará a menos que proporciones `WEBHOOK_URL`.** La
  configuración lanzará un `RuntimeError` y `run_webhook()` finalizará
  con un error si esta variable queda vacía.

### Actualización

Si cuentas con una instalación previa y tu base de datos incluye las tablas
`subscription_products` o `user_subscriptions`, ejecuta:

```bash
python migrate_drop_subscriptions.py
```

antes de iniciar la nueva versión del bot para eliminarlas de forma segura.

Si tu base de datos de publicidad no incluye la columna `shop_id`,
ejecuta:

```bash
python migrate_add_shop_id_ads.py
```
o `init_db.py` para crear la base desde cero. Esto añadirá el campo
faltante y prevendrá errores en el módulo de marketing.

Si la tabla `target_groups` no incluye la columna `topic_id`, ejecuta:

```bash
python migrate_add_topic_id.py
```
o `init_db.py` para crear la base desde cero. Esto añadirá la columna para
soportar temas de Telegram.

Si utilizas una versión antigua y tu tabla `shops` no incluye los campos de
descripción o botones de inicio, ejecuta:

```bash
python migrate_add_shop_info.py
```

Para que la configuración de descuentos funcione por tienda debes añadir la
columna `shop_id` a `discount_config` con:

```bash
python migrate_add_shop_id_discount.py
```

El sistema de marketing requiere una tabla `bot_groups`. Si no la tienes,
ejecuta:

```bash
python migrate_create_bot_groups.py
```

Si la tabla `campaign_schedules` no incluye la columna `group_ids`, ejecuta:

```bash
python migrate_add_group_ids.py
```
o `init_db.py` para crear la base desde cero.

Por último, si la tabla `goods` aún no utiliza `(name, shop_id)` como clave
primaria ejecuta:

```bash
python migrate_goods_unique_pair.py
```
o `init_db.py` para crear la base desde cero.

## Uso

Antes de iniciar el bot por primera vez se debe crear la estructura de la base de datos. Ejecuta:

```bash
python init_db.py
```

Esto crea las carpetas y la base de datos en `data/`.

> **Nota**: las tablas necesarias para el sistema de descuentos se
> crean automáticamente la primera vez que ejecutes el bot. Si ves el
> error `no such table: discount_config`, puedes generarlas manualmente
> ejecutando `python migrate_create_discounts.py` o `python reset_data.py`.

Luego puedes iniciar el bot con:

```bash
python main.py
```

Este comando levanta un servidor Flask que escucha en `WEBHOOK_PORT` y registra
el webhook definido en `WEBHOOK_URL`. Al iniciar, el proceso guarda su ID en
`data/bot.pid` para evitar ejecuciones duplicadas. Si el archivo existe y
corresponde a un proceso activo, el bot se detendrá con una advertencia. El
archivo se elimina automáticamente al cerrar el bot. Además, el servidor expone
la ruta `/metrics` que puede usarse para comprobar el estado del bot.
El valor de `WEBHOOK_URL` es obligatorio: si se deja vacío, la carga de
`config.py` lanzará un `RuntimeError` antes de iniciar el servidor.

### Reinicio del bot

Si necesitas reiniciarlo manualmente ejecuta:

```bash
bash restart.sh
```
No intentes ejecutarlo con `python3`; debes correrlo con `bash`.

El script mata cualquier proceso activo de `main.py`, elimina `data/bot.pid` y
vuelve a lanzarlo en segundo plano guardando la salida en `bot.log`. Tras el
reinicio puedes revisar dicho archivo o visitar `/metrics` para verificar que el
bot responda correctamente.

### Despliegue en hosting compartido

Si tu proveedor no permite procesos persistentes, puedes hospedar el bot
ejecutando `webhook_server.py` y apuntando el webhook hacia ese servidor
(o usar el proxy `webhook.php`). Copia `.env.example` a `.env`, define
`WEBHOOK_URL` con la URL pública de tu dominio y luego ejecuta:

```bash
python webhook_server.py
```

Para usar la alternativa en PHP, sube `webhook.php` a tu hosting y
configura la ruta de destino en el script (`http://127.0.0.1:8444` por
defecto). Asegúrate de mantener la carpeta `data/` en la misma ruta que
el bot y crea una tarea `cron` para ejecutar regularmente
`keep_bot_alive.sh`, lo que reiniciará el proceso si se detiene. Si tu
dominio cuenta con certificado HTTPS, define `WEBHOOK_SSL_CERT` y
`WEBHOOK_SSL_PRIV` en `.env` para usarlo en la conexión segura.

El bot mostrará mensajes de depuración y podrás configurarlo enviando `/start` desde la cuenta de administrador.  Para
ver mensajes más detallados establece la variable de entorno `LOGLEVEL` a `DEBUG` al ejecutarlo:

```bash
LOGLEVEL=DEBUG python main.py
```

Tras ello, los administradores deben escribir `/adm` para abrir el panel de administración. El comando solo está disponible para los IDs indicados en `TELEGRAM_ADMIN_ID` o en `data/lists/admins_list.txt`.

Desde ese menú también podrás pulsar **"Mis compras"** para revisar un resumen de todos los productos que hayas adquirido.

Asimismo están disponibles los comandos `/help` y `/report` (o `/reporte`).
`/help` envía al usuario el texto de ayuda configurado, mientras que
`/report` permite remitir incidencias o consultas directamente al administrador.

## Múltiples tiendas

El bot admite gestionar varias tiendas. El usuario cuyo ID figura en `TELEGRAM_ADMIN_ID` es el *super admin* y posee un menú adicional **🛍️ Gestionar tiendas** dentro de **⚙️ Otros**. Solo este super admin puede añadir o eliminar otros administradores.

Desde allí puede crear nuevas tiendas y asignar el ID de Telegram de su administrador. Cada cliente, al enviar `/start`, verá la lista de tiendas disponibles y deberá elegir una para acceder al catálogo. Su elección se guarda para futuras visitas. Si un usuario ya tiene tienda asignada, `/start` lo lleva directamente al menú principal.

Cada administrador puede renombrar su tienda desde **⚙️ Otros** usando la opción *Cambiar nombre de tienda*.

### Calificaciones de tienda

Los clientes pueden puntuar a cada vendedor de 1 a 5 estrellas desde la portada de la tienda. La media de calificaciones aparece bajo la descripción y cada usuario puede actualizar su voto en cualquier momento eligiendo nuevamente el número de estrellas.

Si vienes de una instalación antigua de una sola tienda, ejecuta `python migrate_add_shop_id.py` (o `init_db.py` si prefieres crear la base desde cero) para añadir la columna `shop_id` requerida.

Para registrar la relación entre usuarios y tiendas existentes, ejecuta:

```bash
python migrate_create_shop_users.py
```

Esto creará la tabla `shop_users` necesaria para las difusiones por tienda.

### Nombre de la tienda

Al crear una tienda se solicitará un nombre, el cual verán los clientes al elegir tienda después de enviar `/start`. Los administradores pueden cambiar este nombre más adelante desde **⚙️ Otros** → **✏️ Renombrar tienda**.

### Presentación de la tienda

Para ajustar la información que se muestra al entrar a una tienda abre el **menú de administración** y selecciona **⚙️ Otros**. Allí encontrarás las opciones:

- *Cambiar nombre de tienda*
- *Cambiar descripción de tienda*
- *Cambiar multimedia de tienda*
- *Cambiar botones de tienda*
- *Cambiar mensaje de inicio (/start)* *(solo super admin)*

El último permite personalizar el texto y la multimedia que verán los usuarios al enviar `/start`.

## Panel de administración

Al entrar verás botones para gestionar las distintas funciones del bot. Entre
ellos se incluyen **💬 Respuestas**, **📦 Surtido**, **➕ Producto**, **💰 Pagos**,
**📊 Stats**, **Resumen de compradores**, **📣 Difusión**, **📢 Marketing**,
**💸 Descuentos** y **⚙️ Otros**.

Si en mitad de un proceso quieres detenerte, escribe `/cancel` o pulsa el botón
*Cancelar* que aparece en muchos diálogos para volver al menú previo.

La opción **Resumen de compradores** genera un listado ordenado por el total
gastado. Para cada comprador se muestra su ID, nombre de usuario, la suma de sus
pagos en dólares y los productos adquiridos.

En **💬 Respuestas** puedes definir distintos textos que el bot enviará. Se añadió la opción
**Agregar/Cambiar mensaje de entrega manual**, utilizado cuando un producto requiere
entrega manual. En ese mensaje puedes incluir las palabras `username` y `name` para
personalizarlo. Configurar **💬 Respuestas** es un privilegio exclusivo del super admin.

### Carga y edición de unidades

En **➕ Producto** se muestran los productos existentes. Tras elegir uno
aparecen tres opciones:

- **Añadir unidades** – agrega nuevas líneas al archivo `data/goods/<producto>.txt`.
- **Editar unidades** – reemplaza el contenido de líneas específicas.
- **Eliminar unidades** – borra las líneas seleccionadas.

Después de cada acción se vuelve al menú de productos.

Si el stock es muy extenso y el mensaje supera los 4096 caracteres que permite
Telegram, el bot lo envía en varias partes automáticamente.

Al crear una nueva posición se preguntará ahora **¿Entrega manual?**. Si respondes
*Sí*, el bot omitirá el formato del producto y utilizará el mensaje configurado
anteriormente para avisar al comprador.

Además, cada producto puede pertenecer a una **categoría**. Desde el panel principal está disponible el menú *🏷️ Categorías* para crear, eliminar, renombrar o ver categorías. Al crear un producto se solicitará elegir una existente o registrar una nueva.

### Difusión

La opción **📣 Difusión** permite enviar un anuncio de forma masiva. Tras
seleccionarla puedes escoger entre **A todos los usuarios** o
**Solo a compradores**, según quieras contactar a toda tu base de usuarios o
únicamente a quienes ya han realizado compras.

Indica cuántos destinatarios procesar y escribe el texto del mensaje. De forma
opcional puedes adjuntar una foto, video o documento antes de confirmar.
Finalizado el envío el bot mostrará un resumen con los aciertos y fallos
obtenidos.

## Marketing/Advertising

El sistema incluye un módulo de **marketing automatizado** para enviar
campañas a distintos grupos de Telegram. Todas las tablas
necesarias (`campaigns`, `campaign_schedules`, `target_groups`, etc.) se
crean automáticamente cuando ejecutas `init_db.py`, por lo que no requiere
una configuración extra.

Para mantener activo el envío automático ejecuta `advertising_cron.py` de
forma periódica o déjalo en segundo plano mediante un servicio `systemd` o
una entrada de `cron`:

```bash
python advertising_cron.py
```

El script determina su ubicación y la agrega al `PYTHONPATH`, por lo que no
necesitas modificar rutas manualmente. Asegúrate de lanzarlo desde la carpeta
del proyecto (o con el directorio de trabajo apuntando allí) para que pueda
encontrar la base de datos.

Desde el panel de administración aparecerá una nueva opción **📢 Marketing**
con comandos para gestionar campañas:

- `🎯 Nueva campaña` para registrar una campaña.
- `🛒 Campaña de producto` para crear una campaña basada en un producto existente.
- `📋 Ver campañas` para listar las existentes.
- `🗑️ Eliminar campaña` para borrar una campaña indicando su ID.
- `⏰ Programar envíos` para definir los horarios.
- `🎯 Gestionar grupos` para administrar los grupos objetivo.
- `📊 Estadísticas hoy` para consultar el resumen diario.
- `⚙️ Configuración` para ajustes adicionales.
  - `▶️ Envío manual <ID>` para disparar un envío inmediato indicando el
    identificador de la campaña. Tras introducir el ID el bot mostrará una lista
    de grupos objetivo para seleccionar. Si un destino corresponde a un topic
    específico aparecerá como `Nombre (ID) (topic <topic_id>)`.

### Crear y programar campañas

1. Abre **📢 Marketing** y selecciona **🎯 Nueva campaña** para registrar el
   mensaje y los botones opcionales. Si deseas usar un producto existente elige
   **🛒 Campaña de producto**.
2. Con la campaña creada ejecuta **⏰ Programar envíos &lt;ID&gt; &lt;días&gt;
   &lt;HH:MM&gt; &lt;HH:MM&gt;** indicando el identificador, los días separados
   por comas y una o más horas. Los días pueden escribirse en español
   (*lunes*, *martes*, ...) o en inglés (*monday*, *tuesday*, ...). Cuando
   existan grupos registrados el bot permitirá elegir los destinos antes de
   confirmar.
3. Para que los envíos permanezcan activos ejecuta `advertising_cron.py` de
   forma periódica (por ejemplo mediante `cron`) o deja corriendo
   `advertising_daemon.py`, que invoca dicho script cada minuto. El daemon ahora
   detecta automáticamente su ubicación y escribe `advertising.log` en esa
   carpeta, de modo que puedes ejecutarlo desde cualquier ruta.

El campo `group_ids` de la tabla `campaign_schedules` guarda los identificadores
de los grupos destino separados por comas; si se deja vacío se utilizarán todos
los grupos activos. Por su parte, `topic_id` en `target_groups` señala el topic
específico dentro de un grupo cuando se emplean temas de Telegram.

Para cancelar, reactivar, editar o eliminar programaciones ya creadas abre
**📆 Programaciones**. El listado muestra cada ID junto con botones para
`Cancelar`/`Reactivar`, `✏️ Editar` o `🗑️ Eliminar` la programación.

Para consultar desde la terminal los horarios y grupos asignados a cada
programación puedes ejecutar:

```bash
python list_schedules.py
```

El script ahora muestra los campos `schedule_json`, `frequency` y
`next_send_telegram`, despliega los días y horas configurados (por ejemplo
`lunes 10:00, 15:00`) e indica si la programación está activa junto con la
próxima fecha de envío en Telegram, si existe.

La *Campaña de producto* permite seleccionar uno de los artículos ya creados y
enviar su información como anuncio. El bot añadirá automáticamente un botón que
apunta al producto usando un enlace profundo, de modo que al abrirlo se muestren
los detalles de ese artículo.

Durante estos flujos puedes cancelar en cualquier momento enviando `Cancelar` o
`/cancel`, o presionando el botón *Cancelar y volver a Marketing* para regresar
al menú de marketing.

`advertising_cron.py` obtiene los tokens a utilizar desde la variable de entorno
`TELEGRAM_TOKEN`.  Puedes indicar varios tokens separados por comas si
necesitas repartir la carga entre diferentes bots.  Si la variable no está
definida el script terminará con un error.

Si deseas verificar manualmente que las campañas pendientes se procesan
correctamente ejecuta:

```bash
python test_auto_sender.py
```

El script carga los tokens desde `.env` (o los aceptados mediante
`--token`) y llama una vez a `AutoSender.process_campaigns()` mostrando por
pantalla si hubo envíos.

## Expiración de compras

Si defines la opción **duración en días** para un producto, las compras de ese
artículo almacenarán su fecha de vencimiento. Para avisar a los usuarios cuando
una compra haya expirado ejecuta periódicamente `expiration_cron.py`. El script
buscará compras vencidas y enviará un mensaje al comprador sugiriendo renovar la
adquisición. Puedes programarlo con `cron` agregando una línea como la
siguiente:

```cron
0 9 * * * cd /ruta/a/Tienda-telegram && TELEGRAM_TOKEN="<tu_token>" python expiration_cron.py
```

Reemplaza la ruta y el token según corresponda. También puedes ejecutarlo de
forma puntual con:

```bash
python expiration_cron.py
```

`expiration_cron.py` utiliza el token indicado en la variable de entorno
`TELEGRAM_TOKEN`. Si no se define, tomará el valor configurado en `config.py` a
través de `bot_instance.py`.

## Pruebas

Para ejecutar las pruebas automatizadas instala las dependencias y luego ejecuta:

```bash
pytest
```

## Depuración

Para verificar que la conexión con el administrador funcione correctamente puedes ejecutar:

```bash
python verify_admin_connection.py
```

El script imprime el ID de administrador configurado y la lista completa de administradores.
Luego intenta enviar un mensaje de prueba al ID principal mostrando el resultado en la consola.

## Licencia

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).
