"""
HTTP client that communicates with the Fusion 360 add-in's bridge server.
Uses only urllib (stdlib) so it has no external dependencies of its own,
though the MCP server that imports this does use third-party packages.
"""

import urllib.request
import urllib.error
import json
import os


class FusionClient:
    """Sends commands to the Fusion bridge HTTP server."""

    def __init__(self, host, port, token_path=None):
        self.url = f'http://{host}:{port}'
        self.token_path = token_path or os.path.join(
            os.path.expanduser('~'), '.fusion_mcp', 'auth_token'
        )

    def _read_token(self):
        """Read the current auth token from the shared file."""
        try:
            with open(self.token_path) as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def call(self, payload):
        """
        Send a command to the Fusion bridge and return the response.

        Args:
            payload: dict with 'operation' and operation-specific fields

        Returns:
            str: JSON response from the bridge (success or error)

        Raises:
            ConnectionError: If the Fusion bridge is not running
        """
        token = self._read_token()
        if not token:
            return json.dumps({
                'success': False,
                'error': f'No auth token found at {self.token_path}. '
                         'Is Fusion running with the fusion_bridge add-in active?'
            })

        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            self.url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                response_body = resp.read().decode('utf-8')
                return response_body
        except urllib.error.URLError as e:
            if 'Connection refused' in str(e):
                return json.dumps({
                    'success': False,
                    'error': 'Cannot connect to Fusion 360. Is Fusion running with the '
                             'fusion_bridge add-in active? Check the Add-Ins dialog.'
                })
            return json.dumps({
                'success': False,
                'error': f'HTTP error: {str(e)}'
            })
        except Exception as e:
            return json.dumps({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            })

    def ping(self):
        """Check if the Fusion bridge is reachable."""
        return self.call({'operation': 'ping'})
