# 📊 Reporte de Integración - Bot Inmobiliario AGO v1.1

## 1. Resumen Ejecutivo

El Bot Inmobiliario AGO es un agente automatizado que responde mensajes de WhatsApp Business con información precisa sobre los inmuebles registrados en un Google Sheet. El bot personaliza cada conversación pidiendo el nombre del cliente y ofrece detalles completos incluyendo requisitos, link de estudio en línea y datos de la inmobiliaria.

---

## 2. Arquitectura del Sistema

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   Cliente     │────>│  WhatsApp Cloud  │────>│   Webhook    │
│  (WhatsApp)   │<────│     API (Meta)   │<────│  (Flask/Bot) │
└──────────────┘     └──────────────────┘     └──────┬───────┘
                                                      │
                                                      │ Lee datos
                                                      ▼
                                               ┌──────────────┐
                                               │ Google Sheets │
                                               │  (Inmuebles)  │
                                               └──────────────┘
```

**Flujo:**
1. Cliente envía mensaje por WhatsApp
2. Meta reenvía el mensaje al webhook (servidor Flask)
3. El bot analiza la intención del mensaje
4. Consulta Google Sheets para obtener datos del inmueble
5. Responde al cliente por WhatsApp con información personalizada

---

## 3. Estructura del Google Sheet

### Columnas Requeridas (actualizadas v1.1)

| # | Columna | Descripción | Obligatoria |
|---|---------|-------------|:-----------:|
| A | **ID** | Código único del inmueble (ej: AGO001) | ✅ |
| B | **Tipo** | Apartamento, Apartaestudio, Casa, Local, etc. | ✅ |
| C | **Operacion** | Arriendo o Venta | ✅ |
| D | **Ubicacion** | Dirección completa | ✅ |
| E | **Ciudad** | Ciudad donde se encuentra | ✅ |
| F | **Precio** | Canon de arrendamiento o precio de venta | ✅ |
| G | **Area_m2** | Área en metros cuadrados | ✅ |
| H | **Habitaciones** | Número de habitaciones | ✅ |
| I | **Baños** | Número de baños | ✅ |
| J | **Parqueaderos** | Número de parqueaderos | ⬜ |
| K | **Tipo_parqueadero** | Moto o Carro | ⬜ |
| L | **Descripcion_Plus** | Descripción detallada y atractiva | ✅ |
| M | **Link_Fotos** | Enlace al catálogo de fotos (WhatsApp/Instagram) | ⬜ |
| N | **Estado** | "Disponible" o "Alquilado/Vendido" | ✅ |
| O | **Requisitos** | Requisitos específicos para este inmueble | ⬜ |
| P | **Link_Estudio** | Enlace al estudio en línea de El Libertador | ⬜ |
| Q | **Datos_Inmobiliaria** | Código y datos legales de la inmobiliaria | ⬜ |

> 💡 **Nota:** Las columnas marcadas con ⬜ son opcionales. Si no tienen datos, el bot usa valores genéricos o simplemente las omite.

---

## 4. Flujo de Conversación del Bot

```
CLIENTE NUEVO:
  Cliente: "Hola"
  AGO: "¡Hola! Soy AGO, en que te puedo ayudar?
        Antes de comenzar... ¿Cómo te llamas?"
  Cliente: "Carlos"
  AGO: "¡Un gusto, Carlos! 🤝 Ahora sí, estoy listo..."

CLIENTE YA REGISTRADO:
  Cliente: "Hola"
  AGO: "¡Hola de nuevo, Carlos! 😊 ¿En qué te puedo ayudar hoy?"

BÚSQUEDA:
  Cliente: "Busco apartamento en Cali"
  AGO: [Muestra inmuebles disponibles en Cali con detalles completos]

REQUISITOS:
  Cliente: "¿Qué requisitos piden?"
  AGO: [Muestra requisitos generales o específicos del inmueble]

APLICAR:
  Cliente: "¿Cómo aplico?"
  AGO: [Muestra Link_Estudio de El Libertador + Datos_Inmobiliaria]

VISITA:
  Cliente: "Quiero visitar el apartamento"
  AGO: [Confirma interés y notifica que un asesor lo contactará]
```

---

## 5. Intenciones Detectadas

| Intención | Palabras Clave | Acción del Bot |
|-----------|---------------|----------------|
| **Saludo** | hola, buenas, hey | Saluda y pide nombre (si es nuevo) |
| **Listado** | disponibles, catálogo, qué tienen | Muestra todos los inmuebles disponibles |
| **Búsqueda** | apartamento, Cali, 2 habitaciones | Busca y muestra inmuebles relevantes |
| **Requisitos** | requisitos, documentos, qué piden | Muestra requisitos generales o específicos |
| **Aplicar** | aplicar, estudio, formulario, libertador | Envía Link_Estudio + Datos_Inmobiliaria |
| **Visita** | visitar, agendar, cita | Confirma y notifica al asesor |
| **Despedida** | gracias, chao, adiós | Se despide personalizadamente |

---

## 6. Componentes del Código

| Archivo | Función |
|---------|---------|
| `app.py` | Servidor Flask, webhook GET (verificación) y POST (mensajes) |
| `bot_logic.py` | Detección de intenciones, flujo de nombre, generación de respuestas |
| `sheets_service.py` | Conexión a Google Sheets, búsqueda fuzzy, formateo de inmuebles |
| `whatsapp_service.py` | Envío de mensajes por WhatsApp Cloud API |
| `requirements.txt` | Dependencias Python |
| `Procfile` | Configuración para Railway/Heroku |
| `Dockerfile` | Contenedor Docker |
| `.env.example` | Variables de entorno necesarias |

---

## 7. Pasos de Configuración (Resumen)

### Paso 1: Meta for Developers
1. Crear app en [developers.facebook.com](https://developers.facebook.com/)
2. Agregar producto WhatsApp
3. Obtener: **Access Token** + **Phone Number ID**

### Paso 2: Google Cloud
1. Habilitar Google Sheets API
2. Crear cuenta de servicio + descargar `credentials.json`
3. Compartir el Sheet con el email de la cuenta de servicio

### Paso 3: Desplegar el bot
- **Railway.app** (recomendado, gratis para iniciar)
- **Render.com** (alternativa)
- **Docker** en servidor propio

### Paso 4: Configurar Webhook en Meta
1. URL: `https://tu-dominio.com/webhook`
2. Token de verificación: el que definiste en `.env`
3. Suscribirse al campo: `messages`

### Paso 5: Ir a Producción
1. Generar token permanente
2. Enviar app a revisión de Meta

---

## 8. Variables de Entorno Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `WHATSAPP_ACCESS_TOKEN` | Token de Meta | `EAABs...` |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número | `1234567890` |
| `WHATSAPP_VERIFY_TOKEN` | Token de verificación | `mi_token_secreto_ago_2024` |
| `GOOGLE_SHEET_ID` | ID del spreadsheet | `1hue1nHUQ6y...` |
| `GOOGLE_CREDENTIALS_PATH` | Ruta al JSON de credenciales | `credentials.json` |
| `PORT` | Puerto del servidor | `5000` |

---

## 9. Limitaciones Actuales

| Limitación | Solución Futura |
|------------|-----------------|
| Sesiones en memoria (se pierden al reiniciar) | Agregar Redis o base de datos |
| Solo mensajes de texto | Soportar imágenes y ubicación |
| Sin notificaciones al dueño | Agregar alertas cuando un cliente quiere visita |
| Sin historial de conversaciones | Agregar logging a base de datos |

---

## 10. Próximos Pasos Recomendados

1. ✅ **Agregar columnas al Google Sheet**: Requisitos, Link_Estudio, Datos_Inmobiliaria, Estado
2. ⬜ **Configurar Meta for Developers** (el usuario necesita hacerlo)
3. ⬜ **Crear cuenta de servicio de Google** (el usuario necesita hacerlo)
4. ⬜ **Desplegar el bot** en Railway o Render
5. ⬜ **Configurar webhook** en Meta
6. ⬜ **Probar** enviando mensajes de prueba
7. ⬜ **Ir a producción** con token permanente

---

*Reporte generado por AGO - Bot Inmobiliario v1.1*
*Fecha: 28 de Abril de 2026*
