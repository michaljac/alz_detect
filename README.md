# Alzheimer's Prediction API

A FastAPI-based service for predicting Alzheimer's disease risk from patient clinical data using a **3-container Docker pipeline**.

![Model Comparison](readme_images/model_comparison.jpeg)

*Performance comparison between XGBoost and Logistic Regression models across different metrics including accuracy, precision, recall, and F1-score.*

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Architecture & Design

### Local (Docker)
- **Containers:** `alzearly-datagen`, `alzearly-train`, `alzearly-serve`
- **Flow:** data → `Data/featurized/` → train → `artifacts/latest/` → FastAPI serve
- **Run:** `docker compose up --build serve` → API at `localhost:8000`
  **Alternatives:**
  - **Windows (CMD):** `train.bat --serve` │ `--tracker mlflow` │ `--force-regen`
  - **Linux/Mac:** `./train.sh --serve` │ `./train.sh`
  - **PowerShell:** `.\train.ps1`


### Cloud (GCP)
- **Region:** `europe-west4` (Netherlands) for EU locality
- **Data:** GCS for Parquet + model artifacts; BigQuery external table over Parquet
- **Compute:**  
  - Cloud Run Jobs → run **datagen** + **train**, save outputs to GCS  
  - Cloud Run Service → runs FastAPI, loads latest model from GCS, auto-scales to zero
- **Tracking:** metrics + params saved with artifacts in GCS (optional: MLflow)

**Flows:**  
- **Local:** Docker volumes hold data + artifacts, FastAPI on port 8000  
- **Cloud:** Cloud Run Jobs produce data/models in GCS → BigQuery queries data → Cloud Run serves predictions


## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Quick Start

<div>

**One command to run the complete pipeline:**

**Windows:** `train.bat --serve`  
**Linux/Mac:** `./train.sh --serve`  
**PowerShell:** `.\train.ps1`

This automatically:
1. ✅ Generates data (if not exists)
2. ✅ Trains ML models with experiment tracking
3. ✅ Starts the API server

**Server will be available at:** `http://localhost:8000/docs`




## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Key area codes

<div>


**train.bat (Windows) - Smart Data Detection:**
```batch
REM Check if featurized data exists
set DATA_FOUND=false
if exist "%DATA_DIR%\featurized\*.parquet" set DATA_FOUND=true
if exist "%DATA_DIR%\featurized\*.csv" set DATA_FOUND=true

if "%DATA_FOUND%"=="false" (
    echo 🔄 Generating data using datagen container...
    docker run --rm -v "%CURRENT_DIR%:/workspace" -v "%DATA_DIR%:/Data" alzearly-datagen:latest
) else (
    echo ✅ Found existing featurized data
)
```

**train.sh (Linux/Mac) - Smart Data Detection:**
```bash
# Check if featurized data exists
if [ ! -f "$DATA_DIR/featurized"/*.parquet ] && [ ! -f "$DATA_DIR/featurized"/*.csv ]; then
    echo "🔄 Generating data using datagen container..."
    docker run --rm -v "$CURRENT_DIR:/workspace" -v "$DATA_DIR:/Data" alzearly-datagen:latest
else
    echo "✅ Found existing featurized data"
fi
```

**Cross-Platform Docker Commands:**
```bash
# Data generation (works on all platforms)
docker run --rm -v "$(pwd):/workspace" -v "$(pwd)/../Data/alzearly:/Data" alzearly-datagen:latest

# Training (works on all platforms)
docker run -it --rm -v "$(pwd):/workspace" -v "$(pwd)/../Data/alzearly:/Data" alzearly-train:latest python run_training.py

# Serving (works on all platforms)
docker run -it --rm -v "$(pwd):/workspace" -p 8000:8000 alzearly-serve:latest python run_serve.py
```



## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Manual Docker Commands

<div>

If you prefer to run containers individually:

### **Data Generation**

**Linux/Mac:**
```bash
docker run --rm -v "$(pwd):/workspace" -v "$(pwd)/../Data/alzearly:/Data" alzearly-datagen:latest
```

**Windows (PowerShell):**
```powershell
docker run --rm -v "${PWD}:/workspace" -v "${PWD}/../Data/alzearly:/Data" alzearly-datagen:latest
```

**Windows (CMD):**
```cmd
docker run --rm -v "%cd%:/workspace" -v "%cd%/../Data/alzearly:/Data" alzearly-datagen:latest
```

### **Training**

**Linux/Mac:**
```bash
docker run --rm -v "$(pwd):/workspace" -v "$(pwd)/../Data/alzearly:/Data" alzearly-train:latest
```

**Windows (PowerShell):**
```powershell
docker run --rm -v "${PWD}:/workspace" -v "${PWD}/../Data/alzearly:/Data" alzearly-train:latest
```

**Windows (CMD):**
```cmd
docker run --rm -v "%cd%:/workspace" -v "%cd%/../Data/alzearly:/Data" alzearly-train:latest
```

### **Serving**

**Linux/Mac:**
```bash
docker run --rm -v "$(pwd):/workspace" -p 8000:8000 alzearly-serve:latest
```

**Windows (PowerShell):**
```powershell
docker run --rm -v "${PWD}:/workspace" -p 8000:8000 alzearly-serve:latest
```

**Windows (CMD):**
```cmd
docker run --rm -v "%cd%:/workspace" -p 8000:8000 alzearly-serve:latest
```

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> API Endpoints

<div>

### **Main Endpoint: POST `/predict`**
**Check if a patient is at risk for Alzheimer's disease.**

**Request:**
```json
{
  "items": [
    {
      "age": 65.0, "bmi": 26.5, "systolic_bp": 140.0, "diastolic_bp": 85.0,
      "heart_rate": 72.0, "temperature": 37.0, "glucose": 95.0,
      "cholesterol_total": 200.0, "hdl": 45.0, "ldl": 130.0, "triglycerides": 150.0,
      "creatinine": 1.2, "hemoglobin": 14.5, "white_blood_cells": 7.5, "platelets": 250.0,
      "num_encounters": 3, "num_medications": 2, "num_lab_tests": 5
    }
  ]
}
```

**Response:**
```json
{
  "predictions": [
    {
      "probability": 0.75,  // Risk score (0.0 = no risk, 1.0 = high risk)
      "label": 1            // 0 = low risk, 1 = high risk
    }
  ]
}
```

### **Other Endpoints:**
- **GET `/health`** - Service health check
- **GET `/version`** - Model version info
- **GET `/docs`** - Interactive API documentation
- **GET `/`** - API information

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> ML Pipeline & Technical Decisions

<div>

### **Core Architecture:**
- **Patient-level splits** → Prevents data leakage
- **Feature engineering** → Temporal aggregations (mean, std, min, max, count)
- **Two-stage feature selection** → Variance threshold + XGBoost importance
- **Optimized models** → XGBoost (50 trees, hist method) + Logistic Regression (liblinear solver)

### **Key Design Decisions:**

**Why Class Weight Over SMOTE?**
```python
# Applied during model training - no data leakage
params['class_weight'] = 'balanced'  # For Logistic Regression
scale_pos_weight = neg_count / pos_count  # For XGBoost
```
✅ **No data leakage** - Doesn't create synthetic samples in validation/test sets  
✅ **Computational efficiency** - No additional preprocessing overhead  
✅ **Production stability** - Preserves original data distribution

**Why Patient-Level Splitting?**
```python
# Prevents data leakage by keeping all records from same patient together
train_patients, val_patients = train_test_split(
    unique_patients, test_size=0.2, stratify=patient_labels
)
```
🚫 **Prevents leakage** - Patient's future data won't leak into training set  
📊 **Realistic evaluation** - Simulates real-world deployment scenarios

**Performance Optimizations:**
- **Conditional data cleaning** → Only processes data if NaN values exist
- **Optimized hyperparameters** → 2x faster training while maintaining accuracy
- **Efficient feature selection** → Reduces training time by 50-70%

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Testing the API

<div>

**Easiest way:** Visit `http://localhost:8000/docs` for interactive testing

**Quick test with curl:**
```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"items":[{"age":65.0,"bmi":26.5,"systolic_bp":140.0,"diastolic_bp":85.0,"heart_rate":72.0,"temperature":37.0,"glucose":95.0,"cholesterol_total":200.0,"hdl":45.0,"ldl":130.0,"triglycerides":150.0,"creatinine":1.2,"hemoglobin":14.5,"white_blood_cells":7.5,"platelets":250.0,"num_encounters":3,"num_medications":2,"num_lab_tests":5}]}'
```

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Required Patient Data Fields

<div>

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `age` | float | 0-120 | Patient age |
| `bmi` | float | 10-100 | Body mass index |
| `systolic_bp` | float | 50-300 | Systolic blood pressure |
| `diastolic_bp` | float | 30-200 | Diastolic blood pressure |
| `heart_rate` | float | 30-200 | Heart rate |
| `temperature` | float | 35-42 | Body temperature (Celsius) |
| `glucose` | float | 20-1000 | Blood glucose level |
| `cholesterol_total` | float | 50-500 | Total cholesterol |
| `hdl` | float | 10-200 | HDL cholesterol |
| `ldl` | float | 10-300 | LDL cholesterol |
| `triglycerides` | float | 10-1000 | Triglycerides |
| `creatinine` | float | 0.1-20 | Creatinine level |
| `hemoglobin` | float | 5-25 | Hemoglobin level |
| `white_blood_cells` | float | 1-50 | White blood cell count |
| `platelets` | float | 50-1000 | Platelet count |
| `num_encounters` | int | ≥0 | Number of healthcare encounters |
| `num_medications` | int | ≥0 | Number of medications |
| `num_lab_tests` | int | ≥0 | Number of lab tests |

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Docker Setup & Requirements

<div>

### **Prerequisites**
- **Docker**: Version 20.10+ with Docker Compose
- **Disk Space**: ~2GB for containers and data
- **Memory**: 4GB+ recommended for training

### **Building Docker Images**

**Linux/Mac:**
```bash
# Build all containers
docker build --network=host -f Dockerfile.datagen -t alzearly-datagen .
docker build --network=host -f Dockerfile.train -t alzearly-train .
docker build --network=host -f Dockerfile.serve -t alzearly-serve .
```

**Windows (PowerShell):**
```powershell
# Build all containers
docker build -f Dockerfile.datagen -t alzearly-datagen .
docker build -f Dockerfile.train -t alzearly-train .
docker build -f Dockerfile.serve -t alzearly-serve .
```

**Windows (CMD):**
```cmd
# Build all containers
docker build -f Dockerfile.datagen -t alzearly-datagen .
docker build -f Dockerfile.train -t alzearly-train .
docker build -f Dockerfile.serve -t alzearly-serve .
```

### **Container Specifications**
| Container | Base Image | Purpose | Key Dependencies |
|-----------|------------|---------|------------------|
| `alzearly-datagen` | Python 3.10-slim | Data generation & preprocessing | pandas, polars, numpy |
| `alzearly-train` | Python 3.10-slim | ML training & experiment tracking | xgboost, sklearn, mlflow |
| `alzearly-serve` | Python 3.10-slim-bullseye | API serving | fastapi, uvicorn, pydantic |

### **Volume Mounts**

**Linux/Mac:**
```bash
# Data persistence
-v "$(pwd):/workspace"           # Project code
-v "$(pwd)/../Data/alzearly:/Data"  # Data storage

# Port mapping (for serving)
-p 8000:8000                     # API server
```

**Windows (PowerShell):**
```powershell
# Data persistence
-v "${PWD}:/workspace"           # Project code
-v "${PWD}/../Data/alzearly:/Data"  # Data storage

# Port mapping (for serving)
-p 8000:8000                     # API server
```

**Windows (CMD):**
```cmd
# Data persistence
-v "%cd%:/workspace"             # Project code
-v "%cd%/../Data/alzearly:/Data" # Data storage

# Port mapping (for serving)
-p 8000:8000                     # API server
-p 8000:8000                     # Alternative port
```

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Key Configuration Parameters

<div>

### **Data Generation (`config/data_gen.yaml`)**
```yaml
dataset:
  n_patients: 3000          # Number of patients to generate
  years: [2021, 2022, 2023, 2024]  # Years to generate data for
  positive_rate: 0.08       # Alzheimer's positive rate (5-10% recommended)
```

### **Model Training (`config/model.yaml`)**
```yaml
xgboost:
  n_estimators: 50          # Number of trees (optimized for speed)
  max_depth: 4              # Tree depth (prevents overfitting)
  learning_rate: 0.2        # Learning rate (faster convergence)
  tree_method: "hist"       # Tree building algorithm (2-3x faster)

class_imbalance:
  method: "class_weight"    # Options: "class_weight", "smote", "none"
```

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Technical Deep Dive

<div>

### **Core Technologies & Libraries**
- **🤖 ML Stack**: XGBoost, Scikit-learn, NumPy/Pandas, Polars
- **📊 MLOps**: MLflow, Weights & Biases, Pydantic, FastAPI
- **🐳 DevOps**: Docker, Volume Mounts, Environment Variables

### **Critical Parameters Explained**

| Parameter | Default | Impact | When to Change |
|-----------|---------|--------|----------------|
| `n_patients` | 3000 | Dataset size & training time | **Increase** for better performance<br>**Decrease** for faster iteration |
| `positive_rate` | 0.08 | Class balance | **Increase** for more positive cases<br>**Decrease** for rare disease simulation |
| `n_estimators` | 50 | Training speed vs accuracy | **Increase** for better performance<br>**Decrease** for faster training |

### **Performance vs. Accuracy Trade-offs**
```yaml
# Fast Training (current settings)
xgboost:
  n_estimators: 50      # 2x faster than default
  max_depth: 4          # Prevents overfitting
  learning_rate: 0.2    # Faster convergence

# High Accuracy (production settings)
xgboost:
  n_estimators: 200     # More trees for better performance
  max_depth: 6          # Capture more complex patterns
  learning_rate: 0.1    # More stable training
```

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Important Notes

<div>

1. **Model Requirements**: The server requires trained model artifacts in `artifacts/latest/` directory
2. **Medical Disclaimer**: This is a research tool and should not be used for clinical diagnosis
3. **Port Conflicts**: The server automatically finds available ports to avoid conflicts

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Troubleshooting

<div>

### **Common Issues:**
- **Port Already in Use**: Let server auto-find port or specify: `python run_serve.py --port 8005`
- **Model Not Found**: Ensure training completed and `artifacts/latest/` exists
- **YAML/PyYAML Issues**: Docker containers handle dependencies automatically

### **Docker Dependencies:**
All Python dependencies (including PyYAML) are pre-installed in Docker containers. No manual installation required.

### **Platform Compatibility:**
- **Windows**: Use `train.bat` script (Windows batch file)
- **Linux/Mac**: Use `train.sh` script (Bash script)
- **Cross-platform**: Use manual Docker commands (works on all platforms)
- **Docker commands**: Use `$(pwd)` for Linux/Mac, `${PWD}` for PowerShell, `%cd%` for CMD

### **Platform-Specific Commands:**

**Check Docker Status:**
```bash
# Linux/Mac
docker --version
docker ps

# Windows (PowerShell/CMD)
docker --version
docker ps
```

**Clean Docker Resources:**
```bash
# Linux/Mac
docker system prune -f
docker volume prune -f

# Windows (PowerShell/CMD)
docker system prune -f
docker volume prune -f
```

**Check Container Logs:**
```bash
# Linux/Mac
docker logs <container_name>

# Windows (PowerShell/CMD)
docker logs <container_name>
```

</div>
</div>

## <img src="readme_images/hippo.jpeg" width="20" height="20" style="vertical-align: middle; margin-right: 8px;"> Related Files

<div>

- `run_serve.py` - Main server script
- `artifacts/latest/` - Trained model and metadata
- `requirements.txt` - Python dependencies
- `config/` - Configuration files directory
- `src/config.py` - Configuration management system

</div>
</div>

</div>
</div>
