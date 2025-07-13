"""
Database utilities and connection management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import os
from typing import Optional
import logging
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database management for the MSME SaaS platform"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Establish database connection"""
        try:
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME', 'msme_saas')
            
            if not mongo_url:
                raise ValueError("MONGO_URL environment variable is required")
                
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            
            # Create indexes for better performance
            await self._create_indexes()
            
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index("created_at")
            
            # Invoices collection indexes
            await self.db.invoices.create_index("user_id")
            await self.db.invoices.create_index("customer_id")
            await self.db.invoices.create_index("status")
            await self.db.invoices.create_index("due_date")
            await self.db.invoices.create_index("created_at")
            
            # Customers collection indexes
            await self.db.customers.create_index("user_id")
            await self.db.customers.create_index("email")
            await self.db.customers.create_index("created_at")
            
            # Reports collection indexes
            await self.db.reports.create_index("user_id")
            await self.db.reports.create_index("report_type")
            await self.db.reports.create_index("created_at")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

# Global database manager instance
db_manager = DatabaseManager()