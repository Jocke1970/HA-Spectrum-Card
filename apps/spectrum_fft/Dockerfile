FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/spectrum
COPY requirements.txt /opt/spectrum/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY analyzer.py /opt/spectrum/analyzer.py
COPY run.py /opt/spectrum/run.py
CMD ["python", "-u", "/opt/spectrum/run.py"]
