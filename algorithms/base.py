from qgis.core import QgsProcessingAlgorithm
from qgis.PyQt.QtCore import QCoreApplication
from .parameters import BaseParameter


def tr(domain, text):
    return QCoreApplication.translate(domain, text)


class PythonAlgorithm:
    class Meta:
        pass

    @classmethod
    def as_processing_algorithm(cls):
        return PythonAlgorithmWrapper(cls)

    @classmethod
    def get_sorted_parameters(cls):
        return sorted([(v.order, v.index, n, v)
                       for (n, v) in cls.__dict__.items()
                       if isinstance(v, BaseParameter)])

    @classmethod
    def get_parameters(cls, wrapper):
        params = cls.get_sorted_parameters()
        for (order, idx, name, param) in params:
            label = tr(cls.__name__, param.label)
            yield param.get_parameter(name, label)

    def __init__(self, feedback):
        self._values = {}
        self._feedback = feedback

    def set_values(self, wrapper, parameters, context):
        params = type(self).get_sorted_parameters()
        for (order, idx, name, param) in params:
            value = param.get_value(wrapper, self, parameters, name, context)
            self._values[name] = value

    def run(self):
        raise NotImplemented


class PythonAlgorithmWrapper(QgsProcessingAlgorithm):
    def __init__(self, cls):
        super().__init__()
        self.cls = cls

    def createInstance(self):
        return type(self)(self.cls)

    def name(self):
        return getattr(self.cls.Meta, 'name', self._cls_name.lower())

    def displayName(self):
        return self.tr(getattr(self.cls.Meta, 'display_name', self._cls_name))

    def group(self):
        return self.tr(getattr(self.cls.Meta, 'group', ''))

    def shortHelpString(self):
        return self.tr(getattr(self.cls.Meta, 'help', ''))

    def tags(self):
        tags = getattr(self.cls.Meta, 'tags', [])
        return self.tr(','.join(tags)).split(',')

    def initAlgorithm(self, config=None):
        for param in self.cls.get_parameters(self):
            self.addParameter(param)

    def processAlgorithm(self, parameters, context, feedback):
        algorithm = self.cls(feedback)
        algorithm.set_values(self, parameters, context)
        return algorithm.run()

    def tr(self, text):
        return tr(self._cls_name, text)

    @property
    def _cls_name(self):
        return type(self.cls).__name__
