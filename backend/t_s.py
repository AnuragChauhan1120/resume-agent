import sys
sys.path.append(".")

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

query = "data scientist internship"
chunk = """WORK EXPERIENCE:\nData Science Intern\nEvoastra Ventures\n|\nDecember 2025 – February 2026\n|\n§\nBuilt production-ready anomaly detection system for commercial building energy consumption using Isolation Forests and\nLSTM autoencoders, achieving 20–40% faster detection and simulating $50K–$200K annual cost savings per building\nDeveloped automated web scraping pipelines using Python (BeautifulSoup, Selenium) to collect and preprocess 10,000+ real-\nworld energy consumption records, reducing manual data collection time by 80%\nPerformed exploratory data analysis on multivariate time-series data to identify consumption patterns and anomalies, delivering\nactionable insights that informed model architecture decisions\nCollaborated with cross-functional team of engineers to iterate on ML prototypes, implementing ensemble methods that im-\nproved detection accuracy by 15% compared to baseline models """

q_vec = model.encode([query], normalize_embeddings=True)
c_vec = model.encode([chunk], normalize_embeddings=True)

score = cosine_similarity(q_vec, c_vec)[0][0]
print(f"Score: {score:.4f}")