Movie Recommendation System (MLOps exercise project)
====================================================

This project was created as part of the MLOps boot camp. The project was used to try out many tools that can be used to deploy ML projects.

**Developer Team**
- Asma Heena Khalil
- Ringo Schwabe 
- Carolin Stolpe [@castolpe](https://github.com/castolpe)

Business Objectives
------------------

The Movie Recommendation application addresses the challenge of providing personalized movie recommendations to users on a streaming platform. By leveraging collaborative filtering techniques, it enhances the user experience by suggesting movies that align with individual tastes. Sponsored by a streaming service, the project aims to improve user engagement and satisfaction through tailored content.

Architecture
------------


File structure
------------
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
--------

## How to run locally

xxx

# Notes

Start API locally:

`fastapi dev .\src\api\main.py`
