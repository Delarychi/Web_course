import base64
from django import template
from io import BytesIO
from PIL import Image

register = template.Library()

@register.filter
def base64_image(image_data):
    """
    Фильтр для преобразования изображения в формат Base64.
    """
    if image_data:
        # Преобразуем байтовые данные в Base64
        return base64.b64encode(image_data).decode('utf-8')
    return ''