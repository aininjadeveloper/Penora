import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import traceback

# Add current directory to path
sys.path.append(os.getcwd())

from flask import Flask, g, session

class MockProject:
    def __init__(self, code, title, text):
        self.code = code
        self.project_title = title
        self.generation_text = text

class TestDownload(unittest.TestCase):
    def setUp(self):
        # We need to import app here.
        # Set dummy env vars to avoid errors
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['SESSION_SECRET'] = 'test'
        
        try:
            from app import app
            self.app = app
            self.client = app.test_client()
        except Exception as e:
            print("Failed to import app:")
            traceback.print_exc()
            raise

    @patch('workspace_service.WorkspaceService.get_project_by_code')
    def test_pdf_download(self, mock_get_project):
        mock_get_project.return_value = MockProject('test_code', 'Test Project', 'Test Content')
        
        with self.client.session_transaction() as sess:
            sess['user_data'] = {'user_id': 'test_user'}
            
        response = self.client.get('/workspace/download/test_code/pdf')
        
        print(f"PDF Response Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data.decode()}")
            
        self.assertEqual(response.status_code, 200)

    @patch('workspace_service.WorkspaceService.get_project_by_code')
    def test_docx_download(self, mock_get_project):
        mock_get_project.return_value = MockProject('test_code', 'Test Project', 'Test Content')
        
        with self.client.session_transaction() as sess:
            sess['user_data'] = {'user_id': 'test_user'}
            
        response = self.client.get('/workspace/download/test_code/docx')
        
        print(f"DOCX Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    @patch('workspace_service.WorkspaceService.get_project_by_code')
    def test_txt_download(self, mock_get_project):
        mock_get_project.return_value = MockProject('test_code', 'Test Project', 'Test Content')
        
        with self.client.session_transaction() as sess:
            sess['user_data'] = {'user_id': 'test_user'}
            
        response = self.client.get('/workspace/download/test_code/txt')
        
        print(f"TXT Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
