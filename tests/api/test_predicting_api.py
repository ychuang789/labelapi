from fastapi.testclient import TestClient
from audience_api import app
from settings import LABEL
from utils.label.run_label_task import read_from_dir


client = TestClient(app)
pattern = read_from_dir('keyword_model', 'author_name')
inv = {v: k for k, v in LABEL.items()}
patterns = [{inv.get(k) : v} for i in pattern for k, v in i.items()]

def test_create():
    response = client.post("tasks/",
                                json={
                                    'MODEL_TYPE': 'keyword_model',
                                    'PREDICT_TYPE': 'author',
                                    'START_TIME': '2020-01-01',
                                    'END_TIME': '2021-01-01',
                                    'PATTERN': patterns,
                                    'INPUT_SCHEMA': 'wh_backpackers',
                                    'INPUT_TABLE': 'ts_page_content',
                                    'OUTPUT_SCHEMA': 'audience_result',
                                    'COUNTDOWN': 5, 'QUEUE': 'queue1',
                                    'MODEL_JOB_LIST': [10, 11],
                                    'SITE_CONFIG': {'host': 'dc-data11.eland.com.tw',
                                                    'port': 3306,
                                                    'user': 'rd2',
                                                    'password': 'eland5678',
                                                    'db': 'wh_backpackers',
                                                    'charset': 'utf8mb4'}
                                    })
    assert response.status_code == 200
    assert response.json()['error_code'] == 200

def test_task_list():
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json()['error_code'] == 200

def test_check_status():
    response = client.get(f"/tasks/9214054272be11ecb10204ea56825bad")
    assert response.status_code == 200
    assert response.json()['error_code'] == 200

def test_sample_result():
    response = client.get(f"/tasks/9214054272be11ecb10204ea56825bad/sample")
    assert response.status_code == 200
    assert response.json()['error_code'] == 200







