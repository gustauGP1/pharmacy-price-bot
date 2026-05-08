# 🏥 Pharmacy Price Bot - Comparador de Precios de Farmacias Chile

Bot de Telegram que compara precios de medicamentos entre las principales farmacias de Chile usando web scraping e inteligencia artificial.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green.svg)](https://www.mongodb.com/atlas)
[![Google Cloud](https://img.shields.io/badge/Google-Cloud%20Run-blue.svg)](https://cloud.google.com/run)

## 🎯 Características

- 🔍 **Búsqueda inteligente** con IA (Groq/Llama 3)
- 💰 **Comparación de precios** en tiempo real
- 🏪 **3 Farmacias principales**: Cruz Verde, Salcobrand, Farmacias Ahumada
- ⚡ **Cache inteligente** con Redis (6 horas TTL)
- 📊 **Analytics** y métricas de uso
- 🌐 **100% Cloud** con recursos gratuitos
- 🚀 **Despliegue automático** con Google Cloud Run

## 📋 Requisitos Previos

- Python 3.11 o superior
- Cuenta de Telegram
- Git instalado
- Cuentas gratuitas en:
  - [MongoDB Atlas](https://www.mongodb.com/atlas)
  - [Upstash Redis](https://upstash.com/)
  - [Groq AI](https://console.groq.com/)
  - [Google Cloud Platform](https://cloud.google.com/)

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio

```bash
# Clonar desde GitHub
git clone https://github.com/tu-usuario/pharmacy-price-bot.git
cd pharmacy-price-bot

# O si estás empezando desde cero
cd C:\proyectos\pharmacy-price-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/tu-usuario/pharmacy-price-bot.git
git push -u origin main
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_WEBHOOK_URL=https://tu-app.run.app/webhook

# MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/pharmacy_bot
MONGODB_DB_NAME=pharmacy_bot

# Redis/Upstash
REDIS_URL=redis://default:pass@host:port

# Groq AI
GROQ_API_KEY=tu_groq_api_key

# Configuración
ENVIRONMENT=development
LOG_LEVEL=INFO
CACHE_TTL=21600
RATE_LIMIT_PER_MINUTE=10
```

### 5. Ejecutar Localmente

```bash
# Modo desarrollo (polling)
python run.py

# O con Flask para webhooks
python bot/main.py
```

## 📦 Estructura del Proyecto

```
pharmacy-price-bot/
├── 📂 bot/                    # Lógica del bot de Telegram
│   ├── main.py               # Punto de entrada
│   ├── handlers.py           # Manejadores de comandos
│   ├── keyboards.py          # Teclados inline
│   └── middleware.py         # Rate limiting, logging
│
├── 📂 scrapers/              # Web scrapers
│   ├── base_scraper.py       # Clase base
│   ├── cruz_verde_scraper.py
│   ├── salcobrand_scraper.py
│   └── ahumada_scraper.py
│
├── 📂 database/              # Capa de datos
│   ├── mongodb_client.py     # Cliente MongoDB
│   ├── models.py             # Modelos Pydantic
│   └── repositories.py       # Repositorios
│
├── 📂 services/              # Servicios de negocio
│   ├── cache_service.py      # Cache Redis
│   ├── ai_service.py         # Integración Groq
│   ├── comparison_service.py # Comparación de precios
│   └── analytics_service.py  # Métricas
│
├── 📂 utils/                 # Utilidades
│   ├── logger.py
│   ├── validators.py
│   └── formatters.py
│
├── 📂 config/                # Configuración
│   └── settings.py
│
├── 📂 tests/                 # Tests
│   ├── test_scrapers.py
│   └── test_bot.py
│
├── 📂 deployment/            # Despliegue
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   └── app.yaml
│
├── .env.example              # Plantilla de variables
├── .gitignore
├── requirements.txt
├── PLAN.md                   # Plan detallado
└── README.md
```

## 🤖 Comandos del Bot

### Comandos Disponibles

- `/start` - Mensaje de bienvenida y guía rápida
- `/buscar [medicamento]` - Buscar y comparar precios
- `/ayuda` - Mostrar ayuda detallada
- `/acerca` - Información sobre el bot

### Ejemplos de Uso

```
/buscar paracetamol
/buscar ibuprofeno 400mg
/buscar aspirina
```

## 🔧 Configuración de Servicios Cloud

### 1. Crear Bot de Telegram

1. Habla con [@BotFather](https://t.me/botfather)
2. Envía `/newbot`
3. Sigue las instrucciones
4. Copia el token y agrégalo a `.env`

### 2. MongoDB Atlas (Gratis)

1. Crea cuenta en [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Crea un cluster M0 (gratis)
3. Configura acceso de red (0.0.0.0/0 para desarrollo)
4. Crea usuario de base de datos
5. Obtén la URI de conexión
6. Agrégala a `.env`

### 3. Upstash Redis (Gratis)

1. Crea cuenta en [Upstash](https://upstash.com/)
2. Crea una base de datos Redis
3. Copia la URL de conexión
4. Agrégala a `.env`

### 4. Groq AI (Gratis)

1. Crea cuenta en [Groq Console](https://console.groq.com/)
2. Genera una API key
3. Agrégala a `.env`

### 5. Google Cloud Run (Gratis)

Ver [DEPLOYMENT.md](DEPLOYMENT.md) para instrucciones detalladas.

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html

# Tests específicos
pytest tests/test_scrapers.py
pytest tests/test_bot.py -v
```

## 📊 Monitoreo

### Logs Locales

```bash
# Ver logs en tiempo real
tail -f logs/bot.log

# Buscar errores
grep ERROR logs/bot.log
```

### Métricas en Producción

- Google Cloud Console: Logs y métricas
- MongoDB Atlas: Queries y performance
- Upstash: Redis metrics

## 🚀 Despliegue

### Despliegue Local

```bash
python run.py
```

### Despliegue en Google Cloud Run

```bash
# Autenticar
gcloud auth login

# Configurar proyecto
gcloud config set project tu-proyecto-id

# Deploy
gcloud run deploy pharmacy-bot \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
```

Ver [DEPLOYMENT.md](DEPLOYMENT.md) para más detalles.

## 🔐 Seguridad

- ✅ Variables de entorno para secretos
- ✅ Rate limiting por usuario
- ✅ Validación de inputs
- ✅ HTTPS obligatorio en producción
- ✅ Logs sin información sensible

## 📈 Roadmap

### v1.0 (Actual)
- [x] Búsqueda básica de medicamentos
- [x] Comparación de 3 farmacias
- [x] Cache inteligente
- [x] IA para búsquedas

### v1.1 (Próximo)
- [ ] Alertas de precio
- [ ] Historial de precios
- [ ] Más farmacias
- [ ] Geolocalización

### v2.0 (Futuro)
- [ ] Panel web
- [ ] API REST pública
- [ ] App móvil

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Guías de Contribución

- Sigue PEP 8 para código Python
- Agrega tests para nuevas funcionalidades
- Actualiza la documentación
- Usa commits descriptivos

## 📝 Changelog

### [1.0.0] - 2026-05-08
- ✨ Lanzamiento inicial
- 🔍 Búsqueda en 3 farmacias
- 🤖 Integración con IA
- 💾 Cache con Redis
- 📊 Analytics básico

## 💰 Costos

### Tier Gratuito (Recomendado)
- Google Cloud Run: $0/mes (2M peticiones)
- MongoDB Atlas: $0/mes (512MB)
- Upstash Redis: $0/mes (10K comandos/día)
- Groq AI: $0/mes (14.4K peticiones/día)
- **Total: $0/mes** 🎉

### Si excedes límites
- ~$25-30/mes para 1000+ usuarios activos

## 📞 Soporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/tu-usuario/pharmacy-price-bot/issues)
- 💬 **Telegram**: [@tu_usuario](https://t.me/tu_usuario)
- 📧 **Email**: tu-email@ejemplo.com

## 📄 Licencia

Este proyecto está bajo **Licencia Propietaria** de GP1 DevStudio.
Copyright © 2026 Gustavo Palma Rodríguez - Todos los derechos reservados.

Ver [LICENSE](LICENSE) para términos y condiciones completos.

**Contacto para licencias comerciales**: gp1devstudio@gmail.com

## 🙏 Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Groq AI](https://groq.com/)
- [MongoDB Atlas](https://www.mongodb.com/atlas)
- [Upstash](https://upstash.com/)
- [Google Cloud](https://cloud.google.com/)

## ⚠️ Disclaimer

Este bot es solo para fines educativos y de comparación de precios. No almacenamos información personal de los usuarios. Los precios mostrados son referenciales y pueden variar. Siempre verifica los precios en el sitio oficial de cada farmacia antes de comprar.

---

**Desarrollado con ❤️ en Chile** 🇨🇱

**Última actualización**: 2026-05-08