"""
Test suite for bunnystream package initialization and version detection.
"""

import sys
from unittest.mock import patch


class TestPackageInitialization:
    """Test package initialization and version detection edge cases."""

    def test_version_fallback_importlib_metadata_missing(self):
        """Test version fallback when importlib.metadata is missing."""
        # Temporarily remove bunnystream from sys.modules to force re-import
        original_modules = sys.modules.copy()

        # Remove bunnystream modules
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith("bunnystream")]
        for module in modules_to_remove:
            del sys.modules[module]

        try:
            # Mock importlib.metadata.version to raise ImportError
            with patch("importlib.metadata.version", side_effect=ImportError):
                # Mock importlib_metadata.version to succeed
                with patch("importlib_metadata.version", return_value="1.0.0") as mock_version:
                    import bunnystream

                    # The fallback should have been called
                    mock_version.assert_called_once_with("bunnystream")
                    assert bunnystream.__version__ == "1.0.0"
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_version_fallback_both_import_errors(self):
        """Test version fallback when both import methods fail."""
        # Temporarily remove bunnystream from sys.modules to force re-import
        original_modules = sys.modules.copy()

        # Remove bunnystream modules
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith("bunnystream")]
        for module in modules_to_remove:
            del sys.modules[module]

        try:
            # Mock both version functions to raise ImportError
            with patch("importlib.metadata.version", side_effect=ImportError):
                with patch("importlib_metadata.version", side_effect=ImportError):
                    import bunnystream

                    # Should fall back to development version
                    assert bunnystream.__version__ == "0.0.1-dev"
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_version_fallback_general_exception(self):
        """Test version fallback when general exception occurs."""
        # Temporarily remove bunnystream from sys.modules to force re-import
        original_modules = sys.modules.copy()

        # Remove bunnystream modules
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith("bunnystream")]
        for module in modules_to_remove:
            del sys.modules[module]

        try:
            # Mock to raise a general exception (not ImportError)
            with patch("importlib.metadata.version", side_effect=Exception("Package not found")):
                import bunnystream

                # Should fall back to development version
                assert bunnystream.__version__ == "0.0.1-dev"
        finally:
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_all_exports_available(self):
        """Test that all expected exports are available."""
        import bunnystream

        # Check that all items in __all__ are actually available
        for item in bunnystream.__all__:
            assert hasattr(bunnystream, item), f"{item} not available in bunnystream"

        # Check specific imports
        assert hasattr(bunnystream, "Warren")
        assert hasattr(bunnystream, "bunny_logger")
        assert hasattr(bunnystream, "get_bunny_logger")
        assert hasattr(bunnystream, "configure_bunny_logger")
        assert hasattr(bunnystream, "__version__")
