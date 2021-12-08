# python
PROJECT_NAME=None
PYTHON_NAME=python

# worker
# WORKER_NAME="worker1"
CONCURRENCY=500
NUMBER_OF_QUEUE=4

# tasks
# YEAR=2020
YEAR=2021
DB_NAME_FILE='requirements_database_list_1.txt'
# DB_NAME_FILE='requirements_database_list_2.txt'

python_path:
	@eval "which $(PYTHON_NAME)"
	@eval "which $(PIP_NAME)"

run_queue_1:
	@eval "celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_queue_2:
	@eval "celery -A celery_worker worker -n worker2@%n -Q queue2 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_queue_3:
	@eval "celery -A celery_worker worker -n worker3@%n -Q queue3 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_queue_4:
	@eval "celery -A celery_worker worker -n worker4@%n -Q queue4 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_api:
	@eval "python label_api.py"

run_tasks:
	@eval "python run_task_cli.py --file $(DB_NAME_FILE) --number_of_queue $(NUMBER_OF_QUEUE) --year $(YEAR)"