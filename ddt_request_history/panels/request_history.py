from __future__ import absolute_import, unicode_literals
import json
import uuid
import logging
import sys

from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

import debug_toolbar
from debug_toolbar import settings as dt_settings
from debug_toolbar.toolbar import DebugToolbar
from debug_toolbar.panels import Panel
import os
from django.template.context import Context
from django.template import Template

try:
    from collections import OrderedDict, Callable
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

logger = logging.getLogger(__name__)

DEBUG_TOOLBAR_URL_PREFIX = getattr(settings, 'DEBUG_TOOLBAR_URL_PREFIX', '/__debug__')

def allow_ajax(request):
    """
    Default function to determine whether to show the toolbar on a given page.
    """
    if request.META.get('REMOTE_ADDR', None) not in settings.INTERNAL_IPS:
        return False
    if request.get_full_path().startswith(DEBUG_TOOLBAR_URL_PREFIX) and \
            request.GET.get('panel_id', None) != 'RequestHistoryPanel':
        return False
    return bool(settings.DEBUG)


def patched_store(self):
    if self.store_id:  # don't save if already have
        return
    self.store_id = uuid.uuid4().hex
    cls = type(self)
    cls._store[self.store_id] = self
    store_size = dt_settings.CONFIG.get(
        'RESULTS_CACHE_SIZE', dt_settings.CONFIG.get('RESULTS_STORE_SIZE', 10))
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

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            if view_func == debug_toolbar.views.render_panel and \
                    request.GET.get('panel_id', None) == self.panel_id:
                return HttpResponse(self.content)
        except AttributeError:
            pass

    def process_response(self, request, response):
        self.record_stats({
            'request_url': request.get_full_path(),
            'post': json.dumps((request.POST), sort_keys=True, indent=4),
            'time': datetime.now(),
        })

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

        template_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'request_history.html'
        )
        t = Template(open(template_path).read())
        return t.render(Context({
            'toolbars': OrderedDict(reversed(list(toolbars.items()))),
            'trunc_length': dt_settings.CONFIG.get('RH_POST_TRUNC_LENGTH', 0)
        }))

    def disable_instrumentation(self):
        if not self.toolbar.stats[self.panel_id]['request_url'].startswith(DEBUG_TOOLBAR_URL_PREFIX):
            self.toolbar.store()
