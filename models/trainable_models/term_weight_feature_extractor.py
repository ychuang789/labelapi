from sklearn.linear_model import SGDClassifier

from utils.enum_config import TWFeatureModel
from utils.exception_tool.exception_manager import TWFeatureModelNotFoundError

class TermWeightFeatureModel():
    def __init__(self):
        pass

    def __repr__(self):
        return 'Create a model that help to extract the term weight feature information'

    @staticmethod
    def create_model(feature_model: str, verbose: int):

        # feature_model: str = kwargs.get('feature_model')

        if not hasattr(TWFeatureModel, feature_model):
            raise TWFeatureModelNotFoundError(f'{feature_model} is not in default TWFeatureModel')
        else:
            feature_model = feature_model.lower()

        if feature_model == TWFeatureModel.SGD.value:
            return SGDClassifier(loss='log', penalty='elasticnet', l1_ratio=0.9,
                                 learning_rate='optimal', n_iter_no_change=10,
                                 shuffle=True, n_jobs=3, fit_intercept=True,
                                 class_weight='balanced', verbose=verbose)
        else:
            raise TWFeatureModelNotFoundError(f'{feature_model} is unknown')
