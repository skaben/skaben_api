from typing import List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from skaben.database import get_db
from sqlalchemy import select, delete
from sqlalchemy.exc import NoResultFound

from skaben.models.state import State, AlertCounter
from skaben.schema.state import (
    StateSchema, ResponseStateSchema, StateUpdateSchema,
    AlertCounterSchema, AlertCounterRelativeSchema
)
from skaben.modules.state import methods

router = APIRouter(
    prefix="/alert",
    tags=["alert"],
    responses={404: {"description": "Alert not found"}},
)


@router.get('/counter', response_model=List[AlertCounterSchema])
async def get_counters(session = Depends(get_db)):
    """Возвращает список счетчиков тревоги"""
    stmt = select(AlertCounter).order_by(AlertCounter.timestamp.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get('/counter/last', response_model=AlertCounterSchema)
async def get_counter_last(session = Depends(get_db)):
    """Возвращает последнее значение счетчика"""
    return await methods.get_last_counter(session)


@router.post('/counter', response_model=AlertCounterSchema)
async def create_counter(counter: AlertCounterSchema, session = Depends(get_db)):
    """Создает запись счетчика уровня тревоги"""
    counter_instance = AlertCounter(**counter.dict())
    await counter_instance.save(session)
    return counter_instance


@router.patch('/counter', response_model=AlertCounterRelativeSchema)
async def change_counter(counter: AlertCounterRelativeSchema, session = Depends(get_db)):
    return await methods.change_counter(session, counter)


@router.get('/state', response_model=List[StateSchema])
async def get_states(name: str | None = None,
                     order: int | None = None,
                     current: bool | None = None,
                     session = Depends(get_db)):
    """Получение списка всех глобальных состояний игры"""
    stmt = select(State)
    if name:
        stmt = stmt.where(State.name == name)
    if order:
        stmt = stmt.where(State.order == order)
    if current:
        stmt = stmt.where(State.current == current)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get('/state/{counter}')
async def get_state_by_counter(counter: int, session = Depends(get_db)):
    """Получение состояния по значению счетчика тревоги"""
    stmt = select(State).where(State.threshold <= counter)\
                              .order_by(State.threshold.desc())
    result = await session.execute(stmt)
    return result.scalars().first()


@router.post('/state/', response_model=ResponseStateSchema)
async def create_state(state: StateSchema, session = Depends(get_db)):
    """Создание нового глобального состояния игры"""
    state_instance = State(**state.dict())
    await state_instance.save(session)
    return state_instance


@router.patch('/state/{name}', response_model=ResponseStateSchema)
async def update_state(name: str, state: StateUpdateSchema, session = Depends(get_db)):
    """Изменение существующего глобального состояния игры"""
    try:
        return await methods.update_state(session, name, state)
    except NoResultFound:
        return HTTPException(status_code=400, detail=f'State with name {name} not found')


@router.delete('/state/{uuid}')
async def delete_state(uuid: str, session = Depends(get_db)):
    stmt = delete(State).where(State.uuid == uuid)
    await session.execute(stmt)
    return f'{uuid} deleted'
