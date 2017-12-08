import nose2
import os
import shutil
import sys
from qgis.core import QgsApplication
from qgis.testing import start_app, unittest
from cuuatsalg.provider import CuuatsAlgorithmProvider

# TODO: Figure out a better way to resuse AlgorithmsTestBase without
# monkey patching and changing the Python path.
sys.path.append(os.path.dirname(__file__))
from processing.tests import AlgorithmsTestBase


def processingTestDataPath():
    return os.path.join(os.path.dirname(__file__), 'testdata')


AlgorithmsTestBase.processingTestDataPath = processingTestDataPath


class TestCuuatsAlgorithms(
        unittest.TestCase, AlgorithmsTestBase.AlgorithmsTest):

    @classmethod
    def setUpClass(cls):
        start_app()
        from processing.core.Processing import Processing
        Processing.initialize()
        QgsApplication.processingRegistry().addProvider(
            CuuatsAlgorithmProvider())
        cls.cleanup_paths = []
        cls.in_place_layers = {}
        cls.vector_layer_params = {}

    @classmethod
    def tearDownClass(cls):
        from processing.core.Processing import Processing
        Processing.deinitialize()
        for path in cls.cleanup_paths:
            shutil.rmtree(path)

    def test_definition_file(self):
        return 'cuuats_algorithm_tests.yaml'


if __name__ == '__main__':
    nose2.main()
