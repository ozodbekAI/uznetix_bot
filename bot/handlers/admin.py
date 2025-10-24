import logging
import csv
from io import StringIO
from datetime import datetime, timedelta
from typing import Union
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, BufferedInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import distinct, select, func, and_, desc

from config import settings
from bot.states import UserStates
from database.models import User, InterviewSession, Recommendation
from database.repositories import UserRepository, InterviewSessionRepository, RecommendationRepository

logger = logging.getLogger(__name__)
router = Router()

ADMIN_PREFIX = "admin_"

def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_ids_list

def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data=f"{ADMIN_PREFIX}stats"),
            InlineKeyboardButton(text="🔍 Foydalanuvchi qidirish", callback_data=f"{ADMIN_PREFIX}search")
        ],
        [
            InlineKeyboardButton(text="👥 Top yakunlaganlar", callback_data=f"{ADMIN_PREFIX}top_completers"),
            InlineKeyboardButton(text="📝 Dialog tarixi", callback_data=f"{ADMIN_PREFIX}history")
        ],
        [
            InlineKeyboardButton(text="📤 Broadcast", callback_data=f"{ADMIN_PREFIX}broadcast"),
            InlineKeyboardButton(text="📊 CSV export", callback_data=f"{ADMIN_PREFIX}export")
        ],
        [InlineKeyboardButton(text="❌ Chiqish", callback_data="close_admin")]
    ])
    return keyboard


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ Sizda admin huquqi yo'q")
        return
    
    welcome_text = """🚀 <b>Uznetix Advisor - Admin Panelga xush kelibsiz!</b>

Quyidagi tugmalardan birini tanlang:"""
    
    await message.answer(welcome_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith(ADMIN_PREFIX))
async def admin_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ Ruxsat yo'q")
        return
    
    data = callback.data
    if data == f"{ADMIN_PREFIX}stats":
        await show_statistics(callback, session)
    elif data == f"{ADMIN_PREFIX}search":
        await show_search_prompt(callback, state)
    elif data == f"{ADMIN_PREFIX}top_completers":
        await show_top_completers(callback, session)
    elif data == f"{ADMIN_PREFIX}history":
        await show_history_prompt(callback, state)
    elif data == f"{ADMIN_PREFIX}broadcast":
        await show_broadcast_prompt(callback, state)
    elif data == f"{ADMIN_PREFIX}export":
        await export_stats(callback, session)
    elif data.startswith(f"{ADMIN_PREFIX}search_result_"):
        telegram_id = int(data.split("_")[-1])
        await show_user_history(callback, session, telegram_id)
    elif data.startswith(f"{ADMIN_PREFIX}history_"):
        telegram_id = int(data.split("_")[-1])
        await show_user_history(callback, session, telegram_id)
    elif data == "close_admin":
        await callback.message.edit_text("❌ Admin panel yopildi.")
        await state.clear()
        await callback.answer()
    else:
        await callback.answer("❓ Noma'lum amal")


async def show_statistics(callback: CallbackQuery, session: AsyncSession):
    try:
        stats = await get_detailed_statistics(session)
        
        stats_text = f"""📊 <b>Bot Statistika (Mukammal)</b>

👥 <b>Unikal foydalanuvchilar:</b>
• Jami: {stats['total_users']}
• Faol (so'nggi 7 kun): {stats['active_users_7d']}
• Tasdiqlangan: {stats['verified_users']}

📝 <b>Intervyular:</b>
• Jami boshlangan: {stats['total_interviews']}
• Yakunlangan: {stats['completed_interviews']}
• Yakunlanish foizi: {stats['completion_rate']:.1f}%
• Eng ko'p tashlab ketilgan bosqich: {stats['most_dropoff_step']} (foizi: {stats['dropoff_rate']:.1f}%)

💡 <b>Tavsiyalar taqsimoti:</b>
• 1-3 g'oyalar: {stats['recommendations_ideas']} ({stats['ideas_percentage']:.1f}%)
• Mini-portfel: {stats['recommendations_portfolio']} ({stats['portfolio_percentage']:.1f}%)

📈 <b>Bugungi:</b>
• Yangi foydalanuvchilar: {stats['new_users_today']}
• Yakunlangan intervyular: {stats['completed_today']}

🕐 <b>O'rtacha tavsiya vaqti:</b> {stats['avg_generation_time']:.1f}s"""
        
        await callback.message.edit_text(stats_text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in stats: {e}")
        await callback.answer("❌ Xatolik")


async def show_search_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_search)
    text = "🔍 <b>Foydalanuvchi qidirish</b>\n\nUsername yoki email yuboring (masalan: @username yoki email@example.com):"
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(UserStates.waiting_for_search) 
async def handle_search(message: Message, session: AsyncSession, state: FSMContext):
    search_query = message.text.strip()
    await state.clear() 
    
    try:
        if search_query.startswith('@'):
            username = search_query[1:]
            result = await session.execute(
                select(User).where(User.username == username)
            )
        elif '@' in search_query:
            email = search_query
            result = await session.execute(
                select(User).where(User.getcourse_email == email)
            )
        else:
            await message.answer("❌ Noto'g'ri format. Username (@username) yoki email kiriting.")
            return
        
        users = result.scalars().all()
        
        if not users:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            return
        
        text = f"🔍 <b>Qidiruv natijalari ({len(users)} ta):</b>\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for user in users[:5]:
            btn_text = f"{user.first_name or ''} {user.last_name or ''} (@{user.username or 'yoq'})"
            keyboard.inline_keyboard.append([InlineKeyboardButton(
                text=btn_text[:30] + "..." if len(btn_text) > 30 else btn_text,
                callback_data=f"{ADMIN_PREFIX}history_{user.telegram_id}"
            )])
        
        if len(users) > 5:
            keyboard.inline_keyboard.append([InlineKeyboardButton(text="Ko'proq...", callback_data=f"{ADMIN_PREFIX}search")])
        
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"{ADMIN_PREFIX}stats")])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        await message.answer("❌ Qidirishda xatolik")


async def show_top_completers(callback: CallbackQuery, session: AsyncSession):
    try:
        result = await session.execute(
            select(
                User.telegram_id,
                User.first_name,
                User.last_name,
                User.username,
                User.completed_interviews
            )
            .order_by(User.completed_interviews.desc())
            .limit(10)
        )
        top_users = result.fetchall()
        
        text = f"👥 <b>Top yakunlagan foydalanuvchilar (10 ta):</b>\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for row in top_users:
            telegram_id, first, last, username, completed = row
            name = f"{first or ''} {last or ''}".strip() or username or str(telegram_id)
            btn_text = f"{name} ({completed} ta)"
            keyboard.inline_keyboard.append([InlineKeyboardButton(
                text=btn_text[:30] + "..." if len(btn_text) > 30 else btn_text,
                callback_data=f"{ADMIN_PREFIX}history_{telegram_id}"
            )])
        
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"{ADMIN_PREFIX}stats")])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in top completers: {e}")
        await callback.answer("❌ Xatolik")


async def show_history_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_history) 
    text = "📝 <b>Dialog tarixi</b>\n\nTelegram ID kiriting (masalan: 123456789):"
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(UserStates.waiting_for_history) 
async def handle_history_input(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    try:
        telegram_id = int(message.text.strip())
        await show_user_history(message, session, telegram_id)
    except ValueError:
        await message.answer("❌ Noto'g'ri ID. Raqam kiriting.")


async def show_user_history(message: Union[Message, CallbackQuery], session: AsyncSession, telegram_id: int):
    try:
        # Get user info
        user = await UserRepository.get_by_telegram_id(session, telegram_id)
        if not user:
            if isinstance(message, Message):
                await message.answer(f"❌ Foydalanuvchi topilmadi: {telegram_id}")
            else:
                await message.message.answer(f"❌ Foydalanuvchi topilmadi: {telegram_id}")
                await message.answer()
            return

        sessions = await InterviewSessionRepository.get_user_sessions(session, telegram_id, limit=None)
        recommendations = await RecommendationRepository.get_user_recommendations(session, telegram_id, limit=None)
        
        output = StringIO()
        output.write(f"Uznetix Advisor - Foydalanuvchi Dialog Tarixi\n")
        output.write(f"{'='*60}\n\n")
        output.write(f"Foydalanuvchi ID: {user.telegram_id}\n")
        output.write(f"Ism: {user.first_name or ''} {user.last_name or ''}\n")
        output.write(f"Username: @{user.username or 'Yoq'}\n")
        output.write(f"Email: {user.getcourse_email or 'Yoq'}\n")
        output.write(f"Jami intervyular: {user.total_interviews} (yakunlangan: {user.completed_interviews})\n\n")
        output.write(f"{'='*60}\n\n")
        
        if not sessions:
            output.write("Intervyu topilmadi.\n")
        else:
            for i, session in enumerate(sessions, 1):
                output.write(f"Intervyu #{i} (ID: {session.id})\n")
                output.write(f"Status: {session.status.capitalize()}\n")
                output.write(f"Savollar soni: {session.questions_asked}\n")
                output.write(f"Boshlangan: {session.created_at.strftime('%Y-%m-%d %H:%M')}\n")
                if session.completed_at:
                    output.write(f"Tugagan: {session.completed_at.strftime('%Y-%m-%d %H:%M')}\n")
                output.write("-" * 40 + "\n")
                
                if session.conversation_history:
                    output.write("Dialog tarixi:\n")
                    for msg in session.conversation_history[:20]: 
                        role = msg.get('role', 'unknown').capitalize()
                        content = msg.get('content', '')[:150] + "..." if len(msg.get('content', '')) > 150 else msg.get('content', '')
                        timestamp = msg.get('timestamp', '')[:19] if msg.get('timestamp') else ''
                        output.write(f"{role} ({timestamp}): {content}\n")
                    output.write("\n")
                else:
                    output.write("Dialog tarixi yo'q.\n\n")
                
                if session.collected_data:
                    output.write("To'plangan ma'lumotlar:\n")
                    for key, value in session.collected_data.items():
                        output.write(f"{key}: {value}\n")
                    output.write("\n")
                
                output.write("="*60 + "\n\n")

        output.write("Tavsiyalar:\n")
        output.write("-" * 40 + "\n")
        if not recommendations:
            output.write("Tavsiya topilmadi.\n")
        else:
            for i, rec in enumerate(recommendations, 1):
                output.write(f"Tavsiya #{i} (ID: {rec.id})\n")
                output.write(f"Turi: {rec.recommendation_type}\n")
                output.write(f"Vaqt: {rec.created_at.strftime('%Y-%m-%d %H:%M')}\n")
                output.write(f"Generation vaqti: {rec.generation_time:.1f}s\n")
                if rec.user_rating:
                    output.write(f"Reyting: {rec.user_rating}/5\n")
                    feedback = rec.user_feedback or 'Yoq'
                    output.write(f"Feedback: {feedback[:200]}...\n")
                output.write(f"Kontent: {rec.content[:300]}...\n\n")
        
        output.write(f"\nYakuniy maslahatlar:\n")
        if user.completed_interviews == 0:
            output.write("- Foydalanuvchi intervyuni yakunlamagan — onboarding ni yaxshilang.\n")
        elif len(sessions) > user.completed_interviews * 1.5:
            output.write("- Ko'p tashlab ketgan — drop-off bosqichlarini tekshiring.\n")
        output.write("- Kontentni moslashtiring: Javoblarga qarab savollarni shaxsiylashtiring.\n")
        
        file_content = output.getvalue().encode('utf-8')
        file_name = f"user_{telegram_id}_dialog_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        txt_file = BufferedInputFile(file_content, filename=file_name)
        
        completion_rate = (user.completed_interviews / max(user.total_interviews, 1)) * 100
        summary = f"📁 <b>Foydalanuvchi {user.telegram_id} dialog tarixi yuklandi</b>\n\nJami intervyular: {len(sessions)}\nTavsiyalar: {len(recommendations)}\nYakunlanish foizi: {completion_rate:.1f}%\n\nTo'liq fayl quyida!"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Umumiy stats", callback_data=f"{ADMIN_PREFIX}stats")],
            [InlineKeyboardButton(text="🔍 Boshqa qidirish", callback_data=f"{ADMIN_PREFIX}search")]
        ])
        
        if isinstance(message, Message):
            await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
            await message.answer_document(txt_file)
        else:
            await message.message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
            await message.message.answer_document(txt_file)
            await message.answer()
        
    except Exception as e:
        logger.error(f"Error in user history: {e}")
        if isinstance(message, Message):
            await message.answer("❌ Dialog tarixini yuklashda xatolik")
        else:
            await message.message.answer("❌ Dialog tarixini yuklashda xatolik")
            await message.answer()


async def show_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserStates.waiting_for_broadcast) 
    text = "📤 <b>Broadcast</b>\n\nXabar matnini yuboring (keyingi xabarda):"
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(UserStates.waiting_for_broadcast) 
async def handle_broadcast_input(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear() 
    text = message.text.strip()
    
    if not text:
        await message.answer("❌ Xabar matni yo'q.")
        return
    
    try:
        users = await UserRepository.get_all_users(session, limit=10000)
        
        sent = 0
        failed = 0
        
        status_msg = await message.answer(f"📤 Yuborilmoqda... 0/{len(users)}")
        
        for i, user in enumerate(users):
            try:
                await message.bot.send_message(user.telegram_id, text)
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send to {user.telegram_id}: {e}")
                failed += 1
            
            if (i + 1) % 10 == 0:
                await status_msg.edit_text(f"📤 Yuborilmoqda... {i + 1}/{len(users)}")
        
        await status_msg.edit_text(
            f"✅ Xabar yuborildi!\n\nMuvaffaqiyatli: {sent}\nXato: {failed}",
            reply_markup=get_admin_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")
        await message.answer("❌ Xabar yuborishda xatolik")


async def export_stats(callback: CallbackQuery, session: AsyncSession):
    try:
        stats = await get_detailed_statistics(session)
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Metrika", "Qiymat"])
        writer.writerow(["Jami foydalanuvchilar", stats['total_users']])
        writer.writerow(["Faol 7 kun", stats['active_users_7d']])
        writer.writerow(["Tasdiqlangan", stats['verified_users']])
        writer.writerow(["Jami intervyular", stats['total_interviews']])
        writer.writerow(["Yakunlangan", stats['completed_interviews']])
        writer.writerow(["Yakunlanish foizi", f"{stats['completion_rate']:.1f}%"])
        writer.writerow(["Eng ko'p drop-off bosqich", stats['most_dropoff_step']])
        writer.writerow(["Drop-off foizi", f"{stats['dropoff_rate']:.1f}%"])
        writer.writerow(["1-3 g'oyalar", stats['recommendations_ideas']])
        writer.writerow(["Mini-portfel", stats['recommendations_portfolio']])
        writer.writerow(["Bugungi yangilar", stats['new_users_today']])
        writer.writerow(["Bugungi yakunlangan", stats['completed_today']])
        writer.writerow(["O'rtacha vaqt", f"{stats['avg_generation_time']:.1f}s"])
        
        csv_content = output.getvalue().encode('utf-8')
        csv_file = BufferedInputFile(csv_content, filename="uznetix_stats.csv")
        
        await callback.message.edit_text("📊 <b>CSV fayl tayyor!</b>", reply_markup=get_admin_keyboard(), parse_mode="HTML")
        await callback.message.answer_document(csv_file)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in export: {e}")
        await callback.answer("❌ Exportda xatolik")


async def get_detailed_statistics(session: AsyncSession) -> dict:
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = datetime.now() - timedelta(days=7)
    
    total_users = await UserRepository.count_users(session)
    

    result = await session.execute(
        select(func.count(distinct(User.id)))
        .where(User.last_activity >= week_ago)
    )
    active_users_7d = result.scalar_one()
    

    result = await session.execute(
        select(func.count(distinct(User.id)))
        .where(User.is_getcourse_client == True)
    )
    verified_users = result.scalar_one()
    

    result = await session.execute(
        select(func.count(InterviewSession.id))
    )
    total_interviews = result.scalar_one()
    

    completed_interviews = await InterviewSessionRepository.count_completed_sessions(session)
    

    completion_rate = (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0
    
    result = await session.execute(
        select(func.count(InterviewSession.id).label('count'))
        .where(InterviewSession.status == "active") 
    )
    dropoff_count = result.scalar_one() or 0
    most_dropoff_step = "Active sessions" 
    dropoff_rate = (dropoff_count / total_interviews * 100) if total_interviews > 0 else 0
    
    result = await session.execute(
        select(func.count(Recommendation.id)).where(Recommendation.recommendation_type == "stock_ideas")
    )
    recommendations_ideas = result.scalar_one() or 0
    result = await session.execute(
        select(func.count(Recommendation.id)).where(Recommendation.recommendation_type == "portfolio")
    )
    recommendations_portfolio = result.scalar_one() or 0
    total_recs = recommendations_ideas + recommendations_portfolio
    ideas_percentage = (recommendations_ideas / total_recs * 100) if total_recs > 0 else 0
    portfolio_percentage = (recommendations_portfolio / total_recs * 100) if total_recs > 0 else 0
    
    result = await session.execute(
        select(func.count(User.id)).where(User.created_at >= today)
    )
    new_users_today = result.scalar_one() or 0
    
    result = await session.execute(
        select(func.count(InterviewSession.id))
        .where(and_(InterviewSession.status == "completed", InterviewSession.completed_at >= today))
    )
    completed_today = result.scalar_one() or 0
    
    result = await session.execute(
        select(func.avg(Recommendation.generation_time))
    )
    avg_generation_time = result.scalar_one() or 0
    
    return {
        'total_users': total_users,
        'active_users_7d': active_users_7d,
        'verified_users': verified_users,
        'total_interviews': total_interviews,
        'completed_interviews': completed_interviews,
        'completion_rate': completion_rate,
        'most_dropoff_step': most_dropoff_step,
        'dropoff_rate': dropoff_rate,
        'recommendations_ideas': recommendations_ideas,
        'recommendations_portfolio': recommendations_portfolio,
        'ideas_percentage': ideas_percentage,
        'portfolio_percentage': portfolio_percentage,
        'new_users_today': new_users_today,
        'completed_today': completed_today,
        'avg_generation_time': avg_generation_time
    }