import sys

# Compatibility patch for Python 3.14 pre-release where copy(super()) in Django's BaseContext
# raises AttributeError: 'super' object has no attribute 'dicts'
if sys.version_info >= (3, 14):
    try:
        from django.template import context

        def _patched_base_context_copy(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        def _patched_context_copy(self):
            duplicate = _patched_base_context_copy(self)
            duplicate.render_context = self.render_context.__copy__()
            duplicate.use_l10n = self.use_l10n
            duplicate.use_tz = self.use_tz
            duplicate.template_name = self.template_name
            return duplicate

        context.BaseContext.__copy__ = _patched_base_context_copy
        context.Context.__copy__ = _patched_context_copy
    except Exception:
        pass
