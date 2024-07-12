FROM gitlab.businessolver.com:5050/data-science/aws-infrastructure/sdc/build-python:3.12.4-ol8 AS base

FROM base as buildtools

RUN dnf -y install graphviz graphviz-python \
    && dnf clean all \
    && python3 -m pip install --upgrade pip \
    && pip3 install poetry

ENV BASEDIR="/usr/local/app"
WORKDIR ${BASEDIR}/src
COPY . .

WORKDIR ${BASEDIR}
COPY .streamlit .streamlit
COPY poetry.lock pyproject.toml .

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

ENV STREAMLIT_SERVER_PORT=8501

# Expose the necessary port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "src/app.py", "--server.fileWatcherType", "none", "--browser.gatherUsageStats", "false"]