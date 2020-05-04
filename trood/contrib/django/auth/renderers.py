from rest_framework.renderers import JSONRenderer


def render_callback(renderer):
    """Wrapper which call base class render if no data returned"""
    def wrapped_renderer(*args, **kwargs):
        response = renderer(*args, **kwargs)
        if not response:
            response = JSONRenderer.render(*args, **kwargs)
        return response
    return wrapped_renderer


class MaskJSONRenderer(JSONRenderer):
    """Renderer which mask data by abac rule and pass through"""
    @render_callback
    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        if not ('request' in renderer_context and hasattr(renderer_context['request'], 'abac')):
            return
        abac = renderer_context['request'].abac
        if not isinstance(data, list):
            return
        for defer in abac.mask:
            for d in data:
                d.pop(defer)
        return super().render(data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)
