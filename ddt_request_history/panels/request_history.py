from __future__ import absolute_import, unicode_literals

import json
import logging
import os
import re
import sys
import threading
import uuid

import debug_toolbar

from collections import OrderedDict
from datetime import datetime
from distutils.version import LooseVersion

from django.conf import settings
from django.template import Template
from django.template.backends.django import DjangoTemplates
from django.template.context import Context
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import Panel
from debug_toolbar.settings import get_config
from debug_toolbar.toolbar import DebugToolbar

try:
    from collections.abc import Callable
except ImportError:  # Python < 3.3
    from collections import Callable

try:
    toolbar_version = LooseVersion(debug_toolbar.VERSION)
except:
    toolbar_version = LooseVersion('0')

logger = logging.getLogger(__name__)

DEBUG_TOOLBAR_URL_PREFIX = getattr(settings, 'DEBUG_TOOLBAR_URL_PREFIX', '/__debug__')

_original_middleware_call = None

def patched_middleware_call(self, request):
    # Decide whether the toolbar is active for this request.
    show_toolbar = debug_toolbar.middleware.get_show_toolbar()
    if not show_toolbar(request):
        return self.get_response(request)

    toolbar = DebugToolbar(request, self.get_response)

    # Activate instrumentation ie. monkey-patch.
    for panel in toolbar.enabled_panels:
        panel.enable_instrumentation()
    try:
        # Run panels like Django middleware.
        response = toolbar.process_request(request)
    finally:
        # Deactivate instrumentation ie. monkey-unpatch. This must run
        # regardless of the response. Keep 'return' clauses below.
        for panel in reversed(toolbar.enabled_panels):
            panel.disable_instrumentation()
    # When the toolbar will be inserted for sure, generate the stats.
    for panel in reversed(toolbar.enabled_panels):
        panel.generate_stats(request, response)
        panel.generate_server_timing(request, response)

    response = self.generate_server_timing_header(
        response, toolbar.enabled_panels
    )

    # Check for responses where the toolbar can't be inserted.
    content_encoding = response.get("Content-Encoding", "")
    content_type = response.get("Content-Type", "").split(";")[0]
    if any(
        (
            getattr(response, "streaming", False),
            "gzip" in content_encoding,
            content_type not in debug_toolbar.middleware._HTML_TYPES,
        )
    ):
        return response

    # Collapse the toolbar by default if SHOW_COLLAPSED is set.
    if toolbar.config["SHOW_COLLAPSED"] and "djdt" not in request.COOKIES:
        response.set_cookie("djdt", "hide", 864000)

    # Insert the toolbar in the response.
    content = response.content.decode(response.charset)
    insert_before = get_config()["INSERT_BEFORE"]
    pattern = re.escape(insert_before)
    bits = re.split(pattern, content, flags=re.IGNORECASE)
    if len(bits) > 1:

        bits[-2] += toolbar.render_toolbar()
        response.content = insert_before.join(bits)
        if response.get("Content-Length", None):
            response["Content-Length"] = len(response.content)
    return response


def patch_middleware():
    if not this_module.middleware_patched:
        try:
            from debug_toolbar.middleware import DebugToolbarMiddleware
            this_module._original_middleware_call = DebugToolbarMiddleware.__call__
            DebugToolbarMiddleware.__call__ = patched_middleware_call
        except ImportError:
            return
        this_module.middleware_patched = True


middleware_patched = False
template = None
this_module = sys.modules[__name__]

# XXX: need to call this as early as possible but we have circular imports when
# running with gunicorn so also try a second later
patch_middleware()
threading.Timer(1.0, patch_middleware, ()).start()


def get_template():
    if this_module.template is None:
        template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'request_history.html'
        )
        with open(template_path) as template_file:
            this_module.template = Template(
                template_file.read(),
                engine=DjangoTemplates({'NAME': 'rh', 'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}).engine
        )
    return this_module.template


def allow_ajax(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if request.META.get('REMOTE_ADDR', None) not in settings.INTERNAL_IPS:
        return False
    return bool(settings.DEBUG)


def patched_store(self):
    if self.store_id:  # don't save if already have
        return
    self.store_id = uuid.uuid4().hex
    cls = type(self)
    cls._store[self.store_id] = self
    store_size = get_config().get('RESULTS_CACHE_SIZE', get_config().get('RESULTS_STORE_SIZE', 100))
    for dummy in range(len(cls._store) - store_size):
        try:
            # collections.OrderedDict
            cls._store.popitem(last=False)
        except TypeError:
            # django.utils.datastructures.SortedDict
            del cls._store[cls._store.keyOrder[0]]


def patched_fetch(cls, store_id):
    return cls._store.get(store_id)


DebugToolbar.store = patched_store
DebugToolbar.fetch = classmethod(patched_fetch)


class RequestHistoryPanel(Panel):
    """ A panel to display Request History """

    title = _("Request History")

    template = 'request_history.html'

    @property
    def nav_subtitle(self):
        return self.get_stats().get('request_url', '')

    def generate_stats(self, request, response):
        self.record_stats({
            'request_url': request.get_full_path(),
            'request_method': request.method,
            'post': json.dumps(request.POST, sort_keys=True, indent=4),
            'time': datetime.now(),
        })

    def process_request(self, request):
        self.record_stats({
            'request_url': request.get_full_path(),
            'request_method': request.method,
            'post': json.dumps(request.POST, sort_keys=True, indent=4),
            'time': datetime.now(),
        })
        return super().process_request(request)

    @property
    def content(self):
        """ Content of the panel when it's displayed in full screen. """
        toolbars = OrderedDict()
        for id, toolbar in DebugToolbar._store.items():
            content = {}
            for panel in toolbar.panels:
                panel_id = None
                nav_title = ''
                nav_subtitle = ''
                try:
                    panel_id = panel.panel_id
                    nav_title = panel.nav_title
                    nav_subtitle = panel.nav_subtitle() if isinstance(
                        panel.nav_subtitle, Callable) else panel.nav_subtitle
                except Exception:
                    logger.debug('Error parsing panel info:', exc_info=True)
                if panel_id is not None:
                    content.update({
                        panel_id: {
                            'panel_id': panel_id,
                            'nav_title': nav_title,
                            'nav_subtitle': nav_subtitle,
                        }
                    })
            toolbars[id] = {
                'toolbar': toolbar,
                'content': content
            }
        return get_template().render(Context({
            'toolbars': OrderedDict(reversed(list(toolbars.items()))),
            'trunc_length': get_config().get('RH_POST_TRUNC_LENGTH', 0)
        }))

    def disable_instrumentation(self):
        request_panel = self.toolbar.stats.get(self.panel_id)
        if request_panel and not request_panel.get('request_url', '').startswith(DEBUG_TOOLBAR_URL_PREFIX):
            self.toolbar.store()
