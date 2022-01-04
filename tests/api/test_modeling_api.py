from fastapi.testclient import TestClient
from audience_api import app

from utils.input_example import InputExample
from datetime import datetime

post_male = "小弟我沒女友，在八卦版混了很久了在八卦版混，時常會有的福利就是偶爾會有人貼清涼養眼圖上班上久了，心情煩悶，看這些圖多多少少會有解鬱消悶的效果感謝八卦版大的貢獻所以在八卦版上，只要看到巨乳等關鍵字，我都是會直覺地點閱進入觀賞，以調劑身心。"
post_female = "小妹的朋友上週領薪水這週就跟我哭哭說全身上下剩一千五明明是她自己限制自己一個月只能花幾千塊其他買保險跟存起來這樣有什麼好哭哭的就是自己強迫自己啊而且明明就是存起來哪是沒錢啊不懂欸"
post_female_2 = "小妹我男朋友上週領薪水這週就跟我哭哭說全身上下剩一千五明明是她自己限制自己一個月只能花幾千塊其他買保險跟存起來這樣有什麼好哭哭的就是自己強迫自己啊而且明明就是存起來哪是沒錢啊不懂欸"
post_young = "小弟我出社會工作不到兩年，今天辦了人生第一張信用卡...。"

input_male = InputExample(id_="2", s_area_id="2", author="Bob", title="", content=post_male,
                          post_time=datetime.now(), label="male")
input_female = InputExample(id_="1", s_area_id="ptt_woman_talk", author="Alice", title="", content=post_female,
                            post_time=datetime.now(), label="female")
input_female_2 = InputExample(id_="1", s_area_id="ptt_woman_talk", author="Alice", title="", content=post_female_2,
                              post_time=datetime.now(), label="female")
input_young = InputExample(id_="1", s_area_id="1", author="Alice", title="", content=post_young,
                           post_time=datetime.now())


class TestAPIs(object):

    client = TestClient(app)

    def test_training(self):
        response = self.client.post("/api/models/training/",
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
        response = self.client.post("/api/models/testing/",
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
        response = self.client.get(f'/api/models/67baa11967b211ec982c04ea56825bad')
        assert response.status_code == 200

    def test_report(self):
        response = self.client.get(f'/api/models/67baa11967b211ec982c04ea56825bad/report/')
        assert response.status_code == 200
