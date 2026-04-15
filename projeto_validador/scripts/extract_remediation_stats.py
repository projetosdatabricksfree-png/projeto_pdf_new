import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "sqlite+aiosqlite:///./data/validador.db"

async def get_remediation_events():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT job_id, payload FROM events WHERE agent_name = 'remediador'"))
        events = result.all()
        
        print(f"Found {len(events)} remediation events")
        for job_id, payload in events:
            try:
                data = json.loads(payload)
                report = data.get("payload", {})
                actions = report.get("actions", [])
                
                print(f"\nJob: {job_id}")
                for action in actions:
                    status = "✅" if action.get("success") else "❌"
                    print(f"  {status} {action.get('remediator')}: {action.get('codigo')}")
                    for change in action.get("changes_applied", []):
                        print(f"    - {change}")
            except Exception as e:
                print(f"Error parsing payload for {job_id}: {e}")
                
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(get_remediation_events())
