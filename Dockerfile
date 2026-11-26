
FROM python:3.13-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application
COPY app/ app/

# Copy only the required trained model artifacts
COPY data/processed/biocascade_model_upper_bound.joblib data/processed/
COPY data/processed/biocascade_model_independent.joblib data/processed/
COPY data/processed/imputer_upper_bound.joblib data/processed/
COPY data/processed/imputer_independent.joblib data/processed/

# Run as a non-root user
RUN useradd --create-home biocascade
USER biocascade

EXPOSE 5000

# Start the production server
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 1 --timeout 120 --access-logfile - app.app:app"]
