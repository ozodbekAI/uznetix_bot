# bot/handlers/start.py
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from bot.keyboards.inline import get_main_menu_keyboard
from bot.states import UserStates
from bot.utils.text_utils import detect_script, get_text
from database.repositories import UserRepository
from services.getcourse import getcourse_service

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    try:
        telegram_id = message.from_user.id
        
        user = await UserRepository.get_by_telegram_id(session, telegram_id)
        
        if not user:
            user = await UserRepository.create(
                session,
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                language_code=message.from_user.language_code,
                preferred_script="latin"
            )
            
        else:
            await UserRepository.update_activity(session, telegram_id)
        
        await session.commit()
        
        if user.is_getcourse_client:
            script = user.preferred_script or "latin"
            welcome_text = get_text("welcome_back_uznetix", script, user_name=message.from_user.first_name or "")
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(script),
                parse_mode=None
            )
            await state.set_state(UserStates.main_menu)
            await state.update_data(script=script, user_id=user.id)
        else:
            script = detect_script(message.text or "") or "latin"
            welcome = get_text("welcome_uznetix", script, user_name=message.from_user.first_name or "")
            disclaimer = get_text("disclaimer", script)
            verification = get_text("verification_prompt", script)
            
            full_text = f"{welcome}\n\n{disclaimer}\n\n{verification}\n\n"
            
            await message.answer(
                full_text,
                parse_mode=None
            )
            
            await state.set_state(UserStates.waiting_email)
            await state.update_data(user_id=user.id, script=script)
        
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        script = "latin"
        error_text = get_text("error_general", script)
        await message.answer(
            error_text,
            parse_mode=None
        )


@router.message(StateFilter(UserStates.waiting_email), F.text)
async def process_email(message: Message, state: FSMContext, session: AsyncSession):
    """Process email verification"""
    try:
        email = message.text.strip()
        telegram_id = message.from_user.id
        
        script = detect_script(message.text)
        
        data = await state.get_data()
        
        if "@" not in email or "." not in email:
            await message.answer(
                get_text("invalid_email", script),
                parse_mode=None
            )
            return
        
        checking_msg = await message.answer(
            get_text("checking_access", script),
            parse_mode=None
        )

        is_verified = await getcourse_service.verify_user(email) 
        
        await checking_msg.delete()
        
        if is_verified:
            await UserRepository.update(
                session,
                telegram_id,
                is_getcourse_client=True,
                getcourse_email=email,
                getcourse_verified_at=datetime.now(),
                preferred_script=script
            )
            await session.commit()
            
            success_text = get_text("verification_success_uznetix", script)
            await message.answer(
                success_text,
                reply_markup=get_main_menu_keyboard(script),
                parse_mode=None
            )
            
            await state.set_state(UserStates.main_menu)
            await state.update_data(script=script)
            

            
        else:
            fail_text = get_text("verification_failed", script)
            verification_text = get_text("verification_prompt", script)
            await message.answer(
                f"{fail_text}\n\n{verification_text}",
                parse_mode=None
            )

            
    except Exception as e:
        logger.error(f"Error in process_email: {e}")
        script = data.get("script", "latin") if data else "latin"
        await message.answer(
            get_text("error_general", script),
            parse_mode=None
        )