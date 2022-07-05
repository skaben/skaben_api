from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound
from skaben.database import AsyncSession
from skaben.models.state import State, AlertCounter
from skaben.schema.state import StateUpdateSchema, AlertCounterSchema, AlertCounterRelativeSchema


async def get_last_counter(session: AsyncSession):
    """Возвращает последнее значение счетчика тревоги"""
    stmt = select(AlertCounter).order_by(AlertCounter.timestamp.desc())
    res = await session.execute(stmt)
    return res.scalars().first()


async def get_current_state(session: AsyncSession):
    """Возвращает текущий уровень тревоги"""
    stmt = select(State).where(State.current == True)
    res = await session.execute(stmt)
    current = res.scalars().one_or_none()
    if not current:
        raise ValueError('Current state is not set')
    return current


async def update_state(session: AsyncSession, name: str, data: dict | StateUpdateSchema, auto: bool = True):
    """Обновляет глобальное состояние уровня тревоги

       Апдейт счетчика тревоги происходит автоматически
    """
    schema = StateUpdateSchema(**data) if isinstance(data, dict) else data
    validated = schema.dict(exclude_none=True)
    current_changed = validated.get('current')
    stmt = select(State).where(State.name == name)
    result = await session.execute(stmt)
    state_instance = result.scalars().one_or_none()
    if not state_instance:
        raise NoResultFound(f'State with name `{name}` not found')
    if current_changed:
        # снимаем флаг current со всех остальных состояний
        unset_current = update(State).where(State.current, State.name != name)\
                                     .values(current=False)\
                                     .execution_options(synchronize_session=False)
        await session.execute(unset_current)
    update_stmt = update(State).where(State.name == name).values(**validated)
    await session.execute(update_stmt)
    if auto:
        await set_counter_by_state_lower_threshold(session, state_instance)
    await session.commit()
    return state_instance


async def create_counter(session: AsyncSession, data: dict | AlertCounterSchema, auto: bool = True):
    """Создает новое значение счетчика уровня тревоги"""
    schema = AlertCounterSchema(**data) if isinstance(data, dict) else data
    counter_instance = AlertCounter(**schema.dict())
    if auto:
        await switch_state_by_counter(session, counter_instance)
    await counter_instance.save(session)
    return counter_instance


async def change_counter(session: AsyncSession, counter: AlertCounterRelativeSchema):
    """Создает новое значение счетчика уровня тревоги на основании предыдущих"""
    last_counter = await get_last_counter(session)
    new_value = last_counter.value + counter.value if counter.increase else last_counter.value - counter.value
    payload = counter.dict()
    payload.update(value=new_value)
    new_counter = AlertCounterSchema(**payload)
    await create_counter(session, new_counter)
    return new_counter


async def set_counter_by_state_lower_threshold(session: AsyncSession, state_instance: State):
    """Сбрасывает счетчик в соответствии с нижним порогом состояния

       Работает только для состояний "в игре" - т.е. с нижним порогом >= 0
    """
    if state_instance.is_ingame():
        schema = AlertCounterSchema(value=state_instance.threshold, comment=f"Auto-set by state {state_instance.name}")
        return await create_counter(session, schema, auto=False)


async def switch_state_by_counter(session: AsyncSession, counter: AlertCounter):
    """Переключает глобальное состояние по счетчику"""
    current = await get_current_state(session)
    if not current.is_ingame:
        return

    stmt = select(State).where(State.threshold <= counter.value).order_by(State.threshold.desc())
    res = await session.execute(stmt)
    state = res.scalars().first()
    if not state:
        return
    if not state.current:
        await update_state(session, state.name, {'current': True}, auto=False)
