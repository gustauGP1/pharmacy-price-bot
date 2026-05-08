"""
Inline keyboards for Telegram bot.
Provides interactive buttons for user actions.
"""

from typing import List, Dict, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Get main menu keyboard.
    
    Returns:
        InlineKeyboardMarkup: Main menu keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("🔍 Buscar Medicamento", callback_data="search"),
        ],
        [
            InlineKeyboardButton("📊 Mis Estadísticas", callback_data="stats"),
            InlineKeyboardButton("❓ Ayuda", callback_data="help"),
        ],
        [
            InlineKeyboardButton("ℹ️ Acerca de", callback_data="about"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_search_results_keyboard(results: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Get keyboard for search results.
    
    Args:
        results: List of search results
        
    Returns:
        InlineKeyboardMarkup: Results keyboard
    """
    keyboard = []
    
    # Add buttons for each result (max 5)
    for i, result in enumerate(results[:5]):
        product_name = result.get("product_name", "Producto")
        best_price = result.get("best_price", 0)
        
        # Truncate name if too long
        if len(product_name) > 30:
            product_name = product_name[:27] + "..."
        
        button_text = f"💊 {product_name} - ${best_price:,.0f}"
        callback_data = f"result_{i}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("🔄 Nueva Búsqueda", callback_data="search"),
        InlineKeyboardButton("🏠 Menú", callback_data="menu"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_product_detail_keyboard(product: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Get keyboard for product details.
    
    Args:
        product: Product data
        
    Returns:
        InlineKeyboardMarkup: Product detail keyboard
    """
    keyboard = []
    
    # Add buttons for each pharmacy price
    for price_info in product.get("prices", [])[:3]:
        pharmacy = price_info.get("pharmacy_display", "Farmacia")
        price = price_info.get("price", 0)
        url = price_info.get("url", "")
        
        button_text = f"🏪 {pharmacy} - ${price:,.0f}"
        
        if url:
            keyboard.append([InlineKeyboardButton(button_text, url=url)])
        else:
            keyboard.append([InlineKeyboardButton(button_text, callback_data="no_url")])
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("⬅️ Volver", callback_data="back"),
        InlineKeyboardButton("🏠 Menú", callback_data="menu"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_pharmacy_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for pharmacy selection.
    
    Returns:
        InlineKeyboardMarkup: Pharmacy selection keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("🟢 Cruz Verde", callback_data="pharmacy_cruz_verde"),
        ],
        [
            InlineKeyboardButton("🔵 Salcobrand", callback_data="pharmacy_salcobrand"),
        ],
        [
            InlineKeyboardButton("🔴 Farmacias Ahumada", callback_data="pharmacy_ahumada"),
        ],
        [
            InlineKeyboardButton("🌟 Todas", callback_data="pharmacy_all"),
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data="back"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_help_keyboard() -> InlineKeyboardMarkup:
    """
    Get help keyboard.
    
    Returns:
        InlineKeyboardMarkup: Help keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("🔍 Cómo Buscar", callback_data="help_search"),
        ],
        [
            InlineKeyboardButton("💰 Comparar Precios", callback_data="help_compare"),
        ],
        [
            InlineKeyboardButton("📱 Comandos", callback_data="help_commands"),
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data="menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """
    Get confirmation keyboard.
    
    Args:
        action: Action to confirm
        
    Returns:
        InlineKeyboardMarkup: Confirmation keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ No", callback_data=f"cancel_{action}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(
    current_page: int,
    total_pages: int,
    prefix: str = "page"
) -> InlineKeyboardMarkup:
    """
    Get pagination keyboard.
    
    Args:
        current_page: Current page number (0-indexed)
        total_pages: Total number of pages
        prefix: Callback data prefix
        
    Returns:
        InlineKeyboardMarkup: Pagination keyboard
    """
    keyboard = []
    buttons = []
    
    # Previous button
    if current_page > 0:
        buttons.append(
            InlineKeyboardButton("⬅️ Anterior", callback_data=f"{prefix}_{current_page - 1}")
        )
    
    # Page indicator
    buttons.append(
        InlineKeyboardButton(f"📄 {current_page + 1}/{total_pages}", callback_data="noop")
    )
    
    # Next button
    if current_page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton("Siguiente ➡️", callback_data=f"{prefix}_{current_page + 1}")
        )
    
    keyboard.append(buttons)
    
    # Back to menu
    keyboard.append([
        InlineKeyboardButton("🏠 Menú Principal", callback_data="menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_share_keyboard(text: str) -> InlineKeyboardMarkup:
    """
    Get share keyboard.
    
    Args:
        text: Text to share
        
    Returns:
        InlineKeyboardMarkup: Share keyboard
    """
    # URL encode the text
    from urllib.parse import quote
    encoded_text = quote(text)
    
    keyboard = [
        [
            InlineKeyboardButton(
                "📤 Compartir",
                url=f"https://t.me/share/url?url={encoded_text}"
            ),
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data="back"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_price_alert_keyboard(medicine_id: str) -> InlineKeyboardMarkup:
    """
    Get price alert keyboard.
    
    Args:
        medicine_id: Medicine ID
        
    Returns:
        InlineKeyboardMarkup: Price alert keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "🔔 Activar Alerta de Precio",
                callback_data=f"alert_enable_{medicine_id}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🔕 Desactivar Alerta",
                callback_data=f"alert_disable_{medicine_id}"
            ),
        ],
        [
            InlineKeyboardButton("⬅️ Volver", callback_data="back"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def remove_keyboard() -> Dict[str, bool]:
    """
    Get remove keyboard markup.
    
    Returns:
        dict: Remove keyboard markup
    """
    return {"remove_keyboard": True}


__all__ = [
    "get_main_menu_keyboard",
    "get_search_results_keyboard",
    "get_product_detail_keyboard",
    "get_pharmacy_selection_keyboard",
    "get_help_keyboard",
    "get_confirmation_keyboard",
    "get_pagination_keyboard",
    "get_share_keyboard",
    "get_price_alert_keyboard",
    "remove_keyboard",
]

# Made with Bob