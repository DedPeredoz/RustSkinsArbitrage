import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import pandas as pd
from datetime import datetime

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot_errors.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
TOKEN = "7649105417:AAGrIblE3kwYkwbXWBEPa-owsmp-GdNB1QU"
DATABASE = "skins.db"
ITEMS_PER_PAGE = 15

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        logger.info(f"User {user.id} ({user.first_name}) started the bot")
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n"
        )
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    try:
        logger.info(f"User {update.effective_user.id} requested help")
        help_text = """
Доступные команды:
/table - Сравнить цены между площадками (вывод vs депозит)
/sources - Показать доступные источники
/filters - Настроить сортировку и фильтры
"""
        await update.message.reply_text(help_text)
    except Exception as e:
        logger.error(f"Error in help command: {str(e)}", exc_info=True)

async def list_sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать список доступных источников"""
    try:
        logger.info(f"User {update.effective_user.id} requested sources list")
        conn = sqlite3.connect(DATABASE)
        sources = pd.read_sql("SELECT DISTINCT source FROM skins UNION SELECT 'rustypot' as source", conn)['source'].tolist()
        conn.close()
        
        text = "Доступные источники:\n" + "\n".join(f"• {source}" for source in sources)
        await update.message.reply_text(text)
    except sqlite3.Error as e:
        logger.error(f"Database error in list_sources: {str(e)}", exc_info=True)
        await update.message.reply_text("Ошибка при работе с базой данных.")
    except Exception as e:
        logger.error(f"Error in list_sources: {str(e)}", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню фильтров и сортировки"""
    try:
        logger.info(f"User {update.effective_user.id} opened filters menu")
        keyboard = [
            [InlineKeyboardButton("Сортировка по названию", callback_data="sort_name")],
            [InlineKeyboardButton("Сортировка по цене", callback_data="sort_price")],
            [InlineKeyboardButton("Сортировка по проценту", callback_data="sort_percent")],
            [InlineKeyboardButton("Показать убыточные", callback_data="toggle_losses")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите тип сортировки:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in show_filters: {str(e)}", exc_info=True)
        await update.message.reply_text("Произошла ошибка при открытии фильтров.")

async def show_comparison_table(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает таблицу сравнения площадок"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} requested comparison table")
        
        conn = sqlite3.connect(DATABASE)
        sources = pd.read_sql("SELECT DISTINCT source FROM skins UNION SELECT 'rustypot' as source", conn)['source'].tolist()
        conn.close()
        
        # Инициализация параметров в user_data
        context.user_data.setdefault('withdraw_source', '(не выбрано)')
        context.user_data.setdefault('deposit_source', '(не выбрано)')
        context.user_data.setdefault('show_losses', False)
        context.user_data.setdefault('sort_by', 'percent')
        
        # Логируем текущее состояние
        logger.debug(f"User {user_id} settings: {context.user_data}")
        
        message = "*Таблица сравнения*\n\n"
        message += f"Текущие настройки:\n"
        message += f"• Сортировка: {context.user_data['sort_by']}\n"
        message += f"• Показывать убытки: {'Да' if context.user_data['show_losses'] else 'Нет'}\n\n"
        message += "Выберите площадки для сравнения:\n\n"
        message += "| WITHDRAW | DEPOSIT |\n"
        message += "|----------|---------|\n"
        message += f"| {context.user_data['withdraw_source']} | {context.user_data['deposit_source']} |\n"
        
        keyboard = []
        for source in sources:
            keyboard.append([
                InlineKeyboardButton(f"W: {source}", callback_data=f"withdraw_{source}"),
                InlineKeyboardButton(f"D: {source}", callback_data=f"deposit_{source}")
            ])
        
        keyboard.append([InlineKeyboardButton("⚙️ Фильтры и сортировка", callback_data="open_filters")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except sqlite3.Error as e:
        logger.error(f"Database error in show_comparison_table: {str(e)}", exc_info=True)
        await update.message.reply_text("Ошибка при работе с базой данных.")
    except Exception as e:
        logger.error(f"Error in show_comparison_table: {str(e)}", exc_info=True)
        await update.message.reply_text("Произошла ошибка при отображении таблицы.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик всех кнопок"""
    query = update.callback_query
    try:
        await query.answer()
        user_id = query.from_user.id
        logger.info(f"User {user_id} pressed button: {query.data}")
        
        # Обработка кнопок выбора площадок
        if query.data.startswith("withdraw_"):
            source = query.data.split("_")[1]
            context.user_data['withdraw_source'] = source
            logger.info(f"User {user_id} selected withdraw source: {source}")
        elif query.data.startswith("deposit_"):
            source = query.data.split("_")[1]
            context.user_data['deposit_source'] = source
            logger.info(f"User {user_id} selected deposit source: {source}")
        # Обработка кнопок сортировки
        elif query.data == "sort_name":
            context.user_data['sort_by'] = 'name'
            logger.info(f"User {user_id} changed sort to: name")
        elif query.data == "sort_price":
            context.user_data['sort_by'] = 'price'
            logger.info(f"User {user_id} changed sort to: price")
        elif query.data == "sort_percent":
            context.user_data['sort_by'] = 'percent'
            logger.info(f"User {user_id} changed sort to: percent")
        elif query.data == "toggle_losses":
            context.user_data['show_losses'] = not context.user_data['show_losses']
            status = "on" if context.user_data['show_losses'] else "off"
            logger.info(f"User {user_id} toggled losses display: {status}")
        elif query.data == "open_filters":
            await show_filters_menu(query)
            return
        elif query.data == "back_to_table":
            await show_comparison_table_menu(query, context)
            return
        elif query.data.startswith("page_"):
            page = int(query.data.split("_")[1])
            logger.info(f"User {user_id} requested page: {page}")
            await show_table_page(query, context, page)
            return
        
        # Если выбраны обе площадки, показываем таблицу
        if (context.user_data['withdraw_source'] != '(не выбрано)') and (context.user_data['deposit_source'] != '(не выбрано)'):
            await show_table_page(query, context, page=0)
        else:
            await show_comparison_table_menu(query, context)
            
    except Exception as e:
        logger.error(f"Error in button handler: {str(e)}", exc_info=True)
        await query.edit_message_text("Произошла ошибка при обработке вашего запроса.")

async def show_filters_menu(query):
    """Показывает меню фильтров"""
    try:
        keyboard = [
            [InlineKeyboardButton("Сортировка по названию", callback_data="sort_name")],
            [InlineKeyboardButton("Сортировка по цене", callback_data="sort_price")],
            [InlineKeyboardButton("Сортировка по проценту", callback_data="sort_percent")],
            [InlineKeyboardButton("Показать убыточные", callback_data="toggle_losses")],
            [InlineKeyboardButton("← Назад", callback_data="back_to_table")],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Настройки фильтров и сортировки:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error in show_filters_menu: {str(e)}", exc_info=True)
        await query.edit_message_text("Произошла ошибка при отображении фильтров.")

async def show_comparison_table_menu(query, context):
    """Показывает меню выбора площадок"""
    try:
        conn = sqlite3.connect(DATABASE)
        sources = pd.read_sql("SELECT DISTINCT source FROM skins UNION SELECT 'rustypot' as source", conn)['source'].tolist()
        conn.close()
        
        message += f"Текущие настройки:\n"
        message += f"• Сортировка: {context.user_data['sort_by']}\n"
        message += "Выберите площадки для сравнения:\n\n"
        message += "| WITHDRAW | DEPOSIT |\n"
        message += "|----------|---------|\n"
        message += f"| {context.user_data['withdraw_source']} | {context.user_data['deposit_source']} |\n"
        
        keyboard = []
        for source in sources:
            keyboard.append([
                InlineKeyboardButton(f"W: {source}", callback_data=f"withdraw_{source}"),
                InlineKeyboardButton(f"D: {source}", callback_data=f"deposit_{source}")
            ])
        
        keyboard.append([InlineKeyboardButton("⚙️ Фильтры ", callback_data="open_filters")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in show_comparison_table_menu: {str(e)}", exc_info=True)
        await query.edit_message_text("Произошла ошибка при отображении меню.")

async def show_table_page(query, context, page=0):
    """Показывает страницу с таблицей"""
    try:
        withdraw_source = context.user_data['withdraw_source']
        deposit_source = context.user_data['deposit_source']
        
        logger.info(
            f"Generating table page {page} for user {query.from_user.id} "
            f"with sources: {withdraw_source} -> {deposit_source}, "
            f"sort: {context.user_data['sort_by']}, "
            f"show losses: {context.user_data['show_losses']}"
        )
        
        table_result = generate_comparison_table(
            withdraw_source=withdraw_source,
            deposit_source=deposit_source,
            show_losses=context.user_data['show_losses'],
            sort_by=context.user_data['sort_by'],
            page=page
        )
        
        # Добавляем кнопки пагинации
        keyboard = []
        if page > 0:
            keyboard.append(InlineKeyboardButton("← Предыдущая", callback_data=f"page_{page-1}"))
        
        # Проверяем, есть ли следующая страница
        conn = sqlite3.connect(DATABASE)
        count_query = f"""
            SELECT COUNT(*) FROM (
                SELECT name FROM skins WHERE source = '{withdraw_source}'
                UNION ALL
                SELECT name FROM rustypot_items WHERE 'rustypot' = '{withdraw_source}'
            )
        """
        total_items = pd.read_sql(count_query, conn).iloc[0, 0]
        conn.close()
        
        if (page + 1) * ITEMS_PER_PAGE < total_items:
            if page > 0:  # Если есть и предыдущая и следующая - размещаем в одной строке
                keyboard.append(InlineKeyboardButton("Следующая →", callback_data=f"page_{page+1}"))
            else:
                keyboard = [[InlineKeyboardButton("Следующая →", callback_data=f"page_{page+1}")]]
        
        # Добавляем кнопку возврата
        if keyboard and isinstance(keyboard[0], list):
            keyboard.append([InlineKeyboardButton("⚙️ Фильтры", callback_data="open_filters")])
            keyboard.append([InlineKeyboardButton("↩️ Выбрать другие площадки", callback_data="back_to_table")])
        else:
            keyboard = [keyboard] if keyboard else []
            keyboard.append([InlineKeyboardButton("⚙️ Фильтры", callback_data="open_filters")])
            keyboard.append([InlineKeyboardButton("↩️ Выбрать другие площадки", callback_data="back_to_table")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            table_result,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except sqlite3.Error as e:
        logger.error(f"Database error in show_table_page: {str(e)}", exc_info=True)
        await query.edit_message_text("Ошибка при работе с базой данных.")
    except Exception as e:
        logger.error(f"Error in show_table_page: {str(e)}", exc_info=True)
        await query.edit_message_text("Произошла ошибка при отображении страницы.")

def generate_comparison_table(withdraw_source, deposit_source, show_losses=False, sort_by='percent', page=0):
    """Генерирует таблицу сравнения с пагинацией"""
    try:
        logger.debug(
            f"Generating comparison table: {withdraw_source} -> {deposit_source}, "
            f"sort: {sort_by}, show losses: {show_losses}, page: {page}"
        )
        
        conn = sqlite3.connect(DATABASE)
        
        # Получаем данные для withdraw (цены покупки)
        withdraw_query = f"""
            SELECT name, withdraw_price as price, have, max, datetime(last_updated, 'localtime') as updated
            FROM skins WHERE source = '{withdraw_source}'
            UNION ALL
            SELECT name, price as price, 1 as have, 100 as max, datetime(last_updated, 'localtime') as updated
            FROM rustypot_items WHERE 'rustypot' = '{withdraw_source}'
        """
        withdraw_df = pd.read_sql(withdraw_query, conn)
        
        # Получаем данные для deposit (цены продажи)
        deposit_query = f"""
            SELECT name, deposit_price as price, have, max, datetime(last_updated, 'localtime') as updated
            FROM skins WHERE source = '{deposit_source}'
            UNION ALL
            SELECT name, price as price, 1 as have, 100 as max, datetime(last_updated, 'localtime') as updated
            FROM rustypot_items WHERE 'rustypot' = '{deposit_source}'
        """
        deposit_df = pd.read_sql(deposit_query, conn)
        
        conn.close()
        
        # Объединяем данные
        merged_df = pd.merge(
            withdraw_df, 
            deposit_df, 
            on='name', 
            suffixes=(f'_{withdraw_source}', f'_{deposit_source}')
        )
        
        # Рассчитываем прибыль/убыток
        merged_df['Profit ($)'] = merged_df[f'price_{deposit_source}'] - merged_df[f'price_{withdraw_source}']
        merged_df['Profit (%)'] = (merged_df['Profit ($)'] / merged_df[f'price_{withdraw_source}']) * 100
        
        # Определяем тип сделки
        merged_df['Deal Type'] = merged_df['Profit ($)'].apply(
            lambda x: '🟢 Прибыль' if x > 0 else '🔴 Убыток'
        )
        
        # Сортировка
        if sort_by == 'name':
            merged_df.sort_values('name', ascending=True, inplace=True)
        elif sort_by == 'price':
            merged_df.sort_values('Profit ($)', ascending=False, inplace=True)
        else:  # percent
            merged_df['Absolute Profit (%)'] = merged_df['Profit (%)'].abs()
            merged_df.sort_values('Absolute Profit (%)', ascending=False, inplace=True)
        
        # Фильтрация убытков
        if not show_losses:
            merged_df = merged_df[merged_df['Profit ($)'] > 0]
        
        # Пагинация
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        result_df = merged_df.iloc[start_idx:end_idx]
        
        # Форматируем вывод
        table_header = (
            f"*Табличка*\n"
            f"*{withdraw_source}*|*{deposit_source}*\n"
            f"Страница {page + 1} | Сортировка: {sort_by} | Минусовые: {'Да' if show_losses else 'Нет'}\n\n"
        )
        
        table_rows = []
        for _, row in result_df.iterrows():
            profit_color = "🟢" if row['Profit ($)'] > 0 else "🔴"
            have_w = row[f"have_{withdraw_source}"]
            have_d = row[f"have_{deposit_source}"]
            max_d = row[f"max_{deposit_source}"]
            ovrst = " OVRST" if have_d >= max_d else ""
            table_row = (
                f"{row['name']} [{have_w}→{have_d}/{max_d}]{ovrst}\n"
                f"{row[f'price_{withdraw_source}']:.2f}   {row[f'price_{deposit_source}']:.2f}   "
                f"Δ {row['Profit ($)']:.2f}   {row['Profit (%)']:.2f}%"
                        )
            table_rows.append(table_row)
        
        full_table = table_header + "\n\n".join(table_rows)
        
        # Добавляем информацию о времени обновления
        if not result_df.empty:
            last_updated = "\n\n*Время обновления:*\n"
            last_updated += f"{withdraw_source}: {result_df.iloc[0][f'updated_{withdraw_source}']}\n"
            last_updated += f"{deposit_source}: {result_df.iloc[0][f'updated_{deposit_source}']}"
            return full_table + last_updated
        else:
            return "Нет данных для отображения с текущими фильтрами."
            
    except sqlite3.Error as e:
        logger.error(f"Database error in generate_comparison_table: {str(e)}", exc_info=True)
        return "Ошибка при работе с базой данных."
    except Exception as e:
        logger.error(f"Error in generate_comparison_table: {str(e)}", exc_info=True)
        return "Произошла ошибка при генерации таблицы."

def main() -> None:
    """Запуск бота"""
    try:
        logger.info("Starting bot...")
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация обработчиков команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("sources", list_sources))
        application.add_handler(CommandHandler("table", show_comparison_table))
        application.add_handler(CommandHandler("filters", show_filters))
        
        # Обработчик всех кнопок
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Запуск бота
        logger.info("Bot is running...")
        application.run_polling()
        
    except Exception as e:
        logger.critical(f"Fatal error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()