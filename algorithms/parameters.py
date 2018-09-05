from qgis.core import QgsProcessingParameterFolderDestination, \
    QgsProcessingParameterString, QgsProcessingParameterField, \
    QgsProcessingParameterFeatureSink, QgsProcessingParameterFeatureSource, \
    QgsProcessingParameterBoolean


class BaseParameter:
    _index = 0

    def __init__(self, label, **kwargs):
        self.label = label
        self.default = kwargs.get('default', None)
        self.optional = kwargs.get('optional', False)
        self.order = kwargs.get('order', 0)
        self.index = BaseParameter._index
        BaseParameter._index += 1

    def __get__(self, instance, owner):
        if owner:
            return self
        return instance._values.get(self.index, None)

    def __set__(self, instance, value):
        instance._values[self.index] = value

    def get_parameter(self, name, label):
        raise NotImplemented

    def get_value(self, wrapper, instance, parameters, name, context):
        raise NotImplemented


class StringParameter(BaseParameter):
    def get_parameter(self, name, label):
        return QgsProcessingParameterString(
            name, label, self.default, optional=self.optional)

    def get_value(self, wrapper, instance, parameters, name, context):
        return wrapper.parameterAsString(parameters, name, context)


class BooleanParameter(BaseParameter):
    def get_parameter(self, name, label):
        return QgsProcessingParameterBoolean(name, label)

    def get_value(self, wrapper, instance, parameters, name, context):
        return wrapper.parameterAsBoolean(
            parameters, name, context, self.default, self.optional)


class FeatureSourceParameter(BaseParameter):
    def get_parameter(self, name, label):
        return QgsProcessingParameterFeatureSource(
            name, label, defaultValue=self.default, optional=self.optional)

    def get_value(self, wrapper, instance, parameters, name, context):
        return wrapper.parameterAsSource(parameters, name, context)


class FolderDestinationParameter(BaseParameter):
    def get_parameter(self, name, label):
        return QgsProcessingParameterFolderDestination(
            name, label, self.default, self.optional)

    def get_value(self, wrapper, instance, parameters, name, context):
        return wrapper.parameterAsFile(parameters, name, context)


class FieldParameter(BaseParameter):
    _value_method = ''

    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self.parent_layer = kwargs.get('parent_layer')

    def get_parameter(self, name, label):
        return QgsProcessingParameterField(
            name, label, self.default,
            optional=self.optional,
            parentLayerParameterName=self.parent_layer)

    def get_value(self, wrapper, instance, parameters, name, context):
        return wrapper.parameterAsFields(
            parameters, name, context)


class FeatureSinkParameter(BaseParameter):
    def __init__(self, label, **kwargs):
        super().__init__(label, **kwargs)
        self.fields = kwargs.get('fields')
        self.fields_from = kwargs.get('fields_from')
        self.fields_method = kwargs.get('fields_method')
        self.geometry = kwargs.get('geometry')
        self.geometry_from = kwargs.get('geometry_from')
        self.geometry_method = kwargs.get('geometry_method')
        self.crs = kwargs.get('crs')
        self.crs_from = kwargs.get('crs_from')
        self.crs_method = kwargs.get('crs_method')

    def get_parameter(self, name, label):
        return QgsProcessingParameterFeatureSink(
            name, label, defaultValue=self.default, optional=self.optional)

    def get_value(self, wrapper, instance, parameters, name, context):
        return wrapper.parameterAsSink(
            parameters, name, context, self._get_fields(instance),
            self._get_geometry(instance), self._get_crs(instance))

    def _get_param(self, name, from_method, instance):
        value = getattr(self, name)
        if value is not None:
            return value
        from_param = getattr(self, name + '_from')
        if from_param is not None:
            return getattr(instance._values[from_param], from_method)()
        method = getattr(self, name + '_method')
        if method is not None:
            return getattr(instance, method)()

    def _get_fields(self, instance):
        return self._get_param('fields', 'fields', instance)

    def _get_geometry(self, instance):
        return self._get_param('geometry', 'wkbType', instance)

    def _get_crs(self, instance):
        return self._get_param('crs', 'sourceCrs', instance)
