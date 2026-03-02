from __future__ import annotations

import asyncio
import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.assistant import DeepseekLegalAssistant
from app.config import Settings, load_settings
from app.rate_limit import InMemoryRateLimiter
from app.sheets_logger import GoogleSheetsLogger
from app.vector_db import VectorKnowledgeBase

ASKING_QUESTION = 1

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def split_for_telegram(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


def get_services(application: Application) -> dict[str, Any]:
    return application.bot_data["services"]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет. Я юридический бот-консультант.\n\n"
        "Команды:\n"
        "/start — старт\n"
        "/help — справка\n"
        "/ask — задать юридический вопрос\n\n"
        "Можно также просто отправить вопрос текстом."
    )
    await update.message.reply_text(text)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Как пользоваться:\n"
        "1) Напиши /ask\n"
        "2) Отправь вопрос\n"
        "3) Получи консультацию на основе векторной базы знаний + DeepSeek\n\n"
        "Формат ответа:\n"
        "- краткий вывод;\n"
        "- рекомендации;\n"
        "- ссылки на нормы права;\n"
        "- альтернативные пути решения."
    )
    await update.message.reply_text(text)


async def cmd_ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напишите ваш юридический вопрос одним сообщением.")
    return ASKING_QUESTION


async def _process_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        return ConversationHandler.END

    question = update.message.text.strip()
    if not question:
        await update.message.reply_text("Пустой вопрос. Напишите текст вопроса.")
        return ASKING_QUESTION

    user = update.effective_user
    chat = update.effective_chat
    user_key = user.id if user else (chat.id if chat else 0)

    services = get_services(context.application)
    kb: VectorKnowledgeBase = services["kb"]
    assistant: DeepseekLegalAssistant = services["assistant"]
    sheets: GoogleSheetsLogger | None = services["sheets"]
    limiter: InMemoryRateLimiter = services["limiter"]

    allowed, deny_message = await limiter.acquire(user_key=user_key, question=question)
    if not allowed:
        await update.message.reply_text(deny_message or "Слишком много запросов.")
        return ConversationHandler.END

    await update.message.reply_text("Обрабатываю вопрос...")

    try:
        chunks = await asyncio.to_thread(kb.retrieve, question)
        answer = await asyncio.to_thread(assistant.generate_answer, question, chunks)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to generate legal answer")
        await update.message.reply_text(f"Ошибка при обработке вопроса: {exc}")
        await limiter.release(user_key)
        return ConversationHandler.END

    try:
        for piece in split_for_telegram(answer):
            await update.message.reply_text(piece)

        if sheets is not None:
            try:
                await asyncio.to_thread(
                    sheets.append_qa,
                    telegram_user_id=user.id if user else None,
                    question=question,
                    answer=answer,
                )
            except Exception:  # noqa: BLE001
                logger.exception("Failed to write Q/A to Google Sheets")
    finally:
        await limiter.release(user_key)

    return ConversationHandler.END


async def fallback_text_question(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    # Удобно для UX: принимаем обычный текст без /ask.
    await _process_question(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Ок, отменено.")
    return ConversationHandler.END


def build_application(settings: Settings) -> Application:
    kb = VectorKnowledgeBase(
        db_path=settings.legal_db_path,
        config_path=settings.legal_db_config_path,
        top_k=settings.retrieval_top_k,
    )
    assistant = DeepseekLegalAssistant(
        api_key=settings.deepseek_api_key,
        model=settings.deepseek_model,
        base_url=settings.deepseek_base_url,
        timeout_seconds=settings.deepseek_timeout_seconds,
        max_retries=settings.deepseek_max_retries,
        retry_base_delay_seconds=settings.deepseek_retry_base_delay_seconds,
    )

    limiter = InMemoryRateLimiter(
        window_seconds=settings.user_rate_limit_window_seconds,
        max_requests_per_window=settings.user_rate_limit_max_requests,
        min_interval_seconds=settings.user_min_interval_seconds,
        max_question_length=settings.max_question_length,
    )

    sheets = None
    if settings.google_sheet_enabled:
        try:
            sheets = GoogleSheetsLogger(
                spreadsheet_id=settings.google_spreadsheet_id,
                worksheet_name=settings.google_worksheet_name,
                service_account_file=str(settings.google_service_account_file),
                max_retries=settings.sheets_max_retries,
                retry_base_delay_seconds=settings.sheets_retry_base_delay_seconds,
            )
        except Exception:  # noqa: BLE001
            logger.exception("Google Sheets logger init failed. Continue without sheets.")
            sheets = None

    app = (
        ApplicationBuilder()
        .token(settings.telegram_token)
        .rate_limiter(AIORateLimiter())
        .build()
    )
    app.bot_data["services"] = {
        "kb": kb,
        "assistant": assistant,
        "sheets": sheets,
        "limiter": limiter,
    }

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("ask", cmd_ask)],
        states={
            ASKING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _process_question)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_user=True,
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(conversation_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text_question))
    return app


def validate_settings(settings: Settings) -> None:
    missing = []
    if not settings.telegram_token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.deepseek_api_key:
        missing.append("DEEPSEEK_API_KEY")
    if missing:
        raise ValueError(f"Отсутствуют обязательные переменные в .env: {', '.join(missing)}")


def main() -> None:
    settings = load_settings()
    validate_settings(settings)
    app = build_application(settings)
    logger.info("Bot is running...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()

