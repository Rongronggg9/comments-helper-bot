FROM python:3.9-slim AS builder

RUN apt-get update && apt-get install -y build-essential

# initialize venv
RUN python -m venv /opt/venv

# activate venv
ENV PATH="/opt/venv/bin:$PATH"

# upgrade venv deps
RUN pip install --trusted-host pypi.python.org --upgrade pip setuptools wheel

COPY requirements.txt .

RUN pip install --trusted-host pypi.python.org -r requirements.txt

#----------------------------------------

FROM python:3.9-slim

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY . /app

# activate venv
ENV PATH="/opt/venv/bin:$PATH"

# Define environment variable
ENV TOKEN X
ENV T_PROXY X

CMD ["python", "-u", "telegramRSSbot.py"]
