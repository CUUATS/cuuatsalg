from qgis.core import QgsFields
from cuuatsalg.algorithms.base import PythonAlgorithm
from cuuatsalg.algorithms.parameters import FeatureSourceParameter, \
    FieldParameter, FolderDestinationParameter, StringParameter, \
    FeatureSinkParameter, BooleanParameter


class ExportArcGISAttachments(PythonAlgorithm):
    source = FeatureSourceParameter('Source layer')
    attach = FeatureSourceParameter('Attachment layer')
    source_id = FieldParameter('Source layer ID field',
                               parent_layer='source')
    attach_id = FieldParameter('Attachment layer foreign key field',
                               parent_layer='attach')
    folder = FolderDestinationParameter('Attachment folder')
    use_fid = BooleanParameter('Use feature ID in results layer',
                               default=True)
    id_name = StringParameter('Results ID field name',
                              default='related_id')
    path_name = StringParameter('Results path field name',
                                default='path')
    output = FeatureSinkParameter('Results layer',
                                  fields_method='output_fields',
                                  geometry='NoGeometry')

    class Meta:
        display_name = 'Export ArcGIS attachments'
        group = 'Attachments'
        tags = [
            'arcgis',
            'attachment',
            'export',
            'image',
            'convert'
        ]

    def run(self):
        output, output_id = self.output
        return {'output': output_id}

    def output_fields(self):
        fields = QgsFields()
        return fields
