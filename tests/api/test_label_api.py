from fastapi.testclient import TestClient
from label_api import app

class TestAPIs(object):
    client = TestClient(app)

    def test_create(self):
        response = self.client.post("/api/tasks/",
                                    json={
                                        "model_type": "keyword_model",
                                        "predict_type": "author_name",
                                        "start_time": "2018-01-01 00:00:00",
                                        "end_time": "2018-12-31 23:59:59",
                                        "target_schema": "forum_data",
                                        "target_table": "ts_page_content"
                                    })
        assert response.status_code == 200

    def test_task_list(self):
        response = self.client.get("/api/tasks/")
        assert response.status_code == 200

    def test_check_status(self):
        response = self.client.get(f"/api/tasks/e138514e307a11eca07b04ea56825bad")
        assert response.status_code == 200

    def test_sample_result(self):
        response = self.client.get(f"/api/tasks/fa097ea92ca211ecbb8004ea56825baa/sample/?table_name=wh_panel_mapping_Dcard&table_name=wh_panel_mapping_forum")
        assert response.status_code == 200







