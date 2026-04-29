# 🏠 Guía Completa de Configuración - Bot Inmobiliario AGO

## Resumen
Este bot conecta tu WhatsApp Business con tu catálogo de inmuebles en Google Sheets. Cuando un cliente te escribe, AGO responde automáticamente con información precisa sobre tus propiedades disponibles.

---

## PASO 1: Configurar Meta for Developers (Facebook)

### 1.1 Crear cuenta y app
1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. Inicia sesión con tu cuenta de Facebook (la misma vinculada a tu WhatsApp Business)
3. Haz clic en **"Mis Apps"** > **"Crear App"**
4. Selecciona **"Otro"** como tipo
5. Selecciona **"Business"** como tipo de app
6. Dale un nombre (ej: "AGO Inmobiliaria") y crea la app

### 1.2 Agregar WhatsApp a la app
1. En el panel de tu app, busca **"WhatsApp"** en la sección de productos
2. Haz clic en **"Configurar"**
3. Te pedirá vincular tu cuenta de Meta Business Suite
4. Selecciona tu número de WhatsApp Business

### 1.3 Obtener las credenciales
1. En el panel de WhatsApp, ve a **"Configuración de la API"**
2. Copia el **Token de acceso temporal** (o genera uno permanente)
3. Copia el **ID del número de teléfono** (Phone Number ID)
4. Guarda ambos valores, los necesitarás en el archivo `.env`

> ⚠️ **IMPORTANTE**: El token temporal dura 24 horas. Para producción, genera un **Token de acceso permanente** desde la configuración del sistema en Meta Business Suite.

---

## PASO 2: Configurar Google Sheets API

### 2.1 Crear credenciales de servicio
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo o selecciona uno existente
3. Habilita la **Google Sheets API**: Busca "Google Sheets API" > Habilitar
4. Ve a **"Credenciales"** > **"Crear credenciales"** > **"Cuenta de servicio"**
5. Dale un nombre (ej: "ago-bot-sheets")
6. Crea una clave JSON: En la cuenta de servicio > Claves > Agregar clave > JSON
7. Descarga el archivo JSON y renómbralo como `credentials.json`

### 2.2 Compartir el Google Sheet
1. Abre el archivo `credentials.json` y busca el campo `"client_email"`
2. Copia ese email (algo como `ago-bot-sheets@proyecto.iam.gserviceaccount.com`)
3. Abre tu Google Sheet de inmuebles
4. Haz clic en **Compartir** y agrega ese email como **"Lector"**

---

## PASO 3: Desplegar el Bot

### Opción A: Railway (Recomendado - Gratis para empezar)
1. Ve a [Railway.app](https://railway.app/)
2. Crea una cuenta con GitHub
3. Haz clic en **"New Project"** > **"Deploy from GitHub Repo"**
4. Sube el código del bot a un repositorio de GitHub
5. Agrega las variables de entorno (del archivo `.env.example`)
6. Railway te dará una URL pública (ej: `https://ago-bot.up.railway.app`)

### Opción B: Render (Alternativa gratuita)
1. Ve a [Render.com](https://render.com/)
2. Crea un **Web Service** desde tu repositorio
3. Configura las variables de entorno
4. Render te dará una URL pública

### Opción C: Docker (Servidor propio)
```bash
docker build -t ago-bot .
docker run -p 5000:5000 --env-file .env ago-bot
```

---

## PASO 4: Configurar el Webhook en Meta

### 4.1 Registrar el webhook
1. En tu app de Meta for Developers, ve a **WhatsApp** > **Configuración**
2. En la sección **"Webhook"**, haz clic en **"Editar"**
3. En **URL de callback**: pega tu URL + `/webhook`
   - Ejemplo: `https://ago-bot.up.railway.app/webhook`
4. En **Token de verificación**: escribe exactamente lo mismo que pusiste en `WHATSAPP_VERIFY_TOKEN` de tu `.env`
   - Por defecto es: `mi_token_secreto_ago_2024`
5. Haz clic en **"Verificar y guardar"**

### 4.2 Suscribirse a eventos
1. Después de verificar, verás una lista de campos
2. **Suscríbete** (activa) al campo: `messages`
3. Esto hará que cada vez que alguien te escriba, WhatsApp envíe el mensaje a tu bot

---

## PASO 5: Probar el Bot

### 5.1 Prueba rápida
1. Desde otro teléfono, envía un mensaje a tu número de WhatsApp Business
2. Escribe: **"Hola"**
3. Deberías recibir: _"¡Hola! Soy AGO, en que te puedo ayudar?"_ seguido del menú de opciones
4. Escribe: **"disponibles"** para ver el listado completo
5. Escribe: **"apartamento en Cali"** para buscar algo específico

### 5.2 Verificar salud del servidor
- Visita `https://tu-url.com/health` en el navegador
- Deberías ver: `{"status": "healthy", "bot": "AGO - Agente Inmobiliario"}`

---

## PASO 6: Ir a Producción

### 6.1 Token permanente
1. En Meta Business Suite > Configuración del sistema
2. Ve a **"Usuarios del sistema"** > Agrega uno
3. Genera un **Token de acceso permanente** con permisos:
   - `whatsapp_business_messaging`
   - `whatsapp_business_management`
4. Reemplaza el token temporal en tu `.env`

### 6.2 Verificar la app
1. En Meta for Developers, envía tu app a **"Revisión de la app"**
2. Esto es necesario para que el bot funcione con usuarios que no sean administradores

---

## Estructura de Archivos
```
bot-inmobiliario-setup/
├── app.py                  # Servidor Flask (webhook principal)
├── bot_logic.py            # Lógica del bot (intenciones, respuestas)
├── sheets_service.py       # Conexión con Google Sheets
├── whatsapp_service.py     # Envío de mensajes por WhatsApp API
├── requirements.txt        # Dependencias Python
├── Procfile                # Para Railway/Heroku
├── Dockerfile              # Para Docker
├── .env.example            # Variables de entorno (plantilla)
└── GUIA_CONFIGURACION.md   # Esta guía
```

---

## Solución de Problemas

| Problema | Solución |
|----------|----------|
| Webhook no verifica | Revisa que `WHATSAPP_VERIFY_TOKEN` sea idéntico en `.env` y en Meta |
| Bot no responde | Verifica que el servidor esté corriendo (`/health`) |
| Error 403 en Sheets | Asegúrate de compartir el Sheet con el email de la cuenta de servicio |
| Token expirado | Genera un token permanente (Paso 6.1) |
| Mensajes duplicados | El bot ya maneja esto respondiendo siempre 200 al webhook |

---

## Soporte
Si necesitas ayuda con la configuración, vuelve a escribirme en el chat. ¡Estoy aquí para ayudarte! 🚀
