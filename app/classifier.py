from __future__ import annotations

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.scoring import clean_text


TRAINING_DATA = [
    ("Scientists announce a promising cancer treatment breakthrough", 1),
    ("Community volunteers rescue families after flooding", 1),
    ("New clean energy project brings power to rural schools", 1),
    ("Doctors restore eyesight with low-cost surgery program", 1),
    ("Local charity helps thousands of children get meals", 1),
    ("Researchers discover a safer battery recycling process", 1),
    ("Endangered species population recovers after conservation effort", 1),
    ("Students build affordable water filter for villages", 1),
    ("New vaccine trial shows strong protection", 1),
    ("City opens new shelter and support program for homeless residents", 1),
    ("Farmers improve crop yields with sustainable methods", 1),
    ("Nonprofit donates laptops to underserved schools", 1),
    ("Hospital celebrates record number of successful transplants", 1),
    ("Ocean cleanup team removes tons of plastic waste", 1),
    ("Startup creates affordable prosthetic limbs for children", 1),
    ("Agreement expands access to mental health care", 1),
    ("New program helps veterans find stable jobs", 1),
    ("Breakthrough discovery could reduce carbon emissions", 1),
    ("Neighborhood raises funds to rebuild damaged playground", 1),
    ("Researchers develop early warning system that saves lives", 1),
    ("War leaves thousands displaced across the region", 0),
    ("Markets crash after unexpected economic shock", 0),
    ("Police investigate violent attack downtown", 0),
    ("Company faces fraud allegations from regulators", 0),
    ("Wildfire destroys homes and forces evacuations", 0),
    ("Deadly crash closes highway for hours", 0),
    ("Political crisis deepens after failed talks", 0),
    ("Data breach exposes customer information", 0),
    ("Hospital reports shortage of critical medicine", 0),
    ("Major layoffs hit technology workers", 0),
    ("Storm damage disrupts travel across the country", 0),
    ("Court hears evidence in corruption trial", 0),
    ("Inflation fears grow as prices rise", 0),
    ("Protests turn violent after disputed election", 0),
    ("Officials warn of dangerous scam targeting seniors", 0),
    ("Disease outbreak spreads to more cities", 0),
    ("Drought threatens food supply in several states", 0),
    ("Factory explosion injures workers", 0),
    ("Cyberattack shuts down public services", 0),
    ("Housing crisis worsens for low income families", 0),
]


@lru_cache(maxsize=1)
def get_classifier() -> Pipeline:
    texts = [clean_text(text) for text, _ in TRAINING_DATA]
    labels = [label for _, label in TRAINING_DATA]

    model = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    stop_words="english",
                ),
            ),
            (
                "classifier",
                LogisticRegression(max_iter=1000, class_weight="balanced", C=5.0),
            ),
        ]
    )
    model.fit(texts, labels)
    return model


def classify_positive_news(title: str, summary: str = "") -> float:
    text = clean_text(f"{title}. {summary}")
    if not text:
        return 0.0

    model = get_classifier()
    positive_index = list(model.classes_).index(1)
    probability = model.predict_proba([text])[0][positive_index]
    return round(float(probability), 3)
