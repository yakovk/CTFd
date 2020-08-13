#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from flask import url_for
from freezegun import freeze_time

from CTFd.cache import clear_pages
from CTFd.utils import set_config
from CTFd.utils.config.pages import get_pages
from CTFd.utils.encoding import hexencode
from tests.helpers import (
    create_ctfd,
    destroy_ctfd,
    gen_challenge,
    gen_file,
    gen_page,
    login_as_user,
    register_user,
    LiveServer,
)
from playwright import sync_playwright
import time


def test_browser_index():
    """Does the index page return a 200 by default"""
    app = create_ctfd(server_name="localhost:8943")
    with LiveServer(app):
        with sync_playwright() as p:
            for browser_type in [p.chromium, p.firefox]:
                browser = browser_type.launch()
                page = browser.newPage()
                page.goto('http://localhost:8943/')
                page.screenshot(path=f'example-{browser_type.name}.png')
                browser.close()
    destroy_ctfd(app)