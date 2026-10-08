"""Offline tests must never connect to paid providers or other outbound services."""

import socket

import pytest


@pytest.fixture(autouse=True)
def offline_network_guard(monkeypatch):
    def denied(*args, **kwargs):
        raise RuntimeError("outbound network disabled during offline pytest")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
