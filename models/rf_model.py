from typing import Optional, List

import jieba
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from models.audience_model_interfaces import SupervisedModel, MODEL_ROOT
from utils.model_helper import load_joblib, get_multi_accuracy
from utils.selections import PredictTarget


class RandomForestModel(SupervisedModel):
    def __init__(self, model_dir_name, is_multi_label=False, feature=PredictTarget.CONTENT, **kwargs):
        super().__init__(model_dir_name, feature=feature, **kwargs)
        self.available_features = {
            PredictTarget.TITLE,
            PredictTarget.CONTENT,
            PredictTarget.AUTHOR_NAME,
        }
        self.vectorizer = None
        self.is_multi_label = is_multi_label
        self.model_path = self.model_dir_name / 'model.pkl'

        self.vectorizer_path = self.model_dir_name / 'vectorizer.pkl'
        self.mlb: Optional[MultiLabelBinarizer] = None
        self.mlb_path = self.model_dir_name / 'mlb.pkl'

    def load(self):
        self.model = load_joblib(MODEL_ROOT / self.model_path)
        self.vectorizer = load_joblib(MODEL_ROOT / self.vectorizer_path)
        if self.is_multi_label:
            self.mlb = load_joblib(MODEL_ROOT / self.mlb_path)

    def convert_feature(self, examples,
                        update_vectorizer=False,
                        max_features=5000, min_df=2, stop_words='english'):
        seg_contents = []
        for example in examples:
            content = getattr(example, self.feature.value)
            if self.feature in {PredictTarget.CONTENT, PredictTarget.TITLE}:
                sentence = jieba.lcut(str(content))
            elif self.feature in {PredictTarget.AUTHOR, }:
                sentence = list(content)
            else:
                raise ValueError(f"Unavailable feature type {self.feature}")
            seg_contents.append(" ".join(sentence))

        if update_vectorizer:
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(max_features=max_features, min_df=min_df, stop_words=stop_words)
            x_features = self.vectorizer.fit_transform(seg_contents)
        else:
            if self.vectorizer:
                x_features = self.vectorizer.transform(seg_contents)
            else:
                raise ValueError("模型尚未被初始化，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")
        return x_features

    def fit(self, examples, y_true: List):

        x_train_features = self.convert_feature(examples, update_vectorizer=True)
        classifier = RandomForestClassifier(n_estimators=100)

        for index, y in enumerate(y_true):
            y_true[index] = y_true[index][0].split(',')

        if self.is_multi_label:
            self.mlb = MultiLabelBinarizer()
            y_true = self.mlb.fit_transform(y_true)
            self.model = OneVsRestClassifier(classifier)
        else:
            y_true = np.asarray(y_true).ravel()
            self.model = classifier
        self.model.fit(x_train_features, y_true)
        return self.save()

    def predict(self, examples):
        x_features = self.convert_feature(examples)
        predict_labels = self.model.predict(x_features)
        predict_logits = self.model.predict_proba(x_features)
        predict_logits = [tuple([elem for elem in zip(self.model.classes_, r)]) for r in predict_logits]
        return predict_labels, predict_logits

    def eval(self, examples, y_true):

        for index, y in enumerate(y_true):
            y_true[index] = y

        if self.model and self.vectorizer:
            predict_labels, predict_logits = self.predict(examples)
            if self.is_multi_label:
                y_true = self.mlb.transform(y_true)
                acc = get_multi_accuracy(y_true, predict_labels)
                report = classification_report(y_true, predict_labels, output_dict=True)
                report['accuracy'] = acc
            else:
                report = classification_report(y_true, predict_labels, output_dict=True)
            return report
        else:
            raise ValueError(f"模型尚未被訓練，或模型尚未被讀取。若模型已被訓練與儲存，請嘗試執行 ' load() ' 方法讀取模型。")

    def save(self):
        tmp_model_dir = MODEL_ROOT / self.model_dir_name
        if not tmp_model_dir.exists():
            tmp_model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, MODEL_ROOT / self.model_path)
        joblib.dump(self.vectorizer, MODEL_ROOT / self.vectorizer_path)
        if self.is_multi_label:
            joblib.dump(self.mlb, MODEL_ROOT / self.mlb_path)

        return self.model_dir_name


