Request History Panel for Django Debug Toolbar
==============================================

Adds a request history panel to [Django Debug Toolbar](https://github.com/django-debug-toolbar/django-debug-toolbar) for viewing stats for different requests (with the option for ajax support).


### Install ###

```bash
pip install django-debug-toolbar-request-history
```

Then add the panel to ```DEBUG_TOOLBAR_PANELS``` (see the config section for more details).

**Note: only Django Debug Toolbar versions 2.0 and higher are now supported. For older versions try:**

```bash
pip install django-debug-toolbar-request-history==0.0.11
```

or for the development version:

```bash
pip install -e git+https://github.com/djsutho/django-debug-toolbar-request-history.git#egg=django-debug-toolbar-request-history
```

### Usage ###

* Click on the "Request History" panel in the toolbar to load the available requests
* Click on the request you are interested in (on the "Time" or "Path" part of the request) to load the toolbar for that request


**Notes**

Due to django-debug-toolbar reliance on thread-local:
- currently requests do not survive server reload, therefore, when using the dev server old requests will not be available after a code change is loaded
- if you get inconsistent request history each time you click on the panel, lower your server threads to 1


### Config (in settings.py) ###

To ```DEBUG_TOOLBAR_PANELS``` add ```'ddt_request_history.panels.request_history.RequestHistoryPanel'``` e.g.:

```python
DEBUG_TOOLBAR_PANELS = [
    'ddt_request_history.panels.request_history.RequestHistoryPanel',  # Here it is
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]
```

To change the number of stored requests add ```RESULTS_STORE_SIZE``` to ```DEBUG_TOOLBAR_CONFIG``` e.g.:

```python
DEBUG_TOOLBAR_CONFIG = {
    'RESULTS_STORE_SIZE': 100,
}
```

### TODO ###
* Clean-up
* Change the storage to survive server reloads (maybe use cache or session).
* Add tests
