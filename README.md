
# 🎬🎞📶 Movie Recommendation System 

This project was created as part of the MLOps bootcamp (Sep24) 🛠👷🏻‍♂️. The project was used to try out different tools that can be used to deploy ML projects.


## 💻 Developer Team:
- Asma Heena Khalil
- Ringo Schwabe 
- Carolin Stolpe ([@castolpe](https://github.com/castolpe))

## Business Objectives

The Movie Recommendation application addresses the challenge of providing personalized movie recommendations to users on a streaming platform. By leveraging collaborative filtering techniques, it enhances the user experience by suggesting movies that align with individual tastes. Sponsored by a streaming service, the project aims to improve user engagement and satisfaction through tailored content.

## App Architecture

## File structure
```
├── .dvc                     <- Configuration of the data version control
├── .github
│   └── workflows            <- Github Actions to trigger CI/CD pipeline and data pipeline 
│ 
├── data
│   ├── interim              <- Intermediate data that has been transformed.
│   ├── processed            <- The final, canonical data sets for modeling.
│   ├── raw                  <- The original, immutable data dump.
│   └── status.txt           <- Indicator, if current data is valid.
│
├── logs                     <- Logs from training and predicting
│
├── metrics                  <- Metrics from the evaluated model.
│ 
├── models                   <- Trained and serialized models, model predictions, or model summaries
│
├── monitoring               <- All files related to the monitoring of the application.
│   ├── alertmanager         <- Configuration of the alert manager to inform in the event of deviations. 
│   ├── grafana              <- Configuration of the Grafana dashboard to visualize the metrics collected by Prometheus.
│   └── prometheues          <- Configuration to collect metrics about the health status of the app, number of requests etc.
│
├── notebooks                <- Jupyter notebooks. Naming convention is a number (for ordering),
│                               the creator's initials, and a short `-` delimited description, e.g.
│                               `1.0-jqp-initial-data-exploration`.
│
├── references               <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports                  <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures              <- Generated graphics and figures to be used in reporting
│
├── src                      <- Source code for use in this project.
│   ├── api                  <- Definiton of API endpoints
│   ├── data_module_def      <- Scripts to download, validate and transform data
│   ├── models_module_def    <- Scripts to train models and then use trained models to make
│   │                           predictions
│   ├── pipeline_steps       <- Scripts for the single pipeline_steps from data download to model evaluation
│   ├── utils                <- Helper functions and other utils (e.g. logger)
│   ├── visualization        <- Scripts to create exploratory and results oriented visualizations
│   │   └── visualize.py
│   ├── config_manager.py    <- Create configuration objects for each of the stages
│   ├── config.py            <- Paths to the config files
│   ├── config.yaml          <- Values for the required configuration fields 
│   └── entity.py            <- Definition of the config fields
│   dvc.lock                 <- Locks of the last pipeline run
│   dvc.yaml                 <- Orchestration of pipeline steps (DAG).
├── LICENSE
├── README.md                <- The top-level README for developers using this project.
└── requirements.txt         <- The requirements file for reproducing the analysis environment, e.g.
                                generated with `pip freeze > requirements.txt`
```

## Getting Started

To run the app locally follow these steps:

### 1. Clone the project
```
git clone https://github.com/DataScientest-Studio/sep24_bmlops_int_reco_films.git
cd /sep24_bmlops_int_reco_films
```

### 2. Setup virtual environment & install dependencies
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Download data from remote storage
Data, metrics and models are stored on Dagshub Remote Storage using DVC. Make sure to download 
the data before running the app.
```
# Configure access to DVC
dvc remote modify origin --local access_key_id YOUR_DVC_ACCESS_KEY
dvc remote modify origin --local secret_access_key YOUR_DVC_ACCESS_KEY

# Pull the data
dvc pull
```

### 4. Build the Docker 🐳 container and launch the app
```
docker-compose up
```

### 5. Query the endpoints
```
# Check, if API is running
curl -X GET i http://0.0.0.0:8000/status

# Read the API docs
curl -X GET i http://0.0.0.0:8000/docs

# Get movie recommendation
curl -X 'POST' \
  'http://localhost:8000/users/recommendations' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "no_genres_listed": 0,
  "action": 0,
  "adventure": 0,
  "animation": 5,
  "children": 3,
  "comedy": 2,
  "crime": 0,
  "documentary": 0,
  "drama": 0,
  "fantasy": 0,
  "film_noir": 0,
  "horror": 0,
  "imax": 0,
  "musical": 0,
  "mystery": 0,
  "romance": 0,
  "sci_fi": 0,
  "thriller": 0,
  "war": 0,
  "western": 0
}'

```

### 6. Checkout the monitoring dashboard

➡ Go to http://localhost:3000/d/_eX4mpl3/fastapi-dashboard in your web browser.
