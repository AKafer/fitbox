from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from web.transactions.schemas import TransactionCreateByAdminInput, TransactionCreateInput


class TransactionCreateError(Exception):
    pass

async def check_before_create(
    transaction_input: TransactionCreateInput | TransactionCreateByAdminInput,
    user: User,
    db_session: AsyncSession,
) -> None:
    pass
