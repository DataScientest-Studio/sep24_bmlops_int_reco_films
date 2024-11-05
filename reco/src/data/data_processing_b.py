import pandas as pd
import logging
from sqlalchemy.orm import Session
from src.data.database import Movie, Rating, Link, Tag, GenomeScore, GenomeTag

logger = logging.getLogger(__name__)

def process_and_store_data(session: Session, movies_file: str, ratings_file: str, links_file: str, tags_file: str, genome_tags_file: str, genome_scores_file: str):
    logger.info("Processing and storing movies data")
    movies_df = pd.read_csv(movies_file)
    for _, row in movies_df.iterrows():
        movie = Movie(movieId=row['movieId'], title=row['title'], genres=row['genres'])
        session.add(movie)

    logger.info("Processing and storing ratings data")
    ratings_df = pd.read_csv(ratings_file)
    for _, row in ratings_df.iterrows():
        rating = Rating(userId=row['userId'], movieId=row['movieId'], rating=row['rating'], timestamp=row['timestamp'])
        session.add(rating)

    logger.info("Processing and storing links data")
    links_df = pd.read_csv(links_file)
    for _, row in links_df.iterrows():
        link = Link(movieId=row['movieId'], imdbId=row['imdbId'], tmdbId=row['tmdbId'])
        session.add(link)

    logger.info("Processing and storing tags data")
    tags_df = pd.read_csv(tags_file)
    for _, row in tags_df.iterrows():
        tag = Tag(userId=row['userId'], movieId=row['movieId'], tag=row['tag'], timestamp=row['timestamp'])
        session.add(tag)

    logger.info("Processing and storing genome tags data")
    genome_tags_df = pd.read_csv(genome_tags_file)
    for _, row in genome_tags_df.iterrows():
        genome_tag = GenomeTag(tagId=row['tagId'], tag=row['tag'])
        session.add(genome_tag)

    logger.info("Processing and storing genome scores data")
    genome_scores_df = pd.read_csv(genome_scores_file)
    for _, row in genome_scores_df.iterrows():
        genome_score = GenomeScore(movieId=row['movieId'], tagId=row['tagId'], relevance=row['relevance'])
        session.add(genome_score)

    session.commit()
    logger.info("All data processed and stored successfully")
