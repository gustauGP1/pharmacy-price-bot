# 🏥 Plan de Desarrollo: Bot de Telegram - Comparador de Precios de Farmacias Chile

## 📋 Resumen Ejecutivo

Bot de Telegram que permite comparar precios de medicamentos entre las principales farmacias de Chile (Cruz Verde, Salcobrand, Farmacias Ahumada) utilizando web scraping automático y recursos cloud gratuitos.

**Stack Tecnológico**: Python + Telegram Bot API + MongoDB Atlas + Google Cloud Run + Groq AI + Redis (Upstash)

## 🎯 Objetivos del Proyecto

1. ✅ Crear bot funcional con búsqueda inteligente de medicamentos
2. ✅ Implementar web scraping eficiente y respetuoso
3. ✅ Comparar precios en tiempo real entre 3 farmacias principales
4. ✅ Utilizar recursos cloud 100% gratuitos
5. ✅ Proporcionar experiencia de usuario excepcional
6. ✅ Implementar IA para mejorar búsquedas (Groq)

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Usuario de Telegram                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Bot de Telegram (Python)                        │
│         Desplegado en Google Cloud Run (Free)                │
└────────┬────────────────────────────────┬───────────────────┘
         │                                │
         ▼                                ▼
┌────────────────────┐          ┌────────────────────┐
│   Groq AI API      │          │  Redis Cache       │
│   (Free Tier)      │          │  (Upstash Free)    │
│   - Búsqueda IA    │          │  - TTL: 6 horas    │
│   - Sugerencias    │          │  - Rate limiting   │
└────────────────────┘          └────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              Web Scrapers (Paralelos)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Cruz Verde   │ │ Salcobrand   │ │ F. Ahumada   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │  MongoDB Atlas     │
                  │  (Free Tier 512MB) │
                  │  - Precios         │
                  │  - Historial       │
                  │  - Analytics       │
                  └────────────────────┘
```

## 📁 Estructura del Proyecto

```
pharmacy-price-bot/
├── 📂 bot/
│   ├── __init__.py
│   ├── main.py                 # Punto de entrada del bot
│   ├── handlers.py             # Manejadores de comandos
│   ├── keyboards.py            # Teclados inline
│   └── middleware.py           # Rate limiting, logging
│
├── 📂 scrapers/
│   ├── __init__.py
│   ├── base_scraper.py         # Clase base abstracta
│   ├── cruz_verde_scraper.py   # Scraper Cruz Verde
│   ├── salcobrand_scraper.py   # Scraper Salcobrand
│   ├── ahumada_scraper.py      # Scraper Farmacias Ahumada
│   └── scraper_manager.py      # Orquestador de scrapers
│
├── 📂 database/
│   ├── __init__.py
│   ├── mongodb_client.py       # Cliente MongoDB Atlas
│   ├── models.py               # Modelos de datos (Pydantic)
│   └── repositories.py         # Repositorios de datos
│
├── 📂 services/
│   ├── __init__.py
│   ├── cache_service.py        # Redis/Upstash cache
│   ├── ai_service.py           # Integración Groq AI
│   ├── comparison_service.py   # Lógica de comparación
│   └── analytics_service.py    # Métricas y estadísticas
│
├── 📂 utils/
│   ├── __init__.py
│   ├── logger.py               # Configuración logging
│   ├── validators.py           # Validación de datos
│   ├── formatters.py           # Formateo de mensajes
│   └── helpers.py              # Funciones auxiliares
│
├── 📂 config/
│   ├── __init__.py
│   └── settings.py             # Configuración centralizada
│
├── 📂 tests/
│   ├── __init__.py
│   ├── test_scrapers.py
│   ├── test_bot.py
│   └── test_services.py
│
├── 📂 deployment/
│   ├── Dockerfile              # Para Google Cloud Run
│   ├── cloudbuild.yaml         # CI/CD con Cloud Build
│   └── app.yaml                # Configuración App Engine
│
├── .env.example                # Plantilla variables de entorno
├── .gitignore
├── requirements.txt            # Dependencias Python
├── README.md                   # Documentación principal
├── DEPLOYMENT.md               # Guía de despliegue
└── run.py                      # Script de ejecución local
```

## 🔧 Stack Tecnológico Detallado

### Core Framework
```python
python-telegram-bot==20.7      # Bot framework
python-telegram-bot[webhooks]  # Soporte webhooks
```

### Web Scraping
```python
beautifulsoup4==4.12.2         # Parsing HTML
requests==2.31.0               # HTTP requests
selenium==4.15.0               # JavaScript rendering
webdriver-manager==4.0.1       # Auto driver management
lxml==4.9.3                    # Parser rápido
```

### Base de Datos y Cache
```python
pymongo==4.6.0                 # MongoDB driver
motor==3.3.2                   # MongoDB async
redis==5.0.1                   # Redis client
pydantic==2.5.0                # Validación de datos
```

### IA y Procesamiento
```python
groq==0.4.1                    # Groq AI SDK
langchain==0.1.0               # LLM framework (opcional)
```

### Utilidades
```python
python-dotenv==1.0.0           # Variables de entorno
loguru==0.7.2                  # Logging mejorado
tenacity==8.2.3                # Retry logic
aiohttp==3.9.1                 # Async HTTP
```

### Testing y Calidad
```python
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0                 # Code formatter
flake8==6.1.0                  # Linter
```

## ☁️ Recursos Cloud Gratuitos

### 1. Google Cloud Platform (Free Tier)

#### Google Cloud Run
- **Límites gratuitos**:
  - 2 millones de peticiones/mes
  - 360,000 GB-segundos de memoria
  - 180,000 vCPU-segundos
- **Uso**: Hosting del bot con webhooks
- **Ventajas**: Auto-scaling, pago por uso, HTTPS gratis

#### Google Cloud Build
- **Límites gratuitos**:
  - 120 minutos de build/día
- **Uso**: CI/CD automático desde GitHub

#### Google Cloud Storage
- **Límites gratuitos**:
  - 5 GB de almacenamiento
- **Uso**: Logs, backups, archivos estáticos

### 2. MongoDB Atlas (Free Tier)
- **Límites gratuitos**:
  - 512 MB de almacenamiento
  - Cluster compartido M0
  - Conexiones ilimitadas
- **Uso**: Base de datos principal
- **Colecciones**:
  - `medicines`: Catálogo de medicamentos
  - `prices`: Precios históricos
  - `searches`: Historial de búsquedas
  - `analytics`: Métricas de uso

### 3. Upstash Redis (Free Tier)
- **Límites gratuitos**:
  - 10,000 comandos/día
  - 256 MB de memoria
  - Latencia global baja
- **Uso**: Cache de precios y rate limiting
- **TTL**: 6 horas para precios

### 4. Groq AI (Free Tier)
- **Límites gratuitos**:
  - 14,400 peticiones/día
  - Modelos: Llama 3, Mixtral
  - Velocidad: ~500 tokens/segundo
- **Uso**:
  - Corrección de búsquedas
  - Sugerencias inteligentes
  - Normalización de nombres

### 5. Alternativas Adicionales

#### Railway.app (Free Tier)
- $5 de crédito mensual
- Ideal para desarrollo/testing

#### Render.com (Free Tier)
- 750 horas/mes
- Auto-deploy desde GitHub

#### Vercel (Free Tier)
- Serverless functions
- Edge network global

## 📊 Modelo de Datos (MongoDB)

### Colección: `pharmacies`
```javascript
{
  _id: ObjectId,
  name: "Cruz Verde",
  slug: "cruz-verde",
  website: "https://www.cruzverde.cl",
  logo_url: "https://...",
  active: true,
  scraper_config: {
    base_url: "https://www.cruzverde.cl/search",
    rate_limit: 2,  // segundos entre peticiones
    user_agent: "...",
    selectors: {
      product_container: ".product-card",
      name: ".product-name",
      price: ".product-price",
      stock: ".stock-status"
    }
  },
  created_at: ISODate,
  updated_at: ISODate
}
```

### Colección: `medicines`
```javascript
{
  _id: ObjectId,
  name: "Paracetamol 500mg",
  normalized_name: "paracetamol 500mg",
  generic_name: "Paracetamol",
  dosage: "500mg",
  presentation: "Comprimidos",
  laboratory: "Laboratorio Chile",
  description: "Analgésico y antipirético",
  tags: ["analgesico", "fiebre", "dolor"],
  search_count: 150,  // popularidad
  created_at: ISODate,
  updated_at: ISODate
}
```

### Colección: `prices`
```javascript
{
  _id: ObjectId,
  medicine_id: ObjectId,
  pharmacy_id: ObjectId,
  price: 2990,
  currency: "CLP",
  stock_available: true,
  stock_quantity: 50,  // si disponible
  url: "https://www.cruzverde.cl/producto/...",
  image_url: "https://...",
  scraped_at: ISODate,
  expires_at: ISODate,  // TTL index
  metadata: {
    discount: 10,  // porcentaje
    original_price: 3322,
    promotion: "Oferta especial"
  }
}
```

### Colección: `searches`
```javascript
{
  _id: ObjectId,
  user_id: 123456789,
  username: "usuario123",
  query: "paracetamol",
  normalized_query: "paracetamol",
  results_count: 3,
  pharmacies_searched: ["cruz-verde", "salcobrand", "ahumada"],
  best_price: 2990,
  worst_price: 3450,
  savings: 460,
  response_time_ms: 2500,
  searched_at: ISODate
}
```

### Colección: `analytics`
```javascript
{
  _id: ObjectId,
  date: ISODate("2026-05-08"),
  metrics: {
    total_searches: 1250,
    unique_users: 450,
    avg_response_time: 2300,
    cache_hit_rate: 0.75,
    scraper_success_rate: {
      "cruz-verde": 0.98,
      "salcobrand": 0.95,
      "ahumada": 0.97
    },
    top_searches: [
      { query: "paracetamol", count: 150 },
      { query: "ibuprofeno", count: 120 }
    ]
  }
}
```

## 🤖 Comandos del Bot

### Comandos Principales

#### `/start`
```
🏥 ¡Bienvenido al Comparador de Precios de Farmacias Chile!

Busca medicamentos y compara precios en tiempo real entre:
• 🟢 Cruz Verde
• 🔵 Salcobrand
• 🟡 Farmacias Ahumada

💡 Cómo usar:
/buscar paracetamol
/buscar ibuprofeno 400mg

🤖 Búsqueda inteligente con IA
⚡ Resultados en segundos
💰 Ahorra en tus medicamentos

Usa /ayuda para más información
```

#### `/buscar [medicamento]`
```
🔍 Buscando "Paracetamol 500mg"...
⏳ Consultando farmacias...

💊 Resultados encontrados:

1️⃣ 🟢 Cruz Verde - $2.990
   📦 Stock disponible (50+ unidades)
   💳 Precio con descuento
   🔗 [Ver en tienda]

2️⃣ 🔵 Salcobrand - $3.200
   📦 Stock disponible
   🔗 [Ver en tienda]

3️⃣ 🟡 Farmacias Ahumada - $3.450
   ⚠️ Stock limitado (5 unidades)
   🔗 [Ver en tienda]

💰 Ahorro máximo: $460 (13.3%)
⏰ Actualizado hace 15 minutos

[🔄 Actualizar] [🔔 Crear alerta] [🆕 Nueva búsqueda]
```

#### `/ayuda`
```
📖 Guía de Uso

🔍 Búsqueda:
/buscar [nombre del medicamento]
Ejemplo: /buscar aspirina 100mg

💡 Consejos:
• Incluye la dosis para mejores resultados
• Usa el nombre genérico o comercial
• La IA corregirá errores de escritura

🤖 Funciones:
• Comparación en tiempo real
• Alertas de precio (próximamente)
• Historial de búsquedas
• Sugerencias inteligentes

⚙️ Otros comandos:
/acerca - Información del bot
/stats - Estadísticas de uso

¿Problemas? Contacta: @soporte_bot
```

#### `/acerca`
```
ℹ️ Sobre el Bot

🏥 Comparador de Precios de Farmacias Chile
Versión 1.0.0

🎯 Misión:
Ayudarte a encontrar los mejores precios en medicamentos
y ahorrar en tus compras de farmacia.

🔧 Tecnología:
• Python + Telegram Bot API
• IA con Groq (Llama 3)
• MongoDB Atlas
• Google Cloud Run

📊 Estadísticas:
• 1,250 búsquedas hoy
• 450 usuarios activos
• 98% tasa de éxito

🔒 Privacidad:
No almacenamos información personal.
Solo guardamos estadísticas anónimas.

💻 Código abierto: [GitHub]
📧 Contacto: @admin_bot
```

## 🕷️ Estrategia de Web Scraping

### Principios Generales
1. **Respeto a robots.txt**: Verificar antes de scrapear
2. **Rate limiting**: Mínimo 2 segundos entre peticiones
3. **User-Agent rotativo**: Evitar bloqueos
4. **Manejo de errores**: Reintentos con backoff exponencial
5. **Cache agresivo**: Reducir carga en sitios

### Implementación por Farmacia

#### Cruz Verde
```python
# URL: https://www.cruzverde.cl
# Método: BeautifulSoup + Requests
# Características:
# - Sitio estático, fácil de scrapear
# - Búsqueda por query parameter
# - JSON-LD con datos estructurados

class CruzVerdeScraper(BaseScraper):
    BASE_URL = "https://www.cruzverde.cl"
    SEARCH_URL = f"{BASE_URL}/search"
    
    async def search(self, query: str) -> List[Product]:
        # Implementación con rate limiting
        # Parsing de resultados
        # Extracción de precios y stock
        pass
```

#### Salcobrand
```python
# URL: https://www.salcobrand.cl
# Método: Selenium (JavaScript dinámico)
# Características:
# - Contenido cargado con JS
# - Requiere espera de elementos
# - API interna posible

class SalcobrandScraper(BaseScraper):
    BASE_URL = "https://www.salcobrand.cl"
    
    async def search(self, query: str) -> List[Product]:
        # Selenium con headless Chrome
        # Espera de elementos dinámicos
        # Extracción de datos
        pass
```

#### Farmacias Ahumada
```python
# URL: https://www.farmaciasahumada.cl
# Método: BeautifulSoup + Requests
# Características:
# - Sitio híbrido
# - Posible API REST

class AhumadaScraper(BaseScraper):
    BASE_URL = "https://www.farmaciasahumada.cl"
    
    async def search(self, query: str) -> List[Product]:
        # Intentar API primero
        # Fallback a scraping HTML
        pass
```

### Scraper Manager (Orquestador)
```python
class ScraperManager:
    def __init__(self):
        self.scrapers = [
            CruzVerdeScraper(),
            SalcobrandScraper(),
            AhumadaScraper()
        ]
    
    async def search_all(self, query: str) -> Dict[str, List[Product]]:
        """Ejecuta scrapers en paralelo"""
        tasks = [
            scraper.search(query) 
            for scraper in self.scrapers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._process_results(results)
```

## 🧠 Integración con Groq AI

### Casos de Uso

#### 1. Normalización de Búsquedas
```python
# Usuario escribe: "paracetamol para el dolor de cabeza"
# Groq normaliza a: "paracetamol"

async def normalize_query(user_query: str) -> str:
    prompt = f"""
    Extrae solo el nombre del medicamento de esta búsqueda:
    "{user_query}"
    
    Responde solo con el nombre del medicamento, sin dosis ni descripción.
    """
    
    response = await groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=50
    )
    
    return response.choices[0].message.content.strip()
```

#### 2. Corrección de Errores
```python
# Usuario escribe: "paracetamol" (error de tipeo)
# Groq corrige a: "paracetamol"

async def correct_spelling(query: str) -> str:
    prompt = f"""
    Corrige el nombre de este medicamento si tiene errores:
    "{query}"
    
    Si está correcto, devuélvelo igual.
    Responde solo con el nombre corregido.
    """
    # Similar implementación
```

#### 3. Sugerencias Inteligentes
```python
# Usuario busca: "dolor de cabeza"
# Groq sugiere: ["paracetamol", "ibuprofeno", "aspirina"]

async def get_suggestions(symptom: str) -> List[str]:
    prompt = f"""
    Sugiere 3 medicamentos comunes para: "{symptom}"
    
    Responde en formato JSON:
    ["medicamento1", "medicamento2", "medicamento3"]
    """
    # Implementación con parsing JSON
```

### Límites y Optimización
- **Rate limit**: 14,400 peticiones/día = 10 por minuto
- **Cache**: Guardar respuestas comunes en Redis
- **Fallback**: Si Groq falla, usar búsqueda directa

## 💾 Sistema de Cache (Redis/Upstash)

### Estrategia de Cache

#### Niveles de Cache
```python
# Nivel 1: Precios (TTL: 6 horas)
cache_key = f"price:{medicine_name}:{pharmacy_slug}"
ttl = 6 * 3600  # 6 horas

# Nivel 2: Búsquedas normalizadas (TTL: 24 horas)
cache_key = f"normalized:{user_query}"
ttl = 24 * 3600

# Nivel 3: Sugerencias IA (TTL: 7 días)
cache_key = f"suggestions:{symptom}"
ttl = 7 * 24 * 3600
```

#### Implementación
```python
class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_prices(self, medicine: str) -> Optional[Dict]:
        """Obtiene precios del cache"""
        key = f"price:{medicine}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set_prices(self, medicine: str, prices: Dict, ttl: int = 21600):
        """Guarda precios en cache"""
        key = f"price:{medicine}"
        await self.redis.setex(
            key, 
            ttl, 
            json.dumps(prices)
        )
    
    async def invalidate(self, pattern: str):
        """Invalida cache por patrón"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

### Rate Limiting
```python
class RateLimiter:
    async def check_limit(self, user_id: int) -> bool:
        """Verifica límite de peticiones por usuario"""
        key = f"ratelimit:{user_id}"
        count = await self.redis.incr(key)
        
        if count == 1:
            await self.redis.expire(key, 60)  # 1 minuto
        
        return count <= 10  # 10 peticiones por minuto
```

## 🚀 Despliegue en Google Cloud Run

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variables de entorno
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Comando de inicio
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 bot.main:app
```

### cloudbuild.yaml
```yaml
steps:
  # Build
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/pharmacy-bot', '.']
  
  # Push
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/pharmacy-bot']
  
  # Deploy
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'pharmacy-bot'
      - '--image'
      - 'gcr.io/$PROJECT_ID/pharmacy-bot'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--memory'
      - '512Mi'
      - '--cpu'
      - '1'
      - '--max-instances'
      - '10'
      - '--set-env-vars'
      - 'TELEGRAM_TOKEN=${_TELEGRAM_TOKEN},MONGODB_URI=${_MONGODB_URI}'

timeout: 1200s
```

### Configuración de Webhooks
```python
# bot/main.py
from flask import Flask, request
from telegram import Update

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Endpoint para webhooks de Telegram"""
    update = Update.de_json(request.get_json(), bot)
    await application.process_update(update)
    return 'OK'

@app.route('/health', methods=['GET'])
def health():
    """Health check para Cloud Run"""
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    # Configurar webhook
    webhook_url = f"https://your-app.run.app/webhook"
    bot.set_webhook(webhook_url)
    
    # Iniciar servidor
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

## 📈 Monitoreo y Analytics

### Métricas Clave
1. **Rendimiento**:
   - Tiempo de respuesta promedio
   - Tasa de éxito de scrapers
   - Cache hit rate
   - Uptime del bot

2. **Uso**:
   - Búsquedas por día/hora
   - Usuarios activos
   - Medicamentos más buscados
   - Farmacias más consultadas

3. **Negocio**:
   - Ahorro promedio por búsqueda
   - Conversión a compra (si tracking)
   - Retención de usuarios

### Implementación con Google Cloud Monitoring
```python
from google.cloud import monitoring_v3

class MetricsService:
    def __init__(self):
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{PROJECT_ID}"
    
    def record_search(self, response_time: float, success: bool):
        """Registra métrica de búsqueda"""
        series = monitoring_v3.TimeSeries()
        series.metric.type = "custom.googleapis.com/pharmacy_bot/search"
        series.resource.type = "global"
        
        point = monitoring_v3.Point()
        point.value.double_value = response_time
        point.interval.end_time.seconds = int(time.time())
        
        series.points = [point]
        self.client.create_time_series(
            name=self.project_name,
            time_series=[series]
        )
```

## 🔒 Seguridad y Mejores Prácticas

### Variables de Entorno (.env)
```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-app.run.app/webhook

# MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/pharmacy_bot
MONGODB_DB_NAME=pharmacy_bot

# Redis/Upstash
REDIS_URL=redis://default:pass@host:port

# Groq AI
GROQ_API_KEY=your_groq_api_key

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Configuración
ENVIRONMENT=production
LOG_LEVEL=INFO
CACHE_TTL=21600
RATE_LIMIT_PER_MINUTE=10
```

### Validación de Inputs
```python
from pydantic import BaseModel, validator

class SearchQuery(BaseModel):
    query: str
    user_id: int
    
    @validator('query')
    def validate_query(cls, v):
        if len(v) < 3:
            raise ValueError('Query muy corta')
        if len(v) > 100:
            raise ValueError('Query muy larga')
        # Sanitizar caracteres especiales
        return v.strip().lower()
```

### Rate Limiting por Usuario
```python
@rate_limit(max_calls=10, period=60)
async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador con rate limiting"""
    user_id = update.effective_user.id
    
    if not await rate_limiter.check_limit(user_id):
        await update.message.reply_text(
            "⚠️ Demasiadas búsquedas. Espera un minuto."
        )
        return
    
    # Procesar búsqueda
    await process_search(update, context)
```

## 📝 Plan de Implementación Detallado

### Fase 1: Setup Inicial (Día 1)
- [x] Crear estructura de directorios
- [ ] Configurar entorno virtual Python
- [ ] Instalar dependencias base
- [ ] Configurar MongoDB Atlas (crear cluster)
- [ ] Configurar Upstash Redis
- [ ] Obtener API keys (Telegram, Groq)
- [ ] Configurar variables de entorno
- [ ] Setup logging básico

### Fase 2: Base de Datos (Día 1-2)
- [ ] Diseñar esquemas MongoDB
- [ ] Crear modelos Pydantic
- [ ] Implementar MongoDB client
- [ ] Crear repositorios de datos
- [ ] Implementar índices y TTL
- [ ] Seed data inicial (farmacias)
- [ ] Tests de base de datos

### Fase 3: Web Scrapers (Día 2-4)
- [ ] Implementar clase base `BaseScraper`
- [ ] Desarrollar `CruzVerdeScraper`
  - [ ] Investigar estructura HTML
  - [ ] Implementar búsqueda
  - [ ] Extraer precios y stock
  - [ ] Manejo de errores
- [ ] Desarrollar `SalcobrandScraper`
  - [ ] Setup Selenium
  - [ ] Implementar búsqueda
  - [ ] Extraer datos dinámicos
- [ ] Desarrollar `AhumadaScraper`
  - [ ] Investigar API/HTML
  - [ ] Implementar búsqueda
  - [ ] Extraer información
- [ ] Implementar `ScraperManager`
- [ ] Tests de scrapers
- [ ] Optimizar rendimiento

### Fase 4: Servicios Core (Día 4-5)
- [ ] Implementar `CacheService`
  - [ ] Conexión Redis/Upstash
  - [ ] Métodos get/set/invalidate
  - [ ] TTL management
- [ ] Implementar `AIService`
  - [ ] Integración Groq
  - [ ] Normalización de queries
  - [ ] Corrección de errores
  - [ ] Sugerencias inteligentes
- [ ] Implementar `ComparisonService`
  - [ ] Lógica de comparación
  - [ ] Ranking de precios
  - [ ] Cálculo de ahorros
- [ ] Implementar `AnalyticsService`
  - [ ] Registro de búsquedas
  - [ ] Métricas de uso
  - [ ] Estadísticas

### Fase 5: Bot de Telegram (Día 5-6)
- [ ] Configurar bot con BotFather
- [ ] Implementar estructura base
- [ ] Comando `/start`
  - [ ] Mensaje de bienvenida
  - [ ] Registro de usuario
- [ ] Comando `/buscar`
  - [ ] Parser de argumentos
  - [ ] Integración con scrapers
  - [ ] Formateo de resultados
  - [ ] Teclados inline
- [ ] Comando `/ayuda`
- [ ] Comando `/acerca`
- [ ] Middleware:
  - [ ] Rate limiting
  - [ ] Logging
  - [ ] Error handling
- [ ] Teclados inline interactivos

### Fase 6: Testing (Día 6-7)
- [ ] Tests unitarios scrapers
- [ ] Tests servicios
- [ ] Tests bot handlers
- [ ] Tests de integración
- [ ] Tests de carga
- [ ] Corrección de bugs

### Fase 7: Despliegue (Día 7-8)
- [ ] Crear Dockerfile
- [ ] Configurar Cloud Build
- [ ] Setup Google Cloud Run
- [ ] Configurar webhooks
- [ ] Variables de entorno en Cloud
- [ ] Deploy inicial
- [ ] Pruebas en producción
- [ ] Monitoreo y logs

### Fase 8: Documentación (Día 8)
- [ ] README.md completo
- [ ] DEPLOYMENT.md
- [ ] Documentación API
- [ ] Guía de contribución
- [ ] Changelog

### Fase 9: Optimización (Día 9-10)
- [ ] Optimizar scrapers
- [ ] Mejorar cache strategy
- [ ] Reducir latencia
- [ ] Optimizar costos cloud
- [ ] Performance testing

### Fase 10: Lanzamiento (Día 10)
- [ ] Revisión final
- [ ] Lanzamiento beta
- [ ] Recolección de feedback
- [ ] Ajustes finales
- [ ] Lanzamiento público

## 🎯 Roadmap Futuro

### v1.1 (Mes 1-2)
- [ ] Alertas de precio por usuario
- [ ] Historial de precios con gráficos
- [ ] Búsqueda por principio activo
- [ ] Más farmacias (Dr. Simi, etc.)

### v1.2 (Mes 3-4)
- [ ] Geolocalización de farmacias
- [ ] Comparación de genéricos vs. comerciales
- [ ] Sistema de favoritos
- [ ] Compartir resultados

### v2.0 (Mes 5-6)
- [ ] Panel web de administración
- [ ] API REST pública
- [ ] App móvil nativa
- [ ] Integración con e-commerce

## 💰 Estimación de Costos (Mensual)

### Recursos Gratuitos
- Google Cloud Run: $0 (dentro de free tier)
- MongoDB Atlas: $0 (M0 cluster)
- Upstash Redis: $0 (free tier)
- Groq AI: $0 (free tier)
- **Total: $0/mes** 🎉

### Si se exceden límites gratuitos
- Cloud Run: ~$5-10/mes (1000 usuarios activos)
- MongoDB: ~$9/mes (M2 cluster)
- Redis: ~$10/mes (plan básico)
- **Total: ~$25-30/mes**

## 📞 Recursos y Enlaces

### Documentación
- [python-telegram-bot](https://docs.python-telegram-bot.org/)
- [MongoDB Atlas](https://www.mongodb.com/docs/atlas/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [Groq AI](https://console.groq.com/docs)
- [Upstash Redis](https://docs.upstash.com/redis)

### Herramientas
- [BotFather](https://t.me/botfather) - Crear bot de Telegram
- [MongoDB Compass](https://www.mongodb.com/products/compass) - GUI para MongoDB
- [Postman](https://www.postman.com/) - Testing de APIs

### Comunidad
- [Telegram Bot Developers](https://t.me/BotDevelopers)
- [Python Chile](https://t.me/PythonChile)

---

**Última actualización**: 2026-05-08  
**Versión**: 1.0  
**Estado**: ✅ Plan completo - Listo para implementación  
**Autor**: Equipo de Desarrollo  
**Licencia**: MIT