# memory.py
from typing import List, Optional
import uuid
from datetime import datetime
import aiosqlite
import json
from models import Memory, Perception, PerceptionType

class MemoryModule:
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path

    async def initialize_db(self):
        """Initialize SQLite database and create necessary tables."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create memories table if it doesn't exist
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        context TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_accessed TEXT NOT NULL,
                        importance_score REAL NOT NULL,
                        UNIQUE(id)
                    )
                """)
                
                # Create indices for better query performance
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_content ON memories(content)
                """)
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance_score)
                """)
                
                await db.commit()
                print("Database initialized successfully")
                
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise

    async def store_memory(self, perception: Perception) -> Memory:
        """Create and store a new memory from a perception."""
        try:
            # Ensure database is initialized
            await self.initialize_db()

            # Create memory object
            memory = Memory(
                id=str(uuid.uuid4()),
                content=perception.content,
                context={
                    "perception_type": perception.input_type.value if isinstance(perception.input_type, PerceptionType) else str(perception.input_type),
                    "original_metadata": perception.metadata
                },
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                importance_score=self._calculate_importance(perception)
            )

            # Store in database
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO memories 
                    (id, content, context, created_at, last_accessed, importance_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    memory.id,
                    memory.content,
                    json.dumps(memory.context),
                    memory.created_at.isoformat(),
                    memory.last_accessed.isoformat(),
                    memory.importance_score
                ))
                await db.commit()

            return memory

        except Exception as e:
            print(f"Error storing memory: {str(e)}")
            raise

    async def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """Retrieve relevant memories based on a query."""
        try:
            # Ensure database is initialized
            await self.initialize_db()

            async with aiosqlite.connect(self.db_path) as db:
                # Simple keyword-based retrieval
                cursor = await db.execute("""
                    SELECT * FROM memories 
                    WHERE content LIKE ? 
                    ORDER BY importance_score DESC 
                    LIMIT ?
                """, (f"%{query}%", limit))
                
                rows = await cursor.fetchall()
                
                memories = []
                for row in rows:
                    memory = Memory(
                        id=row[0],
                        content=row[1],
                        context=json.loads(row[2]),
                        created_at=datetime.fromisoformat(row[3]),
                        last_accessed=datetime.fromisoformat(row[4]),
                        importance_score=row[5]
                    )
                    memories.append(memory)
                    
                    # Update last accessed time
                    await self._update_last_accessed(memory.id)

                return memories

        except Exception as e:
            print(f"Error retrieving memories: {str(e)}")
            return []

    async def _update_last_accessed(self, memory_id: str):
        """Update the last accessed timestamp for a memory."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE memories 
                    SET last_accessed = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), memory_id))
                await db.commit()
        except Exception as e:
            print(f"Error updating last accessed time: {str(e)}")

    def _calculate_importance(self, perception: Perception) -> float:
        """Calculate importance score for a perception."""
        importance = 0.5  # Base importance

        try:
            # Safely handle perception type
            if hasattr(perception, 'input_type'):
                if isinstance(perception.input_type, PerceptionType):
                    # Add importance based on type
                    if perception.input_type == PerceptionType.TEXT:
                        importance += 0.1
                    elif perception.input_type == PerceptionType.IMAGE:
                        importance += 0.2

            # Adjust based on content length
            content_length = len(perception.content)
            if content_length > 100:
                importance += 0.2
            elif content_length > 50:
                importance += 0.1

            # Adjust based on enhanced analysis if available
            if perception.metadata and "enhanced_analysis" in perception.metadata:
                importance += 0.2

        except Exception as e:
            print(f"Error calculating importance: {str(e)}")

        # Ensure importance is between 0 and 1
        return min(1.0, max(0.0, importance))

    async def cleanup_old_memories(self, days_old: int = 30):
        """Remove memories older than specified days."""
        try:
            cutoff_date = (datetime.now() - datetime.timedelta(days=days_old)).isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    DELETE FROM memories 
                    WHERE created_at < ?
                """, (cutoff_date,))
                await db.commit()
                
        except Exception as e:
            print(f"Error cleaning up old memories: {str(e)}")

    async def get_memory_stats(self) -> dict:
        """Get statistics about stored memories."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_memories,
                        AVG(importance_score) as avg_importance,
                        MIN(created_at) as oldest_memory,
                        MAX(created_at) as newest_memory
                    FROM memories
                """)
                
                row = await cursor.fetchone()
                
                return {
                    "total_memories": row[0],
                    "average_importance": row[1],
                    "oldest_memory": row[2],
                    "newest_memory": row[3]
                }
                
        except Exception as e:
            print(f"Error getting memory stats: {str(e)}")
            return {}

# Example usage
async def test_memory():
    try:
        # Initialize memory module
        memory_module = MemoryModule()
        await memory_module.initialize_db()

        # Create test perception
        test_perception = Perception(
            input_type=PerceptionType.TEXT,
            content="Test memory content",
            metadata={"test": "metadata"}
        )

        # Store memory
        stored_memory = await memory_module.store_memory(test_perception)
        print(f"Stored memory: {stored_memory.dict()}")

        # Get stats
        stats = await memory_module.get_memory_stats()
        print(f"Memory stats: {stats}")

    except Exception as e:
        print(f"Error in test: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_memory())