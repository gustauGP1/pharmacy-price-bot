"""
Command handlers for Telegram bot.
Handles user commands and callback queries.
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.keyboards import (
    get_main_menu_keyboard,
    get_search_results_keyboard,
    get_product_detail_keyboard,
    get_help_keyboard,
)
from bot.middleware import log_handler, rate_limit, track_analytics
from services.comparison_service import get_comparison_service
from services.analytics_service import get_analytics_service
from utils.logger import logger


# ============================================
# COMMAND HANDLERS
# ============================================

@log_handler
@track_analytics("start")
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    user = update.effective_user
    
    welcome_message = (
        f"👋 ¡Hola {user.first_name}!\n\n"
        "🏥 Bienvenido al **Bot Comparador de Precios de Farmacias**\n\n"
        "Busca medicamentos y compara precios entre:\n"
        "🟢 Cruz Verde\n"
        "🔵 Salcobrand\n"
        "🔴 Farmacias Ahumada\n\n"
        "💡 **¿Cómo usar el bot?**\n"
        "• Usa `/buscar [medicamento]` para buscar\n"
        "• Ejemplo: `/buscar paracetamol`\n"
        "• O simplemente escribe el nombre del medicamento\n\n"
        "¡Ahorra dinero comprando inteligentemente! 💰"
    )
    
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )


@log_handler
@rate_limit
@track_analytics("search")
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /buscar command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    # Get search query from command args
    query = " ".join(context.args) if context.args else None
    
    if not query:
        await update.message.reply_text(
            "❓ Por favor especifica qué medicamento quieres buscar.\n\n"
            "**Ejemplo:**\n"
            "`/buscar paracetamol`\n"
            "`/buscar ibuprofeno 400mg`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Send "searching" message
    searching_msg = await update.message.reply_text(
        f"🔍 Buscando **{query}** en todas las farmacias...\n"
        "⏳ Esto puede tomar unos segundos.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        # Get comparison service
        comparison_service = await get_comparison_service()
        
        # Search and compare
        results = await comparison_service.search_and_compare(
            query=query,
            user_id=update.effective_user.id
        )
        
        # Delete searching message
        await searching_msg.delete()
        
        # Check if successful
        if not results.get("success", False):
            await update.message.reply_text(
                f"❌ Error al buscar: {results.get('error', 'Error desconocido')}"
            )
            return
        
        # Check if results found
        comparison_results = results.get("results", [])
        
        if not comparison_results:
            await update.message.reply_text(
                f"😕 No se encontraron resultados para **{query}**\n\n"
                "💡 **Sugerencias:**\n"
                "• Verifica la ortografía\n"
                "• Intenta con el nombre genérico\n"
                "• Usa menos palabras\n\n"
                "Ejemplo: `paracetamol` en lugar de `paracetamol 500mg comprimidos`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Format and send results
        await send_search_results(update, context, results)
        
        # Track analytics
        analytics_service = await get_analytics_service()
        await analytics_service.track_search(
            user_id=update.effective_user.id,
            query=query,
            results_count=len(comparison_results),
            duration_ms=int(results.get("duration_seconds", 0) * 1000),
            cache_hit=results.get("cache_hit", False)
        )
        
    except Exception as e:
        logger.exception(f"Error in search command: {e}")
        await searching_msg.delete()
        await update.message.reply_text(
            "❌ Ocurrió un error al buscar. Por favor intenta nuevamente."
        )


@log_handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /ayuda command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    help_text = (
        "📖 **Guía de Uso**\n\n"
        "**Comandos Disponibles:**\n"
        "• `/start` - Iniciar el bot\n"
        "• `/buscar [medicamento]` - Buscar y comparar precios\n"
        "• `/ayuda` - Mostrar esta ayuda\n"
        "• `/acerca` - Información sobre el bot\n\n"
        "**Cómo Buscar:**\n"
        "1️⃣ Usa el comando `/buscar` seguido del medicamento\n"
        "2️⃣ O simplemente escribe el nombre del medicamento\n"
        "3️⃣ Espera los resultados de las 3 farmacias\n"
        "4️⃣ Haz clic en un resultado para ver detalles\n\n"
        "**Ejemplos:**\n"
        "• `/buscar paracetamol`\n"
        "• `/buscar ibuprofeno 400mg`\n"
        "• `/buscar aspirina`\n\n"
        "**Consejos:**\n"
        "💡 Usa nombres genéricos para mejores resultados\n"
        "💡 Evita incluir dosis en la búsqueda inicial\n"
        "💡 El bot corrige automáticamente errores ortográficos\n\n"
        "¿Necesitas más ayuda? Contáctanos: @tu_usuario"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_help_keyboard()
    )


@log_handler
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /acerca command.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    about_text = (
        "ℹ️ **Acerca del Bot**\n\n"
        "🏥 **Pharmacy Price Bot**\n"
        "Versión 1.0.0\n\n"
        "**¿Qué hace este bot?**\n"
        "Compara precios de medicamentos entre las principales farmacias de Chile "
        "para ayudarte a ahorrar dinero.\n\n"
        "**Farmacias incluidas:**\n"
        "🟢 Cruz Verde\n"
        "🔵 Salcobrand\n"
        "🔴 Farmacias Ahumada\n\n"
        "**Tecnología:**\n"
        "• 🤖 IA para búsquedas inteligentes (Groq/Llama 3)\n"
        "• ⚡ Cache para respuestas rápidas\n"
        "• 🔄 Actualización en tiempo real\n"
        "• 🔒 100% seguro y privado\n\n"
        "**Desarrollado con ❤️ en Chile** 🇨🇱\n\n"
        "📧 Contacto: tu-email@ejemplo.com\n"
        "🐛 Reportar errores: @tu_usuario\n"
        "⭐ GitHub: github.com/tu-usuario/pharmacy-price-bot"
    )
    
    await update.message.reply_text(
        about_text,
        parse_mode=ParseMode.MARKDOWN
    )


@log_handler
@rate_limit
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle regular text messages (treat as search).
    
    Args:
        update: Telegram update
        context: Bot context
    """
    query = update.message.text.strip()
    
    # Ignore if it's a command
    if query.startswith("/"):
        return
    
    # Treat as search query
    context.args = query.split()
    await search_command(update, context)


# ============================================
# CALLBACK QUERY HANDLERS
# ============================================

@log_handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle inline keyboard button callbacks.
    
    Args:
        update: Telegram update
        context: Bot context
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Route to appropriate handler
    if callback_data == "menu":
        await show_main_menu(update, context)
    elif callback_data == "search":
        await prompt_search(update, context)
    elif callback_data == "help":
        await show_help(update, context)
    elif callback_data == "about":
        await show_about(update, context)
    elif callback_data == "stats":
        await show_user_stats(update, context)
    elif callback_data.startswith("result_"):
        await show_product_detail(update, context)
    elif callback_data == "back":
        await go_back(update, context)
    else:
        await query.edit_message_text("⚠️ Opción no disponible")


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu."""
    query = update.callback_query
    
    menu_text = (
        "🏠 **Menú Principal**\n\n"
        "Selecciona una opción:"
    )
    
    await query.edit_message_text(
        menu_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu_keyboard()
    )


async def prompt_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to search."""
    query = update.callback_query
    
    await query.edit_message_text(
        "🔍 **Buscar Medicamento**\n\n"
        "Escribe el nombre del medicamento que quieres buscar.\n\n"
        "**Ejemplo:**\n"
        "`paracetamol`\n"
        "`ibuprofeno 400mg`",
        parse_mode=ParseMode.MARKDOWN
    )


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help information."""
    query = update.callback_query
    
    help_text = (
        "❓ **Ayuda**\n\n"
        "**¿Cómo buscar medicamentos?**\n"
        "1. Usa `/buscar [medicamento]`\n"
        "2. O simplemente escribe el nombre\n\n"
        "**Ejemplos:**\n"
        "• `paracetamol`\n"
        "• `ibuprofeno 400mg`\n"
        "• `aspirina`\n\n"
        "El bot buscará en las 3 farmacias principales y te mostrará "
        "los mejores precios."
    )
    
    await query.edit_message_text(
        help_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_help_keyboard()
    )


async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show about information."""
    query = update.callback_query
    
    about_text = (
        "ℹ️ **Acerca del Bot**\n\n"
        "Bot comparador de precios de medicamentos en Chile.\n\n"
        "**Farmacias:**\n"
        "🟢 Cruz Verde\n"
        "🔵 Salcobrand\n"
        "🔴 Farmacias Ahumada\n\n"
        "Desarrollado con ❤️ en Chile 🇨🇱"
    )
    
    await query.edit_message_text(
        about_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics."""
    query = update.callback_query
    user = update.effective_user
    
    try:
        analytics_service = await get_analytics_service()
        stats = await analytics_service.get_user_stats(user.id)
        
        if not stats:
            await query.edit_message_text(
                "📊 No hay estadísticas disponibles aún.\n"
                "¡Realiza algunas búsquedas para ver tus estadísticas!"
            )
            return
        
        stats_text = (
            f"📊 **Tus Estadísticas**\n\n"
            f"🔍 Búsquedas totales: {stats.get('total_searches', 0)}\n"
            f"📅 Búsquedas hoy: {stats.get('searches_today', 0)}\n"
            f"📆 Miembro desde: {stats.get('member_since', 'N/A')[:10]}\n\n"
            f"**Últimas búsquedas:**\n"
        )
        
        recent = stats.get('recent_searches', [])[:5]
        for i, search in enumerate(recent, 1):
            stats_text += f"{i}. {search.get('query')} ({search.get('results_count')} resultados)\n"
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error showing user stats: {e}")
        await query.edit_message_text(
            "❌ Error al obtener estadísticas"
        )


async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show product detail."""
    query = update.callback_query
    
    # Extract result index from callback data
    try:
        result_index = int(query.data.split("_")[1])
        
        # Get results from context (stored during search)
        results = context.user_data.get("last_results", {}).get("results", [])
        
        if result_index >= len(results):
            await query.edit_message_text("❌ Producto no encontrado")
            return
        
        product = results[result_index]
        
        # Format product detail message
        detail_text = format_product_detail(product)
        
        await query.edit_message_text(
            detail_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_product_detail_keyboard(product),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error showing product detail: {e}")
        await query.edit_message_text("❌ Error al mostrar detalles")


async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Go back to previous screen."""
    # For now, just show main menu
    await show_main_menu(update, context)


# ============================================
# HELPER FUNCTIONS
# ============================================

async def send_search_results(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    results: dict
) -> None:
    """
    Send formatted search results.
    
    Args:
        update: Telegram update
        context: Bot context
        results: Search results
    """
    comparison_results = results.get("results", [])
    query = results.get("original_query", "")
    
    # Store results in context for later use
    context.user_data["last_results"] = results
    
    # Format header
    header = (
        f"🔍 **Resultados para: {query}**\n\n"
        f"✅ Encontrados: {len(comparison_results)} productos\n"
        f"⏱️ Tiempo: {results.get('duration_seconds', 0):.1f}s\n"
    )
    
    if results.get("cache_hit"):
        header += "⚡ Resultado desde cache\n"
    
    header += "\n"
    
    # Format top 5 results
    results_text = ""
    for i, result in enumerate(comparison_results[:5], 1):
        product_name = result.get("product_name", "Producto")
        best_price = result.get("best_price", 0)
        available_in = result.get("available_in", 0)
        price_range = result.get("price_range", {})
        
        results_text += f"**{i}. {product_name}**\n"
        results_text += f"💰 Mejor precio: ${best_price:,.0f}\n"
        results_text += f"🏪 Disponible en: {available_in} farmacia(s)\n"
        
        if price_range:
            min_price = price_range.get("min", 0)
            max_price = price_range.get("max", 0)
            if min_price != max_price:
                savings = max_price - min_price
                results_text += f"💵 Ahorro máximo: ${savings:,.0f}\n"
        
        results_text += "\n"
    
    # Add suggestions if available
    suggestions = results.get("suggestions", [])
    if suggestions:
        results_text += "💡 **También podrías buscar:**\n"
        for suggestion in suggestions[:3]:
            results_text += f"• {suggestion}\n"
    
    full_message = header + results_text
    
    await update.message.reply_text(
        full_message,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_search_results_keyboard(comparison_results)
    )


def format_product_detail(product: dict) -> str:
    """
    Format product detail message.
    
    Args:
        product: Product data
        
    Returns:
        str: Formatted message
    """
    name = product.get("product_name", "Producto")
    prices = product.get("prices", [])
    
    message = f"💊 **{name}**\n\n"
    message += "**Precios por farmacia:**\n\n"
    
    for price_info in prices:
        pharmacy = price_info.get("pharmacy_display", "Farmacia")
        price = price_info.get("price", 0)
        in_stock = price_info.get("in_stock", True)
        discount = price_info.get("discount")
        
        stock_emoji = "✅" if in_stock else "❌"
        message += f"{stock_emoji} **{pharmacy}**\n"
        message += f"💰 ${price:,.0f}"
        
        if discount:
            message += f" (-{discount}%)"
        
        message += "\n\n"
    
    # Add price comparison
    if len(prices) > 1:
        prices_list = [p["price"] for p in prices]
        min_price = min(prices_list)
        max_price = max(prices_list)
        savings = max_price - min_price
        
        message += f"💵 **Ahorro máximo:** ${savings:,.0f}\n"
        message += f"📊 **Diferencia:** {((savings / max_price) * 100):.1f}%\n"
    
    return message


__all__ = [
    "start_command",
    "search_command",
    "help_command",
    "about_command",
    "message_handler",
    "button_callback",
]

# Made with Bob