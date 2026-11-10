"""
Fuentes curadas para ClientSettings.font_family (#AUD-11 Paso 3).

Lista cerrada a propósito: texto libre permite guardar una fuente sin
Google Font asociada, que rompe el fallback silenciosamente (mismo tipo
de bug que #BUG-01 -- un campo que existe en el modelo pero no está
conectado a nada real). Son las 4 fuentes que ya usan los temas reales
hoy como --font-display (ver docs/design-system.md): Outfit (servelec,
electricidad), Space Grotesk (andesscale), Fraunces (ranchocachimba).
Inter es el fallback universal.

Los pesos de abajo son para uso como --font-sans (cuerpo de texto) --
la fuente de --font-display de cada tema sigue fija por diseño, no la
controla este choice.
"""

FONT_CHOICES = [
    ('Inter', 'Inter'),
    ('Outfit', 'Outfit'),
    ('Fraunces', 'Fraunces'),
    ('Space Grotesk', 'Space Grotesk'),
]

_GOOGLE_FONTS_QUERY = {
    'Inter': 'Inter:wght@400;500;600;700',
    'Outfit': 'Outfit:wght@400;500;600;700',
    'Fraunces': 'Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700',
    'Space Grotesk': 'Space+Grotesk:wght@400;500;600;700',
}


def google_fonts_query(font_name):
    """
    Fragmento `family=...` para el <link> de Google Fonts de la fuente
    elegida. Si el valor guardado no está en la lista curada (dato viejo
    o corrupto), cae a Inter -- nunca a una URL rota.
    """
    return _GOOGLE_FONTS_QUERY.get(font_name, _GOOGLE_FONTS_QUERY['Inter'])
