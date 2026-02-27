# SPIS-ML | Seismic Performance Intelligent System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Dash](https://img.shields.io/badge/Dash-2.0+-green.svg)](https://dash.plotly.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌍 Descripción

**SPIS-ML** es una plataforma académica avanzada para exploración, modelado y comunicación de información sísmica. El sistema integra técnicas de machine learning, análisis estadístico y visualización interactiva para facilitar el estudio y comprensión de la actividad sísmica global.

### ✨ Características Principales

- **🏠 Monitoreo en Tiempo Real**: Integración con USGS para datos sísmicos actualizados automáticamente
- **🗺️ Exploración Geográfica**: Visualización interactiva de eventos sísmicos en mapas globales
- **📊 Análisis Gutenberg-Richter**: Modelado estadístico de la relación magnitud-frecuencia
- **📈 Regresión Logarítmica**: Análisis predictivo de patrones sísmicos
- **🧠 LSTM Prediction**: Red neuronal para predicción de secuencias temporales
- **🔄 Comparativa de Modelos**: Evaluación y comparación de múltiples metodologías
- **🎯 Análisis de Densidad**: Identificación de zonas de alta actividad sísmica
- **📋 Reportes Gerenciales**: Generación automática de informes ejecutivos (PDF/CSV)
- **📚 Glosario Académico**: Base de conocimiento técnico curado

## 🛠️ Tecnologías

- **Backend**: Python 3.8+
- **Frontend**: Dash + Plotly
- **UI Framework**: Dash Bootstrap Components
- **Data Science**: Pandas, NumPy, Scikit-learn
- **Machine Learning**: TensorFlow/Keras (LSTM)
- **Visualización**: Plotly Express, Matplotlib
- **Reportes**: FPDF, Plotly Kaleido

## 🚀 Instalación

### Prerrequisitos

```bash
# Python 3.8 o superior
python --version

# Git
git --version
```

### Configuración del Entorno

1. **Clonar el repositorio**
```bash
git clone https://github.com/feliperivasdev/SPIS-ML.git
cd SPIS-ML/dashboard
```

2. **Crear entorno virtual**
```bash
# Windows
python -m venv sismos_dashboard
sismos_dashboard\Scripts\activate

# Linux/macOS
python3 -m venv sismos_dashboard
source sismos_dashboard/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

## 📱 Uso

### Inicio Rápido

1. **Ejecutar la aplicación**
```bash
python app.py
```

2. **Acceder a la interfaz**
   - Abrir navegador en: `http://127.0.0.1:8050/`

3. **Cargar dataset**
   - Usar la zona de carga en la pantalla principal
   - Formatos soportados: CSV con columnas estándar de catálogos sísmicos
   - El sistema incluye preprocesamiento automático

### Estructura de Datos Esperada

El CSV debe contener las siguientes columnas mínimas:
```
time, latitude, longitude, depth, mag
```

**Ejemplo:**
```csv
time,latitude,longitude,depth,mag
2024-01-15T10:30:00.000Z,-33.4489,70.6693,25.5,4.2
2024-01-15T15:45:30.000Z,-36.8485,73.0544,15.2,3.8
```

## 🏗️ Arquitectura del Sistema

```
dashboard/
├── app.py                 # Aplicación principal Dash
├── preprocessor.py        # Limpieza y procesamiento de datos
├── requirements.txt       # Dependencias del proyecto
├── modules/              # Módulos de análisis
│   ├── data_handler.py           # Gestión de datos
│   ├── home_module.py            # Página principal y monitoreo
│   ├── exploration_module.py     # Exploración geográfica
│   ├── model_Gutenberg_Richter_module.py
│   ├── model_log_regression_module.py
│   ├── model_lstm_prediction_module.py
│   ├── model_comparison_module.py
│   ├── density_module.py         # Análisis de densidad
│   └── reports_module.py         # Generación de reportes
├── assets/               # Recursos estáticos (CSS)
├── data/                # Datasets procesados
└── templates/           # Plantillas adicionales
```

## 📊 Módulos de Análisis

### 1. **Exploración Geográfica**
- Mapas interactivos con filtrado dinámico
- Visualización por magnitud, profundidad y tiempo
- Herramientas de zoom y selección regional

### 2. **Gutenberg-Richter**
- Cálculo automático de parámetros a y b
- Visualización de ajuste log-lineal
- Análisis de completitud del catálogo

### 3. **Regresión Logarítmica**
- Modelado predictivo de magnitudes
- Evaluación de métricas (R², RMSE, MAE)
- Gráficos de residuos y predicción vs observado

### 4. **LSTM Prediction**
- Red neuronal recurrente para series temporales
- Predicción de secuencias de magnitudes
- Arquitectura configurable

### 5. **Comparativa de Modelos**
- Evaluación simultánea de múltiples algoritmos
- Métricas comparativas de rendimiento
- Selección automática del mejor modelo

### 6. **Análisis de Densidad**
- Mapas de calor de actividad sísmica
- Identificación de clusters espaciales
- Análisis de distribución temporal

### 7. **Reportes Gerenciales**
- Informes ejecutivos automáticos (PDF)
- Exportación de datos filtrados (CSV)
- Dashboards con KPIs principales

## 🌐 API y Datos Externos

- **USGS Earthquake API**: Monitoreo en tiempo real
- **Formato GeoJSON**: Compatible con estándares internacionales
- **Actualización automática**: Cada 60 segundos en el dashboard principal

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Opcional: Puerto personalizado
export DASH_PORT=8050

# Opcional: Modo debug
export DASH_DEBUG=True
```

### Personalización

- **Temas**: Modificar `assets/style.css` para personalizar la UI
- **Parámetros**: Ajustar constantes en cada módulo según necesidades
- **Modelos ML**: Entrenar con datasets específicos en `modules/`

## 🧪 Testing

```bash
# Ejecutar tests unitarios (cuando estén disponibles)
python -m pytest tests/

# Validación de datos de ejemplo
python preprocessor.py --validate data/example.csv
```

## 📈 Roadmap

- [ ] Integración con más fuentes de datos sísmicos (EMSC, GEOFON)
- [ ] Análisis de series temporales avanzado (ARIMA, Prophet)
- [ ] Módulo de alerta temprana
- [ ] API REST para integración externa
- [ ] Soporte para múltiples idiomas
- [ ] Análisis de vulnerabilidad sísmica urbana

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

### Guías de Contribución

- Mantener estilo PEP 8
- Incluir docstrings en funciones nuevas
- Añadir tests para nuevas funcionalidades
- Documentar cambios importantes en el changelog

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Desarrollador

**Felipe Rivas**
- GitHub: [@feliperivasdev](https://github.com/feliperivasdev)
- Email: [davidfe.gustin@gmail.com](mailto:davidfe.gustin@gmail.com)

## 🙏 Agradecimientos

- **USGS Earthquake Hazards Program** por los datos en tiempo real
- **Dash/Plotly Community** por la excelente documentación
- **Comunidad científica sismológica** por los métodos y estándares

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/feliperivasdev/SPIS-ML/issues)
- **Documentación**: [Wiki del proyecto](https://github.com/feliperivasdev/SPIS-ML/wiki)
- **Email**: [davidfe.gustin@gmail.com](mailto:davidfe.gustin@gmail.com)

---

<div align="center">

**SPIS-ML** - *Democratizando el análisis sísmico a través de tecnología inteligente*

[![GitHub stars](https://img.shields.io/github/stars/feliperivasdev/SPIS-ML.svg)](https://github.com/feliperivasdev/SPIS-ML/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/feliperivasdev/SPIS-ML.svg)](https://github.com/feliperivasdev/SPIS-ML/network)

</div>
