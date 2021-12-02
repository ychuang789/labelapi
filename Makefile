# python
PROJECT_NAME=None
PYTHON_NAME=python

# worker
WORKER_NAME="worker1"
CONCURRENCY=500

python_path:
	@eval "which $(PYTHON_NAME)"
	@eval "which $(PIP_NAME)"

activate:
	@source venv/bin/activate
	@eval "which $(PYTHON_NAME)"

run_queue_1:
	@eval "celery -A celery_worker worker -n $(WORKER_NAME)@%n -Q queue1 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_queue_2:
	@eval "celery -A celery_worker worker -n $(WORKER_NAME)@%n -Q queue2 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_queue_3:
	@eval "celery -A celery_worker worker -n $(WORKER_NAME)@%n -Q queue3 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_queue_4:
	@eval "celery -A celery_worker worker -n $(WORKER_NAME)@%n -Q queue4 -l INFO -P gevent --concurrency=$(CONCURRENCY)"

run_api:
	@eval "python label_api.py"

