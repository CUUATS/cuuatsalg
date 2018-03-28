import os
import processing
import re
from qgis.core import QgsProcessingParameterFolderDestination, \
    QgsProcessingParameterString, QgsProcessingException
from cuuatsalg.algorithms.base import BaseAlgorithm


class CreateProjectFolder(BaseAlgorithm):
    FOLDER = 'FOLDER'
    NAME = 'NAME'
    OUTPUT = 'OUTPUT'

    ALLOW_SPACES = re.compile(r'[^A-Za-z0-9 ]+')
    NO_SPACES = re.compile(r'[^A-Za-z0-9]+')
    PROJECT_FOLDERS = ['Data', 'Layers', 'Maps', 'Scripts', 'Templates']

    HELP = \
        '''This algorithm creates the folder and GeoPackage structure for a
        new project. The project name should be provided in title case and
        should end with a year, if applicable (e.g., Urbana Transportation
        Plan 2015). The client folder is the folder in which the new project
        will be created.
        '''.replace('\n', '')

    def name(self):
        return 'createprojectfolder'

    def displayName(self):
        return self.tr('Create project folder')

    def group(self):
        return self.tr('Project management')

    def shortHelpString(self):
        return self.tr(self.HELP)

    def tags(self):
        tags = [
            'project',
            'folder',
            'geopackage',
            'structure',
            'organization',
            'client',
            'template'
        ]
        return self.tr(','.join(tags)).split(',')

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString(
            self.NAME,
            self.tr('Project name')))

        self.addParameter(QgsProcessingParameterFolderDestination(
            self.FOLDER,
            self.tr('Client folder')))

    def _sanitize(self, name, camel_case=False):
        """
        Sanitize strings for use in file and folder names.
        """

        if camel_case:
            return self.NO_SPACES.sub('', name.title())
        return self.ALLOW_SPACES.sub('', name)

    def processAlgorithm(self, parameters, context, feedback):
        client_dir = self.parameterAsFile(parameters, self.FOLDER, context)
        project_name = self.parameterAsString(parameters, self.NAME, context)
        project_camel = self._sanitize(project_name, camel_case=True)

        if not os.path.isdir(client_dir):
            raise QgsProcessingException(self.tr('Invalid client folder'))

        if not (project_name and project_camel):
            raise QgsProcessingException(self.tr('Invalid project name'))

        # Create the project folder.
        project_path = os.path.join(client_dir, project_name)
        if os.path.exists(project_path):
            raise QgsProcessingException(
                self.tr('Project folder already exists: %s') % (project_path,))
        os.makedirs(project_path)

        # Create project subfolders.
        for folder in self.PROJECT_FOLDERS:
            os.mkdir(os.path.join(project_path, folder))

        # Create a GeoPackage.
        gpkg_name = '%s.gpkg' % (project_camel,)
        gpkg_path = os.path.join(project_path, 'Data', gpkg_name)
        gpkg = processing.run('native:package', {
            'LAYERS': [],
            'OUTPUT': gpkg_path,
            'OVERWRITE': False,
        }, feedback=feedback, context=context)['OUTPUT']

        return {self.OUTPUT: gpkg}
