import json
from aiohttp import web
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Poll, Question, Option, Vote
from sqlalchemy.orm import sessionmaker, selectinload, joinedload
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://root:root@localhost:5432/testdbname"
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_poll(request):
    try:
        data = await request.json()
        async with SessionLocal() as session:
            new_poll = Poll(title=data['title'])
            session.add(new_poll)
            await session.commit()
            await session.refresh(new_poll)
            for question_data in data.get('questions', []):
                question = Question(text=question_data['text'], poll_id=new_poll.id)
                session.add(question)
                await session.commit()
                await session.refresh(question)

                for option_text in question_data.get('options', []):
                    option = Option(text=option_text, question_id=question.id)
                    session.add(option)
                await session.commit()

            return web.Response(text=f"Poll '{new_poll.title}' created with id {new_poll.id}", status=201)
    except json.decoder.JSONDecodeError:
        return web.Response(text="Invalid JSON", status=400)
    except KeyError as e:
        return web.Response(text=f"Missing data: {e}", status=400)


async def delete_poll(request):
    poll_id = int(request.match_info['poll_id'])
    async with SessionLocal() as session:
        poll = await session.get(Poll, poll_id)
        if poll:
            await session.delete(poll)
            await session.commit()
            return web.Response(text=f"Poll with id {poll_id} deleted", status=200)
        else:
            return web.Response(text="Poll not found", status=404)


async def list_polls(request):
    async with SessionLocal() as session:
        result = await session.execute(select(Poll))
        polls = result.scalars().all()
        data = [{"id": poll.id, "title": poll.title} for poll in polls]
        return web.json_response(data)


async def get_poll(request):
    poll_id = int(request.match_info['poll_id'])
    async with SessionLocal() as session:
        stmt = (
            select(Poll)
            .options(selectinload(Poll.questions).selectinload(Question.options))
            .where(Poll.id == poll_id)
        )
        result = await session.execute(stmt)
        poll = result.scalar_one_or_none()

        if poll:
            questions_data = []
            for question in poll.questions:
                options_data = [{"id": option.id, "text": option.text} for option in question.options]
                questions_data.append({"id": question.id, "text": question.text, "options": options_data})
            data = {"id": poll.id, "title": poll.title, "questions": questions_data}
            return web.json_response(data)
        else:
            return web.Response(text="Poll not found", status=404)


async def cast_vote(request):
    poll_id = int(request.match_info['poll_id'])
    data = await request.json()
    option_id = data.get('option_id')
    async with SessionLocal() as session:
        option = await session.get(Option, option_id)
        if option and option.question.poll_id == poll_id:
            new_vote = Vote(option_id=option_id)
            session.add(new_vote)
            await session.commit()
            return web.Response(text="Vote cast successfully", status=200)
        else:
            return web.Response(text="Invalid option or poll", status=400)


app = web.Application()
app.add_routes([
    web.post('/polls/', create_poll),
    web.delete('/polls/{poll_id}/', delete_poll),
    web.get('/polls/', list_polls),
    web.get('/polls/{poll_id}/', get_poll),
    web.post('/polls/{poll_id}/', cast_vote),
])

if __name__ == '__main__':
    web.run_app(app, port=8080)
