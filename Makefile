# Variables
APP_IMAGE_NAME := jira-link-graph
APP_CONTAINER_NAME := jira-link-graph


build_docker:
	docker build -t $(APP_IMAGE_NAME) -f containers/Dockerfile .

run_docker:
	docker run -it -p 8506:8501/tcp \
	-d --name $(APP_CONTAINER_NAME) $(APP_IMAGE_NAME)

run_local:
	poetry run streamlit run app.py

# Make commands
.PHONY: run_docker run_local build_docker
