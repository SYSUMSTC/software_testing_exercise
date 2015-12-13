import os
import tempfile
import unittest
from subprocess import Popen
from unittest import mock

from tornado.testing import AsyncHTTPTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions, wait

from download_server import web_service


class TestCalculateEta(unittest.TestCase):

    def test_eta(self):
        task = {
            'totalLength': 1000,
            'completedLength': 300,
            'downloadSpeed': 80,
            'status': 'active',
        }
        eta = web_service.calculate_eta(task)
        self.assertAlmostEqual(8.75, eta)


class TestTaskHandler(AsyncHTTPTestCase):

    def get_app(self):
        self.mock_rpc = mock.MagicMock()
        return web_service.create_app(
            'aria2_token', 'download_dir', self.mock_rpc)

    def tearDown(self):
        super().tearDown()
        self.mock_rpc.reset_mock()

    def test_stop_task(self):
        self.mock_rpc.aria2.remove.return_value = 'the_task_gid'
        response = self.fetch('/task?gid=the_task_gid', method='DELETE')
        self.assertEqual(b'the_task_gid', response.body)
        self.mock_rpc.aria2.remove.assert_called_with(
            'token:aria2_token', 'the_task_gid')


class TestE2E(unittest.TestCase):

    def setUp(self):
        import run
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.server = Popen([run.__file__, '--run', self.tmp_dir.name])

        if 'TRAVIS' in os.environ and os.environ['TRAVIS']:  # we are on travis
            if os.environ['TRAVIS_PULL_REQUEST'] != 'false':
                self.skipTest('Travis does\'t allow selenium test for PRs')

            wd_url = 'http://{}:{}@localhost:4445/wd/hub'.format(
                os.environ['SAUCE_USERNAME'], os.environ['SAUCE_ACCESS_KEY']
            )
            cap = DesiredCapabilities.FIREFOX.copy()
            cap['tunnel-identifier'] = os.environ['TRAVIS_JOB_NUMBER']
            cap['build'] = os.environ["TRAVIS_BUILD_NUMBER"]
            cap["tags"] = [os.environ["TRAVIS_PYTHON_VERSION"], "CI"]
            self.webdriver = webdriver.Remote(command_executor=wd_url,
                                              desired_capabilities=cap)
        else:
            self.webdriver = webdriver.Firefox()

    def tearDown(self):
        self.webdriver.quit()
        self.server.terminate()
        self.server.wait()
        self.tmp_dir.cleanup()

    def test_add_task(self):
        self.webdriver.get('http://localhost:8000')
        self.webdriver.implicitly_wait(10)

        url_input = self.webdriver.find_element_by_id('url-input')
        url_input.click()
        url_input.send_keys('http://httpbin.org/bytes/1024')

        add_button = self.webdriver.find_element_by_id('add-button')
        add_button.click()

        wait.WebDriverWait(self.webdriver, 10).until(
            expected_conditions.text_to_be_present_in_element(
                (By.CLASS_NAME, 'task-status'), 'complete')
        )

        filename_cell = self.webdriver.find_element_by_class_name(
            'task-filename')
        self.assertEqual('1024', filename_cell.text)
