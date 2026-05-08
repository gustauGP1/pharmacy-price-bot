# 🚀 Deployment Guide - Pharmacy Price Bot

Guía completa para desplegar el bot en Google Cloud Run.

## 📋 Requisitos Previos

- Cuenta de Google Cloud Platform
- Google Cloud SDK instalado (`gcloud`)
- Docker instalado (para pruebas locales)
- Credenciales configuradas:
  - Token de Telegram Bot
  - MongoDB Atlas URI
  - Upstash Redis URL
  - Groq API Key

## 🔧 Configuración Inicial

### 1. Configurar Google Cloud Project

```bash
# Autenticar
gcloud auth login

# Crear proyecto (si no existe)
gcloud projects create pharmacy-bot-prod --name="Pharmacy Price Bot"

# Configurar proyecto activo
gcloud config set project pharmacy-bot-prod

# Habilitar APIs necesarias
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Configurar Secrets en Google Secret Manager

```bash
# Crear secrets
echo -n "TU_TELEGRAM_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
echo -n "TU_MONGODB_URI" | gcloud secrets create mongodb-uri --data-file=-
echo -n "TU_REDIS_URL" | gcloud secrets create redis-url --data-file=-
echo -n "TU_GROQ_API_KEY" | gcloud secrets create groq-api-key --data-file=-

# Dar permisos al servicio de Cloud Run
PROJECT_NUMBER=$(gcloud projects describe pharmacy-bot-prod --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding telegram-bot-token \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding mongodb-uri \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding redis-url \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding groq-api-key \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## 🐳 Build y Deploy

### Opción 1: Deploy Automático con Cloud Build

```bash
# Desde el directorio raíz del proyecto
gcloud builds submit --config=deployment/cloudbuild.yaml
```

### Opción 2: Deploy Manual

```bash
# 1. Build de la imagen
docker build -t gcr.io/pharmacy-bot-prod/pharmacy-bot:latest -f deployment/Dockerfile .

# 2. Push a Container Registry
docker push gcr.io/pharmacy-bot-prod/pharmacy-bot:latest

# 3. Deploy a Cloud Run
gcloud run deploy pharmacy-bot \
  --image gcr.io/pharmacy-bot-prod/pharmacy-bot:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,MONGODB_URI=mongodb-uri:latest,REDIS_URL=redis-url:latest,GROQ_API_KEY=groq-api-key:latest
```

## 🔗 Configurar Webhook de Telegram

Después del deploy, obtén la URL del servicio:

```bash
SERVICE_URL=$(gcloud run services describe pharmacy-bot --region us-central1 --format 'value(status.url)')
echo "Service URL: $SERVICE_URL"
```

Configura el webhook:

```bash
curl -X POST "https://api.telegram.org/bot<TU_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${SERVICE_URL}/webhook\"}"
```

Verifica el webhook:

```bash
curl "https://api.telegram.org/bot<TU_BOT_TOKEN>/getWebhookInfo"
```

## 🧪 Pruebas Locales

### Con Docker

```bash
# Build
docker build -t pharmacy-bot -f deployment/Dockerfile .

# Run
docker run -p 8080:8080 \
  -e TELEGRAM_BOT_TOKEN="tu_token" \
  -e MONGODB_URI="tu_mongodb_uri" \
  -e REDIS_URL="tu_redis_url" \
  -e GROQ_API_KEY="tu_groq_key" \
  -e ENVIRONMENT="development" \
  pharmacy-bot
```

### Sin Docker

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar
python run.py
```

## 📊 Monitoreo

### Ver Logs

```bash
# Logs en tiempo real
gcloud run services logs tail pharmacy-bot --region us-central1

# Logs recientes
gcloud run services logs read pharmacy-bot --region us-central1 --limit 50
```

### Métricas

```bash
# Ver métricas en Cloud Console
gcloud run services describe pharmacy-bot --region us-central1
```

## 🔄 Actualizar el Bot

### Actualización Rápida

```bash
# Rebuild y redeploy
gcloud builds submit --config=deployment/cloudbuild.yaml
```

### Rollback

```bash
# Listar revisiones
gcloud run revisions list --service pharmacy-bot --region us-central1

# Rollback a revisión anterior
gcloud run services update-traffic pharmacy-bot \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

## 🔐 Seguridad

### Actualizar Secrets

```bash
# Actualizar un secret
echo -n "NUEVO_VALOR" | gcloud secrets versions add telegram-bot-token --data-file=-

# Redeploy para usar nuevo secret
gcloud run services update pharmacy-bot --region us-central1
```

### Configurar Firewall

```bash
# Restringir acceso solo a Telegram
gcloud run services update pharmacy-bot \
  --region us-central1 \
  --ingress internal-and-cloud-load-balancing
```

## 💰 Optimización de Costos

### Configurar Auto-scaling

```bash
gcloud run services update pharmacy-bot \
  --region us-central1 \
  --min-instances 0 \
  --max-instances 5 \
  --concurrency 80
```

### Monitorear Costos

```bash
# Ver uso de recursos
gcloud run services describe pharmacy-bot \
  --region us-central1 \
  --format="value(status.traffic)"
```

## 🐛 Troubleshooting

### Bot no responde

1. Verificar logs:
```bash
gcloud run services logs tail pharmacy-bot --region us-central1
```

2. Verificar webhook:
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

3. Verificar secrets:
```bash
gcloud secrets versions access latest --secret="telegram-bot-token"
```

### Errores de conexión a MongoDB

1. Verificar IP whitelist en MongoDB Atlas
2. Verificar secret de MongoDB URI
3. Revisar logs de conexión

### Errores de memoria

```bash
# Aumentar memoria
gcloud run services update pharmacy-bot \
  --region us-central1 \
  --memory 1Gi
```

## 📚 Recursos Adicionales

- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [MongoDB Atlas](https://docs.atlas.mongodb.com/)
- [Upstash Redis](https://docs.upstash.com/)

## 🆘 Soporte

Si encuentras problemas:
1. Revisa los logs
2. Verifica la configuración
3. Consulta la documentación
4. Abre un issue en GitHub

---

**Desarrollado con ❤️ en Chile** 🇨🇱

# Made with Bob