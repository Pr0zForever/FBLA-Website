import os
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
import re
import nltk
nltk.download('punkt_tab')
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('stopwords')
nltk.download('punkt')

# Ensure models directory exists
if not os.path.exists("models"):
    os.makedirs("models")

# Load dataset (replace with actual data)
df = pd.read_csv("job_postings.csv")  # Ensure this CSV has 'description' and 'salary' columns
resumes = pd.read_csv("user_resumes.csv")  # Ensure this CSV has 'resume_text' and 'user_id'

# Text preprocessing function
def preprocess_text(text):
    text = re.sub(r'\W', ' ', text)  # Remove special characters
    text = text.lower()  # Convert to lowercase
    words = word_tokenize(text)  # Tokenize
    words = [word for word in words if word not in stopwords.words('english')]  # Remove stopwords
    return " ".join(words)

# Apply preprocessing
df['processed_desc'] = df['Description'].apply(preprocess_text)
resumes['processed_resume'] = resumes['Resume Text'].apply(preprocess_text)

# Vectorization
vectorizer = TfidfVectorizer(max_features=500)
job_vectors = vectorizer.fit_transform(df['processed_desc'])
resume_vectors = vectorizer.transform(resumes['processed_resume'])

# Save vectorizer
joblib.dump(vectorizer, "models/tfidf_vectorizer.pkl")

# Compute cosine similarity between resumes and jobs
similarity_scores = cosine_similarity(resume_vectors, job_vectors)

# Create labels (1 = relevant, 0 = not relevant) – needs labeled data
df['relevance'] = np.random.choice([0, 1], size=len(df))  # Temporary random labels, replace with actual

X_train, X_test, y_train, y_test = train_test_split(job_vectors, df['relevance'], test_size=0.2, random_state=42)

# Train logistic regression model
relevance_model = LogisticRegression()
relevance_model.fit(X_train, y_train)

# Save model
joblib.dump(relevance_model, "models/job_relevance_model.pkl")

print("✅ Job Relevance Model Trained and Saved!")

# Dummy dataset - replace with real application results (0 = rejected, 1 = accepted)
df['accepted'] = np.random.choice([0, 1], size=len(df))  

X_train, X_test, y_train, y_test = train_test_split(job_vectors, df['accepted'], test_size=0.2, random_state=42)

# Train acceptance model
acceptance_model = LogisticRegression()
acceptance_model.fit(X_train, y_train)

# Save model
joblib.dump(acceptance_model, "models/acceptance_model.pkl")

print("✅ Acceptance Prediction Model Trained and Saved!")

X_train, X_test, y_train, y_test = train_test_split(job_vectors, df['Salary'], test_size=0.2, random_state=42)

salary_model = RandomForestRegressor(n_estimators=100)
salary_model.fit(X_train, y_train)

joblib.dump(salary_model, "models/salary_model.pkl")

print("✅ Salary Prediction Model Trained and Saved!")
