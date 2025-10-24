# bot/handlers/interview.py
import logging
import json
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_main_menu_keyboard
from bot.states import UserStates
from bot.utils.text_utils import detect_script, get_text
from database.repositories import (
    UserRepository, 
    InterviewSessionRepository, 
    RecommendationRepository, 
)
from services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "start_interview", StateFilter(UserStates.main_menu, UserStates.advisor_chat))
async def start_interview(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    try:
        await callback.answer()
        telegram_id = callback.from_user.id
        
        user = await UserRepository.get_by_telegram_id(session, telegram_id)
        if not user or not user.is_getcourse_client:
            await callback.message.answer(
                get_text("verification_required", user.preferred_script if user else "latin")
            )
            return
        
        script = user.preferred_script or "latin"
        
        active_session = await InterviewSessionRepository.get_active_session(session, telegram_id)
        if active_session:
            await InterviewSessionRepository.update_session(
                session,
                active_session.id,
                status="abandoned"
            )
        
        interview = await InterviewSessionRepository.create(
            session,
            telegram_id=telegram_id,
            user_id=user.id,
            preferred_script=script,
            status="active"
        )
        await session.commit()
        
        await state.update_data(
            interview_session_id=interview.id,
            script=script,
            user_id=user.id
        )
        await state.set_state(UserStates.interview_in_progress)
        
        welcome_text = get_text("interview_start", script)
        await callback.message.answer(welcome_text, parse_mode="HTML")
        
        initial_greeting = "Assalomu alaykum! Men Uznetix Advisor investitsiya maslahatchiman. Minglab odamlarga muvaffaqiyatli portfel yig'ishda yordam berganman.\n\nKeling, birgalikda sizning maqsadlaringizga erishamiz! Menga haqingizda ko'proq ma'lumot bering.\n\nSiz nima maqsadda investitsiya qilmoqchisiz? Uy sotib olish, bolalaringiz ta'limi, yoqimli pensiya yoki passiv daromadmi?"

        if script == "cyrillic":
            initial_greeting = "Ассалому алайкум! Мен Uznetix Advisor -  инвестиция маслаҳатчиман. Минглаб одамларга муваффақиятли портфел йиғишда ёрдам берганман.\n\nКелинг, биргаликда сизнинг мақсадларингизга эришамиз! Менга ҳақингизда кўпроқ маълумот беринг.\n\nСиз нима мақсадда инвестиция қилмоқчисиз? Уй сотиб олиш, болаларингиз таълими, ёқимли пенсия ёки пассив даромадми?"

        await callback.message.answer(initial_greeting, parse_mode="HTML")

        await InterviewSessionRepository.add_message(
            session,
            interview.id,
            role="assistant",
            content=initial_greeting
        )
        await session.commit()
        
        await UserRepository.update(
            session,
            telegram_id,
            total_interviews=user.total_interviews + 1
        )
        await session.commit()
        
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        await callback.message.answer(
            get_text("error_general", "latin"),
            parse_mode="HTML"
        )


@router.message(StateFilter(UserStates.interview_in_progress), F.text)
async def process_interview_message(message: Message, state: FSMContext, session: AsyncSession):
    try:
        data = await state.get_data()
        interview_session_id = data.get("interview_session_id")
        script = data.get("script", "latin")
        
        if not interview_session_id:
            await message.answer(get_text("error_general", script))
            return
        
        interview = await InterviewSessionRepository.get_by_id(session, interview_session_id)
        if not interview or interview.status != "active":
            await message.answer(get_text("error_general", script))
            return
        
        user_message = message.text.strip()
        
        await InterviewSessionRepository.add_message(
            session,
            interview_session_id,
            role="user",
            content=user_message
        )
        await session.commit()
        
        conversation_history = interview.conversation_history or []
        
        bot_response, collected_data = await ai_service.conduct_interview(
            conversation_history=conversation_history,
            user_message=user_message,
            script=script
        )

        await message.bot.send_chat_action(message.chat.id, "typing")
        
        await InterviewSessionRepository.add_message(
            session,
            interview_session_id,
            role="assistant",
            content=bot_response
        )
        
        await InterviewSessionRepository.update_session(
            session,
            interview_session_id,
            questions_asked=interview.questions_asked + 1
        )
        await session.commit()
        
        await message.answer(bot_response, parse_mode="HTML")
        
        if collected_data:
            await handle_interview_completion(
                message, state, session, interview_session_id, collected_data, script
            )
        
    except Exception as e:
        logger.error(f"Error processing interview message: {e}")
        await message.answer(
            get_text("error_general", script if 'script' in locals() else "latin"),
            parse_mode="HTML"
        )


async def handle_interview_completion(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    interview_session_id: int,
    collected_data: dict,
    script: str
):
    try:
        await InterviewSessionRepository.update_session(
            session,
            interview_session_id,
            status="completed",
            completed_at=datetime.now(),
            collected_data=collected_data
        )
        await session.commit()
        
        generating_msg = await message.answer(
            get_text("generating_recommendation", script),
            parse_mode="HTML"
        )
        
        recommendation_text = await ai_service.generate_recommendation(
            collected_data=collected_data,
            script=script
        )
        
        await generating_msg.delete()
        
        await message.answer(recommendation_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard(script))
        
        interview = await InterviewSessionRepository.get_by_id(session, interview_session_id)
        recommendation = await RecommendationRepository.create(
            session,
            session_id=interview_session_id,
            user_id=interview.user_id,
            telegram_id=interview.telegram_id,
            recommendation_type="mixed",
            content=recommendation_text,
            content_json=collected_data,
            ai_model_used=ai_service.model,
            generation_time=0.0
        )
        await session.commit()
        
        user = await UserRepository.get_by_telegram_id(session, interview.telegram_id)
        await UserRepository.update(
            session,
            interview.telegram_id,
            completed_interviews=user.completed_interviews + 1
        )
        await session.commit()
        
        continue_text = get_text("continue_chat_offer", script)
        await message.answer(
            continue_text,
            parse_mode="HTML"
        )
        
        await state.set_state(UserStates.advisor_chat)
        await state.update_data(
            last_recommendation_id=recommendation.id,
            last_recommendation_text=recommendation_text, 
            collected_data=collected_data,
            script=script
        )
        
    except Exception as e:
        logger.error(f"Error handling interview completion: {e}")
        await message.answer(
            get_text("error_generating_recommendation", script),
            reply_markup=get_main_menu_keyboard(script),
            parse_mode="HTML"
        )
        await state.set_state(UserStates.main_menu)


# Post-interview advisor chat
@router.callback_query(F.data == "continue_chat", StateFilter(UserStates.advisor_chat))
async def continue_advisor_chat(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        data = await state.get_data()
        script = data.get("script", "latin")
        
        chat_ready_text = get_text("chat_ready", script)
        await callback.message.answer(chat_ready_text, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in continue_advisor_chat: {e}")


@router.callback_query(F.data == "back_to_menu", StateFilter(UserStates.advisor_chat))
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        data = await state.get_data()
        script = data.get("script", "latin")
        
        await callback.message.answer(
            get_text("back_to_menu_text", script),
            reply_markup=get_main_menu_keyboard(script),
            parse_mode="HTML"
        )
        await state.set_state(UserStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in back_to_main_menu: {e}")


@router.message(StateFilter(UserStates.advisor_chat), F.text)
async def process_advisor_chat(message: Message, state: FSMContext, session: AsyncSession):
    try:
        data = await state.get_data()
        script = data.get("script", "latin")
        collected_data = data.get("collected_data", {})
        recommendation_text = data.get("last_recommendation_text")  # ← RECOMMENDATION MATNINI OLAMIZ
        
        user_message = message.text.strip()
        
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        bot_response = await ai_service.chat_about_investments(
            user_message=user_message,
            user_profile=collected_data,
            recommendation=recommendation_text,
            script=script
        )
        
        await message.answer(bot_response, parse_mode="HTML")
        
        interview_session_id = data.get("interview_session_id")
        if interview_session_id:
            await InterviewSessionRepository.add_message(
                session,
                interview_session_id,
                role="user",
                content=user_message
            )
            await InterviewSessionRepository.add_message(
                session,
                interview_session_id,
                role="assistant",
                content=bot_response
            )
            await session.commit()
        
    except Exception as e:
        logger.error(f"Error in advisor chat: {e}")
        await message.answer(
            get_text("error_general", script if 'script' in locals() else "latin"),
            parse_mode="HTML"
        )