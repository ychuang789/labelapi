import os
from unittest import TestCase

from definition import ROOT_DIR
from utils.data_helper import load_examples

training_file = os.path.join(ROOT_DIR, "tests/sample_data/train.csv")
testing_file = os.path.join(ROOT_DIR, "tests/sample_data/test.csv")

training_set = load_examples(file=training_file, sample_count=500)
train_y = [d.label for d in training_set]

testing_set = load_examples(file=testing_file)
test_y = [d.label for d in testing_set]

class TestRandomForestModel(TestCase):
