"""Controller that leaves the adapter's MELCloud connection setting alone.

The adapter stores the CONNECT element of a /smart request as a setting, it
does not treat it as a per-request flag. The stock status request sends
CONNECT ON, so every poll re-enables the connection to the MELCloud servers
and a local-only installation can never stay disconnected. A request with no
CONNECT element returns the same status payload and does not change the
setting, so that is what this controller polls with.

Local control over /smart keeps working while the cloud connection is off.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pymitsubishi import MitsubishiAPI, MitsubishiController, ParsedDeviceState


def build_status_payload(connect: bool | None) -> str:
    """Return the /smart status payload for a given cloud connection intent.

    connect=None leaves the setting untouched. True enables the cloud
    connection and False disables it.
    """
    if connect is None:
        return "<CSV></CSV>"
    return f"<CSV><CONNECT>{'ON' if connect else 'OFF'}</CONNECT></CSV>"


def read_cloud_connect(response: str) -> bool | None:
    """Return the cloud connection setting the adapter reported, if any."""
    try:
        root = ET.fromstring(response)
    except ET.ParseError:
        return None
    element = root.find(".//CONNECT")
    if element is None or element.text is None:
        return None
    return element.text.strip().upper() == "ON"


class MitsubishiLocalController(MitsubishiController):
    """MitsubishiController that never changes the cloud connection on a poll."""

    def __init__(self, api: MitsubishiAPI) -> None:
        """Initialize the controller."""
        super().__init__(api=api)
        # Cloud connection setting last reported by the adapter, None until the
        # first successful status fetch.
        self.cloud_connect: bool | None = None

    def fetch_status(self, connect: bool | None = None) -> ParsedDeviceState:
        """Fetch device status, preserving the cloud connection setting."""
        response = self.api.make_request(build_status_payload(connect))
        state = self._parse_status_response(response)
        self.cloud_connect = read_cloud_connect(response)
        return state

    def set_cloud_connect(self, enabled: bool) -> ParsedDeviceState:
        """Enable or disable the adapter's connection to the MELCloud servers."""
        return self.fetch_status(connect=enabled)
