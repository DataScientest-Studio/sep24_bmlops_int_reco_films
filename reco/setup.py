from setuptools import find_packages, setup

setup(
    name='movie_recommendation_mlops',
    packages=find_packages(),
    version='0.1.0',
    description="Comprehensive Movie Recommendation System with MLOps practices.",
    author='Your Name',
    license='MIT',
    install_requires=[
        # Add your project's dependencies here
        'pandas',
        'numpy',
        'scikit-learn',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'apache-airflow',
        'mlflow',
        'dvc',
        'prometheus-client',
        'grafana-api',
        'pytest',
        'docker',
        'kubernetes',
        'python-dotenv',
        'pyyaml',
        'matplotlib',
    ],
)



# setup.py

from setuptools import find_packages, setup

setup(
    name='movie_recommendation_mlops',
    version='0.1.0',
    description='A movie recommendation system with MLOps practices',
    author='Your Name',
    author_email='youremail@example.com',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'scikit-learn',
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        # Add other dependencies as needed
    ],
)
