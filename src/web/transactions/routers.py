import sqlalchemy
from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from database.models import User, Transactions
from dependencies import get_db_session
from starlette.exceptions import HTTPException

from main_schemas import ResponseErrorBody

from web.transactions.filters import TransactionsFilter
from web.transactions.schemas import Transaction, TransactionCreateInput, TransactionCreateByAdminInput
from web.transactions.services import check_before_create, TransactionCreateError
from web.users.users import current_superuser, current_user

router = APIRouter(
    prefix='/transactions',
    tags=['transactions'],
)

@router.get(
    '/',
    response_model=list[Transaction],
    dependencies=[Depends(current_superuser)]
)
async def get_all_transactions(
    db_session: AsyncSession = Depends(get_db_session),
    transactions_filter: TransactionsFilter = FilterDepends(TransactionsFilter),
):
    query = select(Transactions).order_by(Transactions.id.desc())
    query = transactions_filter.filter(query)
    transactions = await db_session.execute(query)
    return transactions.scalars().all()


@router.post(
    '/',
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_user)]
)
async def create_user_transaction(
    transaction_input: TransactionCreateInput,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Superuser cannot create transactions',
        )
    try:
        await check_before_create(transaction_input, user,  db_session)
    except TransactionCreateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Can not create new Transaction: {e}',
        )
    try:
        db_transaction = Transactions(**transaction_input.model_dump())
        db_transaction.user_id = user.id
        db_session.add(db_transaction)
        if user.count_trainings is not None:
            user.count_trainings += transaction_input.count
        else:
            user.count_trainings = transaction_input.count
        await db_session.commit()
        await db_session.refresh(db_transaction)
        return db_transaction
    except sqlalchemy.exc.IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Some error while creating new Transaction: {e}',
        )


@router.post(
    '/by-admin',
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            'model': ResponseErrorBody,
        },
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_superuser)]
)
async def create_admin_transaction(
    transaction_input: TransactionCreateByAdminInput,
    db_session: AsyncSession = Depends(get_db_session),
):
    query = select(User).filter(User.id == transaction_input.user_id)
    user = await db_session.scalar(query)
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Superuser cannot create transactions',
        )
    try:
        await check_before_create(transaction_input, user,  db_session)
    except TransactionCreateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Can not create new Transaction: {e}',
        )
    try:
        db_transaction = Transactions(**transaction_input.model_dump())
        db_session.add(db_transaction)
        if user.count_trainings is not None:
            user.count_trainings += transaction_input.count
        else:
            user.count_trainings = transaction_input.count
        await db_session.commit()
        await db_session.refresh(db_transaction)
        return db_transaction
    except sqlalchemy.exc.IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Some error while creating new Transaction: {e}',
        )


@router.delete(
    '/{transaction_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'model': ResponseErrorBody,
        },
    },
    dependencies=[Depends(current_user)]
)
async def delete_transaction(
    transaction_id: int,
    db_session: AsyncSession = Depends(get_db_session),
    user: User = Depends(current_user)
):
    query = select(Transactions).filter(Transactions.id == transaction_id)
    transaction = await db_session.scalar(query)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Transaction with id {transaction_id} not found',
        )
    query = select(User).filter(User.id == transaction.user_id)
    user_tr = await db_session.scalar(query)
    if user_tr is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'User with id {transaction.user_id} not found',
        )
    if not  user.is_superuser:
        if transaction.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You do not have permission to delete this transaction',
            )
    try:
        user_tr.count_trainings -= transaction.count
        await db_session.delete(transaction)
        await db_session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Some error while deleting Transaction: {e}',
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
