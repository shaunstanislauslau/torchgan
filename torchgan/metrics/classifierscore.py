import torch
import torch.nn.functional as F
import torchvision
from .metric import EvaluationMetric
from ..utils import reduce

__all__ = ['ClassifierScore']

class ClassifierScore(EvaluationMetric):
    r"""
    Computes the Classifier Score of a Model.

    Args:
        classifier (torch.nn.Module, optional) : The model to be used as a base to compute the classifier
            score. If `None` is passes the pretrained :mod:`torchvision.models.inception_v3` is used.
        transform (torchvision.transforms, optional) : Transformations applied to the image before feeding
            it to the classifier
    """
    def __init__(self, classifier=None, transform=None):
        self.classifier = torchvision.models.inception_v3(True) if classifier is None else classifier
        self.classifier.eval()
        self.transform = transform
        self.arg_map = {}

    def set_arg_map(self, value):
        self.arg_map.update(value)

    def preprocess(self, x):
        r"""
        Preprocessor for the Classifier Score. It transforms the image as per the transform requirements
        and feeds it to the classifier.

        Args:
            x (torch.Tensor) : Image in tensor format

        Returns:
            The output from the classifier.
        """
        x = x if self.transform is None else self.transform(x)
        x = x.unsqueeze(0)
        return self.classifier(x)

    def calculate_score(self, x):
        r"""
        Computes the Inception Score for the Input.

        Args:
            x (torch.Tensor) : Image in tensor format

        Returns:
            The Inception Score.
        """
        p = F.softmax(x, dim=1)
        q = torch.mean(p, dim=0)
        kl = torch.sum(p * (F.log_softmax(x, dim=1) - torch.log(q)), dim=1)
        return torch.exp(reduce(kl, 'elementwise_mean')).data

    def metric_ops(self, generator, device):
        noise = torch.randn(1, generator.encoding_dims, device=device)
        img = generator(noise).detach().cpu()
        score = self.__call__(img.squeeze(0))
        return score
