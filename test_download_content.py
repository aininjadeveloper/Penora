import unittest
import sys
import os
from io import BytesIO

sys.path.append(os.getcwd())

class TestDownloadContent(unittest.TestCase):
    def setUp(self):
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SESSION_SECRET'] = 'test'
        try:
            from app import app
            self.app = app
            self.client = app.test_client()
        except:
            # If app import fails, print why
            import traceback
            traceback.print_exc()
            raise

    def test_post_download_txt(self):
        response = self.client.post('/download-content', data={
            'title': 'Test Doc',
            'content': 'This is test content.',
            'format': 'txt'
        })
        print(f"TXT Status: {response.status_code}")
        if response.status_code != 200:
            print(f"TXT Data: {response.data.decode()}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/plain; charset=utf-8')

    def test_post_download_pdf(self):
        response = self.client.post('/download-content', data={
            'title': 'Test PDF',
            'content': 'This is test content.',
            'format': 'pdf'
        })
        print(f"PDF Status: {response.status_code}")
        if response.status_code != 200:
            print(f"PDF Data: {response.data.decode()}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/pdf')

if __name__ == '__main__':
    unittest.main()
