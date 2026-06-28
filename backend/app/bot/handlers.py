"""Bot command and message handlers."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import dashboard_keyboard, split_keyboard, undo_keyboard
from app.database import AsyncSessionLocal
from app.models.enums import TxnScope, TxnType
from app.services import analytics, crud
from app.services.parser import ParseError

router = Router(name="finbuddy")

_CURRENCY_SYMBOLS = {
    "INR": "\u20b9",
    "USD": "$",
    "EUR": "\u20ac",
    "GBP": "\u00a3",
    "JPY": "\u00a5",
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
}


def _money(currency: str, amount) -> str:
    """Format an amount with its currency symbol, e.g. \u20b91,000."""
    symbol = _CURRENCY_SYMBOLS.get((currency or "").upper())
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    rendered = f"{value:,.2f}".rstrip("0").rstrip(".")
    if symbol:
        return f"{symbol}{rendered}"
    return f"{currency} {rendered}"

WELCOME = (
    "👋 <b>Welcome to FinBuddy!</b>\n\n"
    "I help you track money in plain language. Just type an expense like:\n"
    "<code>1000-zomato</code>  or  <code>250 auto</code>\n"
    "Income works too: <code>+50000 salary</code>\n\n"
    "Commands:\n"
    "• /dashboard — open your visual dashboard\n"
    "• /balance — quick monthly snapshot\n"
    "• /report — AI summary &amp; savings tips\n"
    "• /invite — share your space with a partner\n"
    "• /help — show this message"
)


async def _ensure_context(message: Message):
    """Return ``(session_factory_user, space)`` ensuring user + space exist."""
    async with AsyncSessionLocal() as session:
        tg = message.from_user
        user = await crud.get_or_create_user(
            session,
            telegram_id=tg.id,
            first_name=tg.first_name or "there",
            username=tg.username,
            language_code=tg.language_code,
        )
        space = await crud.ensure_personal_space(session, user)
        await session.commit()
        return user.id, space.id


@router.message(CommandStart(deep_link=True))
async def start_with_payload(message: Message, command: CommandObject) -> None:
    payload = (command.args or "").strip()
    async with AsyncSessionLocal() as session:
        tg = message.from_user
        user = await crud.get_or_create_user(
            session,
            telegram_id=tg.id,
            first_name=tg.first_name or "there",
            username=tg.username,
            language_code=tg.language_code,
        )
        await crud.ensure_personal_space(session, user)

        if payload.startswith("join_"):
            code = payload[len("join_"):]
            space = await crud.get_space_by_invite(session, code)
            if space is None:
                await session.commit()
                await message.answer("❌ That invite link is invalid or expired.")
                return
            await crud.join_space(session, space=space, user=user)
            await session.commit()
            await message.answer(
                f"✅ You joined <b>{space.name}</b>! You now share this budget."
            )
            return
        await session.commit()
    await message.answer(WELCOME, reply_markup=dashboard_keyboard())


@router.message(CommandStart())
async def start(message: Message) -> None:
    await _ensure_context(message)
    await message.answer(WELCOME, reply_markup=dashboard_keyboard())


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=dashboard_keyboard())


@router.message(Command("dashboard"))
async def dashboard(message: Message) -> None:
    kb = dashboard_keyboard()
    if kb is None:
        await message.answer(
            "The web dashboard isn't configured yet. Ask the admin to set "
            "<code>MINIAPP_URL</code>. Meanwhile try /balance and /report."
        )
        return
    await message.answer("Tap below to open your dashboard 👇", reply_markup=kb)


@router.message(Command("invite"))
async def invite(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        tg = message.from_user
        user = await crud.get_or_create_user(
            session,
            telegram_id=tg.id,
            first_name=tg.first_name or "there",
            username=tg.username,
        )
        space = await crud.ensure_personal_space(session, user)
        code = space.invite_code
        name = space.name
        await session.commit()
    me = await message.bot.me()
    link = f"https://t.me/{me.username}?start=join_{code}"
    await message.answer(
        f"🔗 Share this link to invite someone into <b>{name}</b>:\n{link}\n\n"
        f"Or share the code: <code>{code}</code>"
    )


@router.message(Command("balance"))
async def balance(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        tg = message.from_user
        user = await crud.get_or_create_user(
            session, telegram_id=tg.id, first_name=tg.first_name or "there"
        )
        space = await crud.ensure_personal_space(session, user)
        summary = await analytics.space_summary(session, space)
        await session.commit()
    cur = summary["space"].currency
    await message.answer(
        f"\U0001f4c5 <b>{summary['month']}</b> — {summary['space'].name}\n\n"
        f"\U0001f4b8 Spent: {_money(cur, summary['total_spent'])}\n"
        f"\U0001f4b0 Income: {_money(cur, summary['total_income'])}\n"
        f"\U0001f4c8 Net: {_money(cur, summary['net'])}\n"
        f"\U0001f3e6 Accounts: {_money(cur, summary['accounts_balance'])}\n"
        f"\U0001f4ca Investments: {_money(cur, summary['investments_value'])}"
    )


@router.message(Command("report"))
async def report(message: Message) -> None:
    from app.services.ai import monthly_summary

    async with AsyncSessionLocal() as session:
        tg = message.from_user
        user = await crud.get_or_create_user(
            session, telegram_id=tg.id, first_name=tg.first_name or "there"
        )
        space = await crud.ensure_personal_space(session, user)
        summary = await analytics.space_summary(session, space)
        insight = await analytics.insights(session, space)
        await session.commit()
        currency = space.currency

    categories = [(c.category, c.amount) for c in insight["categories"]]
    text, advice = await monthly_summary(
        month=summary["month"],
        currency=currency,
        total_spent=summary["total_spent"],
        total_income=summary["total_income"],
        categories=categories,
    )
    tips = "\n".join(f"• {a}" for a in advice)
    await message.answer(f"🧾 <b>{summary['month']} report</b>\n\n{text}\n\n{tips}")


@router.message(F.text & ~F.text.startswith("/"))
async def log_expense(message: Message) -> None:
    text = (message.text or "").strip()
    async with AsyncSessionLocal() as session:
        tg = message.from_user
        user = await crud.get_or_create_user(
            session,
            telegram_id=tg.id,
            first_name=tg.first_name or "there",
            username=tg.username,
        )
        space = await crud.ensure_personal_space(session, user)
        try:
            txn = await crud.create_transaction(
                session, space=space, payer=user, raw_text=text
            )
        except (ParseError, ValueError):
            await session.rollback()
            await message.answer(
                "🤔 I couldn't read that. Try something like "
                "<code>1000-zomato</code> or <code>+50000 salary</code>."
            )
            return
        await session.commit()
        cur = space.currency
        emoji = "💰" if txn.type == TxnType.INCOME else "💸"
        verb = "Income" if txn.type == TxnType.INCOME else "Logged"
        body = (
            f"{emoji} <b>{verb}</b> {_money(cur, txn.amount)}\n"
            f"📂 {txn.category} · {txn.note}"
        )
        is_shared_space = len(space.members) > 1
        txn_id = txn.id

    if is_shared_space and txn.type == TxnType.EXPENSE:
        await message.answer(
            body + "\n\nWhose expense is this?",
            reply_markup=split_keyboard(txn_id),
        )
    else:
        await message.answer(body, reply_markup=undo_keyboard(txn_id))


@router.callback_query(F.data.startswith("scope:"))
async def set_scope(callback: CallbackQuery) -> None:
    _, txn_id_str, scope_str = callback.data.split(":")
    txn_id = int(txn_id_str)
    new_scope = TxnScope.SHARED if scope_str == "shared" else TxnScope.PERSONAL

    async with AsyncSessionLocal() as session:
        txn = await crud.get_transaction(session, txn_id)
        if txn is None:
            await callback.answer("Transaction not found", show_alert=True)
            return
        space = await crud.get_space(session, txn.space_id)
        txn.scope = new_scope
        # Reset splits and recompute equally for shared.
        txn.splits.clear()
        if new_scope == TxnScope.SHARED and space is not None:
            await session.flush()
            from app.models.transaction import TransactionSplit
            from app.services.crud import _equal_splits

            member_ids = [m.user_id for m in space.members]
            for uid, share in _equal_splits(txn.amount, member_ids).items():
                txn.splits.append(TransactionSplit(user_id=uid, share=share))
        await session.commit()

    label = "shared 👥" if new_scope == TxnScope.SHARED else "personal 🙋"
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(f"Marked as {label}")
    await callback.message.answer(f"✅ Updated to <b>{label}</b>.")


@router.callback_query(F.data.startswith("del:"))
async def delete_txn(callback: CallbackQuery) -> None:
    txn_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        txn = await crud.get_transaction(session, txn_id)
        if txn is not None:
            await session.delete(txn)
            await session.commit()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Deleted")
    await callback.message.answer("🗑 Transaction deleted.")
