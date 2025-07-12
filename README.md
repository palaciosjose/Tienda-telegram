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

## Uso

Antes de iniciar el bot por primera vez se debe crear la estructura de la base de datos. Ejecuta:

```bash
python init_db.py
```

Esto crea las carpetas y la base de datos en `data/`.

> **Nota**: las tablas necesarias para el sistema de descuentos se
> crean automáticamente la primera vez que ejecutes el bot. Si ves el
> error `no such table: discount_config`, puedes generarlas manualmente
> con `python setup_discounts.py`.

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

El bot mostrará mensajes de depuración y podrás configurarlo enviando `/start` desde la cuenta de administrador.  Para
ver mensajes más detallados establece la variable de entorno `LOGLEVEL` a `DEBUG` al ejecutarlo:

```bash
LOGLEVEL=DEBUG python main.py
```

Tras ello, los administradores deben escribir `/adm` para abrir el panel de administración. El comando solo está disponible para los IDs indicados en `TELEGRAM_ADMIN_ID` o en `data/lists/admins_list.txt`.

Desde ese menú también podrás pulsar **"Mis compras"** para revisar un resumen de todos los productos que hayas adquirido.
También puedes buscar productos por nombre enviando `/buscar <palabra>` y seleccionar el resultado para comprar.

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
**📊 Stats**, **📣 Difusión**, **📢 Marketing**, **💸 Descuentos** y **⚙️ Otros**.

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

Desde el panel de administración aparecerá una nueva opción **📢 Marketing**
con comandos para gestionar campañas:

- `🎯 Nueva campaña` para registrar una campaña.
- `📋 Ver campañas` para listar las existentes.
- `🗑️ Eliminar campaña` para borrar una campaña indicando su ID.
- `⏰ Programar envíos` para definir los horarios.
- `🎯 Gestionar grupos` para administrar los grupos objetivo.
- `📊 Estadísticas hoy` para consultar el resumen diario.
- `⚙️ Configuración` para ajustes adicionales.
- `▶️ Envío manual <ID>` para disparar un envío inmediato indicando el
  identificador de la campaña. Tras introducir el ID el bot mostrará una lista
  de grupos objetivo para seleccionar.

Durante estos flujos puedes cancelar en cualquier momento enviando `Cancelar` o
`/cancel`, o presionando el botón *Cancelar y volver a Marketing* para regresar
al menú de marketing.

`advertising_cron.py` obtiene los tokens a utilizar desde la variable de entorno
`TELEGRAM_TOKEN`.  Puedes indicar varios tokens separados por comas si
necesitas repartir la carga entre diferentes bots.  Si la variable no está
definida el script terminará con un error.

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

