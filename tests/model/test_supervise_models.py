import os
from datetime import datetime
from unittest import TestCase

import numpy as np

from definition import ROOT_DIR
from models.trainable_models.rf_model import RandomForestModel
from models.trainable_models.tw_model import TermWeightModel
from utils.data.data_helper import load_examples
from utils.data.input_example import InputExample

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


training_file = os.path.join(ROOT_DIR, "tests/sample_data/train.csv")
testing_file = os.path.join(ROOT_DIR, "tests/sample_data/test.csv")

training_set = load_examples(training_file, sample_count=500)
train_y = [[d.label] for d in training_set]

testing_set = load_examples(testing_file)
test_y = [[d.label] for d in testing_set]

class TestRandomForestModel(TestCase):
    model_path = "1_random_forest_model"
    model = RandomForestModel(model_dir_name=model_path)

    def test_convert_feature(self):
        feature = self.model.convert_feature([input_young, input_male, input_female], update_vectorizer=True)
        self.assertIsInstance(feature.toarray(), np.ndarray)

    def test_fit(self):
        self.model.fit(examples=training_set, y_true=train_y)

    def test_load(self):
        self.model.load()

    def test_eval(self):
        self.model.load()
        self.model.eval(examples=testing_set, y_true=test_y)

class TestTermWeightModel(TestCase):
    model_path = "2_term_weight_model"
    model = TermWeightModel(model_dir_name=model_path, na_tag='一般')

    def test_fit(self):
        self.model.fit(examples=training_set, y_true=train_y)

    def test_load(self):
        self.model.load()

    def test_eval(self):
        self.model.load()
        self.model.eval(examples=testing_set, y_true=test_y)





