from fastapi.testclient import TestClient
from audience_api import app


class TestAPIs(object):
    client = TestClient(app)

    def test_training(self):
        response = self.client.post("/models/prepare/",
                                    json={
                                        "QUEUE": "queue2",
                                        "DATASET_DB": "audience-toolkit-django",
                                        "DATASET_NO": 1,
                                        "TASK_ID": "TEST_API",
                                        "PREDICT_TYPE": "CONTENT",
                                        "MODEL_TYPE": "TERM_WEIGHT_MODEL",
                                        "MODEL_INFO": {
                                            "feature_model": "SGD",
                                            "model_path": "model_path"
                                        }
                                    })
        assert response.status_code == 200
        # return response.status_code, response.content

    def test_testing(self):
        response = self.client.post("/models/test/",
                                    json={
                                        "QUEUE": "queue2",
                                        "DATASET_DB": "audience-toolkit-django",
                                        "DATASET_NO": 1,
                                        "TASK_ID": "TEST_API",
                                        "MODEL_TYPE": "TERM_WEIGHT_MODEL",
                                        "PREDICT_TYPE": "CONTENT",
                                        "MODEL_INFO": {
                                            "model_path": "model_path"
                                        }
                                    })
        assert response.status_code == 200

    def test_status(self):
        response = self.client.get(f'/models/TEST_API')
        assert response.status_code == 200

    def test_report(self):
        response = self.client.get(f'/models/TEST_API/report/')
        assert response.status_code == 200

    def test_abort(self):
        response = self.client.post(f'/models/abort/',
                                    json={
                                        "TASK_ID": "TEST_API"
                                    })
        assert response.status_code == 200

    def test_delete(self):
        response = self.client.delete(f'/models/delete/',
                                      json={
                                          "TASK_ID": "TEST_API"
                                      })
        assert response.status_code == 200

    # def test_model_import(self):
    #     """Missing test case"""
    #     pass

    # def test_get_import_model_status(self):
    # """Missing test case"""
    #     pass

    def test_get_eval_details(self):
        response = self.client.get("/models/04e0960e735511ecab4b04ea56825bad/eval_details/33/100")
        assert response.status_code == 200

    def test_get_eval_details_false_prediction(self):
        response = self.client.get("/models/04e0960e735511ecab4b04ea56825bad/false_predict/33/100")
        assert response.status_code == 200

    def test_get_eval_details_true_prediction(self):
        response = self.client.get("/models/04e0960e735511ecab4b04ea56825bad/true_predict/33/100")
        assert response.status_code == 200

    # def test_download_details(self):
    #     """missing test case"""
    #     pass

    def test_term_weight_add(self):
        response = self.client.put("/models/term_weight/add",
                                   json={
                                       "TASK_ID": "04e0960e735511ecab4b04ea56825bad",
                                       "TERM": "RD2_NLP",
                                       "WEIGHT": 0.25,
                                       "LABEL": "一般"
                                   })
        assert response.status_code == 200

    def test_get_term_weights(self):
        response = self.client.get("/models/04e0960e735511ecab4b04ea56825bad/term_weight")
        assert response.status_code == 200

    def test_term_weight_update(self):
        response = self.client.post("/models/term_weight/update",
                                    json={
                                        'TERM_WEIGHT_ID': 1,
                                        'LABEL': '一般',
                                        'TERM': 'RD2_NLP',
                                        'WEIGHT': 0.25
                                    })
        assert response.status_code == 200

    def test_term_weight_download(self):
        response = self.client.get("/models/04e0960e735511ecab4b04ea56825bad/term_weight/download")
        assert response.status_code == 200







