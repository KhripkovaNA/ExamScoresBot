import asyncio
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger
from bot.config import bot, dp
from bot.users.router import router as users_router
from bot.scores.router import router as scores_router


async def set_default_commands():
    """Устанавливает команды бота в Telegram"""
    commands = [
        BotCommand(command="/start", description="Начать работу с ботом")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    logger.info("Команды бота установлены")


async def start_bot():
    """Выполняется при старте бота"""
    logger.info("Бот запущен")


async def stop_bot():
    """Выполняется при завершении работы бота"""
    logger.info("Бот остановлен")


async def main():
    """Основная функция запуска приложения"""
    # Регистрация маршрутов (обработчиков)
    dp.include_router(users_router)
    dp.include_router(scores_router)

    # Регистрация хуков на запуск и завершение
    dp.startup.register(start_bot)
    dp.startup.register(set_default_commands)
    dp.shutdown.register(stop_bot)

    # Запуск бота в режиме long polling и очистка всех ожидающих обновлений
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.warning("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()
        logger.info("Сессия бота закрыта")


if __name__ == "__main__":
    asyncio.run(main())
