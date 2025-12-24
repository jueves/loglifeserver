import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestStartServerHTTPS:
    """Test HTTPS configuration in start_server.py"""

    @pytest.fixture
    def temp_certs(self):
        """Create temporary certificate files for testing"""
        temp_dir = tempfile.mkdtemp()
        cert_path = os.path.join(temp_dir, "cert.pem")
        key_path = os.path.join(temp_dir, "key.pem")

        # Create dummy certificate files
        with open(cert_path, 'w') as f:
            f.write("dummy cert")
        with open(key_path, 'w') as f:
            f.write("dummy key")

        yield cert_path, key_path

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_uvicorn(self):
        """Mock uvicorn.run to prevent actual server startup"""
        with patch('start_server.uvicorn.run') as mock:
            yield mock

    def test_https_enabled_with_certificates(self, temp_certs, mock_uvicorn):
        """Test that HTTPS is enabled when certificate paths are set"""
        cert_path, key_path = temp_certs

        with patch.dict(os.environ, {
            'SSL_CERT_PATH': cert_path,
            'SSL_KEY_PATH': key_path,
            'PORT': '3001',
            'HOST': '0.0.0.0'
        }):
            from start_server import main
            main()

        # Verify uvicorn.run was called with SSL config
        mock_uvicorn.assert_called_once()
        call_kwargs = mock_uvicorn.call_args.kwargs

        assert 'ssl_certfile' in call_kwargs
        assert 'ssl_keyfile' in call_kwargs
        assert call_kwargs['ssl_certfile'] == cert_path
        assert call_kwargs['ssl_keyfile'] == key_path
        assert call_kwargs['host'] == '0.0.0.0'
        assert call_kwargs['port'] == 3001

    def test_http_without_certificates(self, mock_uvicorn):
        """Test that HTTP is used when no certificates are configured"""
        # Mock load_dotenv to prevent loading real .env
        with patch('start_server.load_dotenv'):
            with patch.dict(os.environ, {
                'PORT': '3001',
                'HOST': '0.0.0.0'
            }, clear=True):
                # Remove SSL env vars if they exist
                os.environ.pop('SSL_CERT_PATH', None)
                os.environ.pop('SSL_KEY_PATH', None)

                from start_server import main
                main()

        # Verify uvicorn.run was called without SSL config
        mock_uvicorn.assert_called_once()
        call_kwargs = mock_uvicorn.call_args.kwargs

        assert 'ssl_certfile' not in call_kwargs
        assert 'ssl_keyfile' not in call_kwargs

    def test_missing_cert_file_exits(self, temp_certs):
        """Test that missing certificate file causes exit"""
        _, key_path = temp_certs
        non_existent_cert = "/path/to/nonexistent/cert.pem"

        with patch.dict(os.environ, {
            'SSL_CERT_PATH': non_existent_cert,
            'SSL_KEY_PATH': key_path,
        }):
            from start_server import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_missing_key_file_exits(self, temp_certs):
        """Test that missing key file causes exit"""
        cert_path, _ = temp_certs
        non_existent_key = "/path/to/nonexistent/key.pem"

        with patch.dict(os.environ, {
            'SSL_CERT_PATH': cert_path,
            'SSL_KEY_PATH': non_existent_key,
        }):
            from start_server import main

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    def test_default_host_and_port(self, mock_uvicorn):
        """Test default host and port values"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('HOST', None)
            os.environ.pop('PORT', None)
            os.environ.pop('SSL_CERT_PATH', None)
            os.environ.pop('SSL_KEY_PATH', None)

            from start_server import main
            main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs['host'] == '0.0.0.0'
        assert call_kwargs['port'] == 3001

    def test_custom_host_and_port(self, mock_uvicorn):
        """Test custom host and port from environment variables"""
        with patch.dict(os.environ, {
            'HOST': '127.0.0.1',
            'PORT': '8080'
        }):
            from start_server import main
            main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs['host'] == '127.0.0.1'
        assert call_kwargs['port'] == 8080

    def test_reload_flag_enabled(self, mock_uvicorn):
        """Test reload flag when RELOAD=true"""
        with patch.dict(os.environ, {'RELOAD': 'true'}):
            from start_server import main
            main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs['reload'] is True

    def test_reload_flag_disabled(self, mock_uvicorn):
        """Test reload flag when RELOAD=false"""
        with patch.dict(os.environ, {'RELOAD': 'false'}):
            from start_server import main
            main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs['reload'] is False

    def test_dotenv_loaded(self, temp_certs, mock_uvicorn):
        """Test that load_dotenv is called to load .env file"""
        cert_path, key_path = temp_certs

        # Mock load_dotenv to simulate loading .env variables
        def mock_load_dotenv_func():
            os.environ['SSL_CERT_PATH'] = cert_path
            os.environ['SSL_KEY_PATH'] = key_path
            os.environ['PORT'] = '4000'

        with patch('start_server.load_dotenv', side_effect=mock_load_dotenv_func):
            with patch.dict(os.environ, {}, clear=True):
                from start_server import main
                main()

        call_kwargs = mock_uvicorn.call_args.kwargs
        assert call_kwargs['port'] == 4000
        assert 'ssl_certfile' in call_kwargs
        assert 'ssl_keyfile' in call_kwargs
        # Verify the paths are what we set in mock .env
        assert call_kwargs['ssl_certfile'] == cert_path
        assert call_kwargs['ssl_keyfile'] == key_path


class TestCertificateFiles:
    """Test certificate file handling"""

    def test_cert_permissions(self):
        """Test that generated certificates have correct permissions"""
        # This test assumes certificates were generated
        cert_path = "./certs/cert.pem"
        key_path = "./certs/key.pem"

        if os.path.exists(cert_path) and os.path.exists(key_path):
            # Check cert.pem permissions (should be 644 - readable by all)
            cert_stat = os.stat(cert_path)
            cert_perms = oct(cert_stat.st_mode)[-3:]
            assert cert_perms == '644', f"cert.pem should have 644 permissions, got {cert_perms}"

            # Check key.pem permissions (should be 600 - readable only by owner)
            key_stat = os.stat(key_path)
            key_perms = oct(key_stat.st_mode)[-3:]
            assert key_perms == '600', f"key.pem should have 600 permissions, got {key_perms}"
        else:
            pytest.skip("Certificates not generated, run ./generate_cert.sh first")

    def test_cert_directory_exists(self):
        """Test that certs directory exists after generation"""
        certs_dir = "./certs"

        if os.path.exists(certs_dir):
            assert os.path.isdir(certs_dir)
            assert os.path.exists(os.path.join(certs_dir, "cert.pem"))
            assert os.path.exists(os.path.join(certs_dir, "key.pem"))
        else:
            pytest.skip("Certificates directory not found, run ./generate_cert.sh first")


class TestHTTPSIntegration:
    """Integration tests for HTTPS functionality"""

    def test_https_server_config_validation(self):
        """Test that HTTPS server configuration is properly validated"""
        # Test with non-existent cert
        with patch.dict(os.environ, {
            'SSL_CERT_PATH': '/nonexistent/cert.pem',
            'SSL_KEY_PATH': '/nonexistent/key.pem'
        }):
            from start_server import main

            with pytest.raises(SystemExit):
                main()

    def test_app_import(self):
        """Test that main app can be imported successfully"""
        from src.main import app
        assert app is not None

    def test_env_example_matches_usage(self):
        """Test that .env.example contains all necessary variables"""
        env_example_path = ".env.example"

        if os.path.exists(env_example_path):
            with open(env_example_path, 'r') as f:
                content = f.read()

            # Check that all SSL-related vars are documented
            assert 'SSL_CERT_PATH' in content or 'ssl_cert' in content.lower()
            assert 'SSL_KEY_PATH' in content or 'ssl_key' in content.lower()
            assert 'LOGLIFE_API_KEY' in content
            assert 'PORT' in content
        else:
            pytest.skip(".env.example not found")
