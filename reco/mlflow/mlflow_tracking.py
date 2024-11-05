import mlflow
import mlflow.sklearn
from src.models.train_model import train_model
from src.models.evaluate_model import evaluate_model

def train_and_log_model():
    with mlflow.start_run():
        model = train_model()
        mlflow.sklearn.log_model(model, "model")
        metrics = evaluate_model(model)
        for key, value in metrics.items():
            mlflow.log_metric(key, value)

if __name__ == "__main__":
    train_and_log_model()
