# python
PROJECT_NAME=None
PYTHON_NAME=python

CONCURRENCY_P=500
CONCURRENCY_M=8

NUMBER_OF_QUEUE=4

python_path:
	@eval "which $(PYTHON_NAME)"
	@eval "which $(PIP_NAME)"

run_predicting_1:
	@eval "celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P gevent --concurrency=$(CONCURRENCY_P) --without-gossip --logfile=logs/predicting_1.log"

#run_predicting_1:
#	@eval "celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO -P solo  --without-gossip --logfile=logs/predicting_1.log"

#run_predicting_1:
#	@eval "celery -A celery_worker worker -n worker1@%n -Q queue1 -l INFO  --without-gossip --logfile=logs/predicting_1.log"

run_predicting_2:
	@eval "celery -A celery_worker worker -n worker2@%n -Q queue1 -l INFO -P gevent --concurrency=$(CONCURRENCY_P) --without-gossip --logfile=logs/predicting_2.log"

run_modeling_1:
	@eval "celery -A celery_worker worker -n worker3@%n -Q queue2 -l INFO -P gevent --concurrency=$(CONCURRENCY_M) --without-gossip --logfile=logs/modeling_1.log"

run_api:
	@eval "python audience_api.py"

run_tasks:
	@eval "python run_task_cli.py --file $(DB_NAME_FILE) --number_of_queue $(NUMBER_OF_QUEUE) --year $(YEAR)"

test_api:
	@eval "pytest tests/api/"
