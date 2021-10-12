from fastapi.testclient import TestClient
from label_api import app

client = TestClient(app)

def test_create():
    response = client.post("/create_tasks/"
                           "?model_type=keyword_model&predict_type=author_name&"
                           "start_year=2021&start_month=1&end_year=2021&"
                           "end_month=12&target_table=predicting_jobs_predictingresult")
    assert response.status_code == 200

def test_task_list():
    response = client.post(f"/task_list/"
                           f"?tasks=4aa7e3b7274211ec9f9004ea56825bad%3B9480611a-fdaa-47d6-ad9f-fc87c164e129"
                           f"&tasks=f9a1a5cb273e11ecbc8f04ea56825bad%3B4aaa678c-69d5-4758-b00c-23b4b48a77a5")
    assert response.status_code == 200

def test_check_status():
    response = client.post(f"/check_status/"
                           f"?_id=f9a1a5cb273e11ecbc8f04ea56825bad%3B4aaa678c-69d5-4758-b00c-23b4b48a77a5")
    assert response.status_code == 200

def test_sample_result():
    response = client.post(f"/sample_result/"
                           f"?_id=1b63fa1c27da11eca73b04ea56825bad%3B7a13d197-691a-48fb-8baf-279467868425"
                           f"&table=test&order_column=create_time&number=10&offset=10000")
    assert response.status_code == 200







