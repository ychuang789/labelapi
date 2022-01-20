from fastapi.testclient import TestClient
from audience_api import app

class TestAPIs(object):

    client = TestClient(app)

    def test_training(self):
        response = self.client.post("/models/prepare/",
                                    json={
                                        "DATASET_DB": "audience-toolkit-django",
                                        "DATASET_NO": 1,
                                        "MODEL_TYPE": "RANDOM_FOREST_MODEL",
                                        "MODEL_INFO": {
                                            "model_path": "model_path"
                                        }
                                    })
        assert response.status_code == 200
        return response.status_code, response.content

    def test_testing(self):
        response = self.client.post("/models/test/",
                                    json={
                                        "DATASET_DB": "audience-toolkit-django",
                                        "DATASET_NO": 1,
                                        "MODEL_TYPE": "RANDOM_FOREST_MODEL",
                                        "MODEL_INFO": {
                                            "model_path": "model_path"
                                        }
                                    })
        assert response.status_code == 200

    def test_status(self):
        response = self.client.get(f'/models/10')
        assert response.status_code == 200

    def test_report(self):
        response = self.client.get(f'/models/0/report/')
        assert response.status_code == 200
