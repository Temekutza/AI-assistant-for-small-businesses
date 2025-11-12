import logging
import asyncio
from dotenv import load_dotenv
load_dotenv("config.env") 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)