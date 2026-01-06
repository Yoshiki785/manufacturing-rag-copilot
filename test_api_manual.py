"""Manual API testing script with mocked OpenAI calls."""

import asyncio
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.app.db.models import Document, Chunk, Embedding, Base
from src.app.rag.chunk import chunk_document

# Test database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/manufacturing_rag_test"

async def setup_test_data():
    """Insert test manufacturing data directly into the database."""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Manufacturing document content
        content = """Manufacturing Process Standard Operating Procedure (SOP)

Equipment: CNC Milling Machine Model XYZ-3000

1. Safety Requirements:
- Always wear safety glasses and protective equipment
- Ensure emergency stop button is accessible
- Check machine guards are in place before operation

2. Operating Parameters:
- Spindle Speed: 2500-3500 RPM for aluminum parts
- Feed Rate: 150-200 mm/min recommended
- Coolant: Use water-soluble coolant mixture (1:20 ratio)

3. Quality Control:
- Measure critical dimensions every 5 parts
- Tolerance: ±0.05mm for precision components
- Surface finish: Ra value should not exceed 1.6 μm

4. Torque Specifications:
- Tool holder tightening torque: 45 Nm
- Workpiece clamping: 30-35 Nm
- Use calibrated torque wrench for all operations

5. Maintenance Schedule:
- Daily: Check coolant level and clean chip tray
- Weekly: Lubricate guide rails and ball screws
- Monthly: Inspect tool holder and spindle runout"""

        # Create document
        doc_id = uuid4()
        document = Document(
            id=doc_id,
            title="CNC Milling Machine SOP",
            content=content,
            source_type="SOP",
            meta={"equipment": "XYZ-3000", "version": "2.1"}
        )
        session.add(document)

        # Create chunks
        chunks_data = chunk_document(content)
        print(f"Created {len(chunks_data)} chunks")

        for chunk_data in chunks_data:
            chunk_id = uuid4()
            chunk = Chunk(
                id=chunk_id,
                document_id=doc_id,
                content=chunk_data.content,
                chunk_index=chunk_data.chunk_index,
                start_char=chunk_data.start_char,
                end_char=chunk_data.end_char,
                meta={}
            )
            session.add(chunk)

            # Create dummy embedding (normalized random vector)
            import random
            import math

            # Create a random but normalized 1536-dim vector
            vec = [random.gauss(0, 0.1) for _ in range(1536)]
            magnitude = math.sqrt(sum(x*x for x in vec))
            normalized_vec = [x/magnitude for x in vec]

            embedding = Embedding(
                id=uuid4(),
                chunk_id=chunk_id,
                embedding=normalized_vec,
                model_name="text-embedding-3-small-mock"
            )
            session.add(embedding)

        await session.commit()
        print(f"✅ Inserted document {doc_id} with {len(chunks_data)} chunks and embeddings")

    await engine.dispose()
    return doc_id

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(setup_test_data())
