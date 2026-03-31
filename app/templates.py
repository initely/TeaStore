"""
Утилиты для работы с шаблонами
"""
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

# Настройка Jinja2 для шаблонов
TEMPLATES_DIR = "templates"
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

# Добавляем полезные функции в шаблоны
def range_filter(start, stop=None, step=1):
    """Фильтр для range в Jinja2"""
    if stop is None:
        return list(range(start))
    return list(range(start, stop, step))

env.filters['range'] = range_filter


def render_template(template_name: str, context: dict = None):
    """Рендеринг HTML шаблона"""
    if context is None:
        context = {}
    template = env.get_template(template_name)
    return HTMLResponse(content=template.render(**context))

