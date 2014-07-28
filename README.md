Request History Panel for Django Debug Toolbar
==============================================


Adds a request history panel to Django Debug Toolbar with the option for ajax support.

### Install ###


```bash
pip install git+https://github.com/djsutho/django-debug-toolbar-request-history.git

```


### Config (in settings.py) ###

To ```DEBUG_TOOLBAR_PANELS``` add ```'ddt_request_history.panels.request_history.RequestHistoryPanel'``` e.g.:

```python

DEBUG_TOOLBAR_PANELS = [
    'ddt_request_history.panels.request_history.RequestHistoryPanel',
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

To record ajax requests add ```SHOW_TOOLBAR_CALLBACK``` to ```DEBUG_TOOLBAR_CONFIG``` e.g.:


```python
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'ddt_request_history.panels.request_history.allow_ajax',
}
```



to change the number of store requests add ```RESULTS_STORE_SIZE``` to ```DEBUG_TOOLBAR_CONFIG``` e.g.:


```python
DEBUG_TOOLBAR_CONFIG = {
    'RESULTS_STORE_SIZE': 100,
}
```



### TODO ###
* Clean-up
* Change the storage to survive server reloads (maybe use cache or session).