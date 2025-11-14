"""Integration tests for Vision Capture MCP Server

Tests the MCP server's tool invocations and end-to-end functionality.
"""

import pytest
import sys
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mcp-servers" / "vision-capture"))

# Test utilities for MCP
from mcp.types import Tool


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config(temp_dir):
    """Create mock configuration"""
    return {
        'vision': {
            'enabled': True,
            'save_images': True,
            'image_quality': 85,
            'retention_days': 7,
            'ocr_language': 'en'
        },
        'storage': {
            'database': str(Path(temp_dir) / 'test.db')
        }
    }


class TestVisionMCPServer:
    """Integration tests for Vision MCP Server"""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that all expected tools are listed"""
        # Import server module
        import server

        # Get tool list
        tools = await server.list_tools()

        # Verify all expected tools are present
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            'capture_screen',
            'capture_region',
            'get_window_title',
            'search_captures'
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found"

        # Verify each tool has proper schema
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert tool.description is not None
            assert len(tool.description) > 0

    @pytest.mark.asyncio
    async def test_capture_screen_schema(self):
        """Test capture_screen tool schema"""
        import server

        tools = await server.list_tools()
        capture_screen = next(t for t in tools if t.name == 'capture_screen')

        schema = capture_screen.inputSchema
        assert schema['type'] == 'object'
        assert 'properties' in schema
        assert 'trigger_reason' in schema['properties']

    @pytest.mark.asyncio
    async def test_capture_region_schema(self):
        """Test capture_region tool schema"""
        import server

        tools = await server.list_tools()
        capture_region = next(t for t in tools if t.name == 'capture_region')

        schema = capture_region.inputSchema
        assert schema['type'] == 'object'
        assert 'required' in schema
        assert 'x' in schema['required']
        assert 'y' in schema['required']
        assert 'width' in schema['required']
        assert 'height' in schema['required']

    @pytest.mark.asyncio
    async def test_search_captures_schema(self):
        """Test search_captures tool schema"""
        import server

        tools = await server.list_tools()
        search_tool = next(t for t in tools if t.name == 'search_captures')

        schema = search_tool.inputSchema
        assert schema['type'] == 'object'
        assert 'required' in schema
        assert 'query' in schema['required']
        assert 'limit' in schema['properties']

    @pytest.mark.asyncio
    @patch('mcp_servers.vision_capture.server.vision')
    @patch('mcp_servers.vision_capture.server.db')
    async def test_get_window_title_call(self, mock_db, mock_vision):
        """Test calling get_window_title tool"""
        import server

        # Mock vision.get_window_title()
        mock_vision.get_window_title.return_value = "Test Window - VSCode"

        # Call tool
        result = await server.call_tool('get_window_title', {})

        # Verify result
        assert len(result) == 1
        assert result[0].type == 'text'
        assert 'Test Window - VSCode' in result[0].text

    @pytest.mark.asyncio
    @patch('mcp_servers.vision_capture.server.vision')
    @patch('mcp_servers.vision_capture.server.db')
    async def test_capture_screen_call(self, mock_db, mock_vision):
        """Test calling capture_screen tool"""
        import server
        from shared.models.screen_capture import ScreenCapture
        from datetime import datetime

        # Mock capture response
        mock_capture = ScreenCapture(
            timestamp=datetime.now().isoformat(),
            window_title="Test Window",
            ocr_text="Hello World\nThis is a test",
            ocr_confidence=0.95,
            image_path="/tmp/screenshot.jpg",
            image_hash="abc123",
            trigger_reason="test"
        )
        mock_vision.capture_screen.return_value = mock_capture

        # Call tool
        result = await server.call_tool('capture_screen', {'trigger_reason': 'test'})

        # Verify result
        assert len(result) == 1
        assert result[0].type == 'text'
        assert 'Test Window' in result[0].text
        assert 'Hello World' in result[0].text
        assert '95.00%' in result[0].text or '95%' in result[0].text

        # Verify vision.capture_screen was called
        mock_vision.capture_screen.assert_called_once_with(trigger_reason='test')

    @pytest.mark.asyncio
    @patch('mcp_servers.vision_capture.server.vision')
    @patch('mcp_servers.vision_capture.server.db')
    async def test_capture_region_call(self, mock_db, mock_vision):
        """Test calling capture_region tool"""
        import server
        from shared.models.screen_capture import ScreenCapture
        from datetime import datetime

        # Mock capture response
        mock_capture = ScreenCapture(
            timestamp=datetime.now().isoformat(),
            window_title="Test Window",
            ocr_text="Region text",
            ocr_confidence=0.88,
            image_path="/tmp/region.jpg",
            image_hash="def456",
            trigger_reason="test",
            metadata={"region": {"x": 100, "y": 200, "width": 300, "height": 400}}
        )
        mock_vision.capture_region.return_value = mock_capture

        # Call tool
        arguments = {
            'x': 100,
            'y': 200,
            'width': 300,
            'height': 400,
            'trigger_reason': 'test'
        }
        result = await server.call_tool('capture_region', arguments)

        # Verify result
        assert len(result) == 1
        assert result[0].type == 'text'
        assert '100' in result[0].text  # Should show region coordinates
        assert 'Region text' in result[0].text

        # Verify vision.capture_region was called
        mock_vision.capture_region.assert_called_once()

    @pytest.mark.asyncio
    @patch('mcp_servers.vision_capture.server.vision')
    @patch('mcp_servers.vision_capture.server.db')
    async def test_search_captures_call(self, mock_db, mock_vision):
        """Test calling search_captures tool"""
        import server
        from datetime import datetime

        # Mock search results
        mock_results = [
            {
                'timestamp': datetime.now().isoformat(),
                'window_title': 'VSCode',
                'ocr_text': 'Python code example with search term',
                'ocr_confidence': 0.92,
                'image_hash': 'hash1'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'window_title': 'Browser',
                'ocr_text': 'Documentation about search functionality',
                'ocr_confidence': 0.89,
                'image_hash': 'hash2'
            }
        ]
        mock_vision.search_captures.return_value = mock_results

        # Call tool
        result = await server.call_tool('search_captures', {'query': 'search', 'limit': 10})

        # Verify result
        assert len(result) == 1
        assert result[0].type == 'text'
        assert 'Found 2' in result[0].text
        assert 'VSCode' in result[0].text
        assert 'Browser' in result[0].text

        # Verify search was called
        mock_vision.search_captures.assert_called_once_with('search', 10)

    @pytest.mark.asyncio
    @patch('mcp_servers.vision_capture.server.vision')
    @patch('mcp_servers.vision_capture.server.db')
    async def test_search_no_results(self, mock_db, mock_vision):
        """Test search with no results"""
        import server

        # Mock empty results
        mock_vision.search_captures.return_value = []

        # Call tool
        result = await server.call_tool('search_captures', {'query': 'nonexistent'})

        # Verify result
        assert len(result) == 1
        assert result[0].type == 'text'
        assert 'No captures found' in result[0].text

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test calling unknown tool returns error"""
        import server

        # Call unknown tool
        result = await server.call_tool('unknown_tool', {})

        # Should return error message
        assert len(result) == 1
        assert result[0].type == 'text'
        assert 'Unknown tool' in result[0].text or 'not initialized' in result[0].text

    @pytest.mark.asyncio
    @patch('mcp_servers.vision_capture.server.vision')
    @patch('mcp_servers.vision_capture.server.db')
    async def test_tool_error_handling(self, mock_db, mock_vision):
        """Test that tool errors are handled gracefully"""
        import server

        # Mock an error
        mock_vision.capture_screen.side_effect = Exception("Test error")

        # Call tool
        result = await server.call_tool('capture_screen', {})

        # Should return error message
        assert len(result) == 1
        assert result[0].type == 'text'
        assert 'Error' in result[0].text or 'error' in result[0].text


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_dir, mock_config):
        """Test complete workflow: capture -> store -> search"""
        # This test would require a full MCP server instance
        # For now, we'll test the components separately

        from shared.storage.database import Database
        from mcp_servers.vision_capture.capture import VisionCapture
        from datetime import datetime

        # Setup
        db_path = Path(temp_dir) / "test.db"
        db = Database(str(db_path))
        db.connect()
        db.create_schema()

        vision = VisionCapture(
            db=db,
            screenshots_dir=str(Path(temp_dir) / "screenshots"),
            save_images=False  # Don't save images in test
        )

        # This test would need mocking for screen capture
        # Just verify the components are connected properly
        assert vision.db == db
        assert db.connection is not None

        # Cleanup
        db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
