# Test

###### Updated by Weber Huang at 2022-01-12

## API

The APIs are built with the fastapi tool, namely `TestClient` by using `pytest` to execute the test function. We wrap the command inside the `Makefile`:

```shell
$ make test_api
```

> Noted that if you edit the file structures of the tests package, please modify the `Makefile` too



## Others

The test scripts of models, workers and connection are built with python `unittest`. Use `test.py` the execute them:

```shell
$ python test.py --help
Usage: test.py [OPTIONS]

Options:
  -D, --dir TEXT     [required]
  -F, --file TEXT    [required]
  -C, --class_ TEXT
  -M, --method TEXT
  --help             Show this message and exit.
```

File structures:

```shell
tests
├── __init__.py
├── api
│   ├── __init__.py
│   ├── test_modeling_api.py
│   └── test_predicting_api.py
├── connection
│   ├── __init__.py
│   └── test_connection.py
├── model
│   ├── __init__.py
│   ├── test_model_creator.py
│   ├── test_rulebase_models.py
│   └── test_supervise_models.py
├── sample_data
│   ├── dev.csv
│   ├── labels.json
│   ├── rulebase_testdata.csv
│   ├── test.csv
│   └── train.csv
└── worker
    ├── __init__.py
    ├── test_dump_worker.py
    ├── test_modeling_worker.py
    ├── test_orm_worker.py
    └── test_predict_worker.py

```

For example, we wanna test the modeling worker:

```shell
$ python test.py -D worker -F test_modeling_worker -C TestModelingWorker2

test tests.worker.test_modeling_worker.TestModelingWorker2
[2022-01-12 10:22:43,572][modeling][INFO] start eval_outer_test_data task: 3298be1f6def11eca8ca04ea56825bad
[2022-01-12 10:22:43,572][modeling][INFO] Initializing the model term_weight_model...
[2022-01-12 10:22:43,580][modeling][INFO] preparing the datasets for task: 3298be1f6def11eca8ca04ea56825bad
[2022-01-12 10:22:44,024][modeling][INFO] load the model 0_term_weight_model ...
[2022-01-12 10:22:44,025][modeling][INFO] evaluating with ext_test data ...
[2022-01-12 10:22:44,186][modeling][INFO] modeling task: 3298be1f6def11eca8ca04ea56825bad is finished
.
----------------------------------------------------------------------
Ran 1 test in 0.692s

OK

```

