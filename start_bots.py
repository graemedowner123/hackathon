#!/usr/bin/env python3
"""
Script to start the automated bot bidding system for the P2P lending platform
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_bidding.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to start bot bidding"""
    logger.info("Starting P2P Lending Bot Bidding System")
    logger.info(f"Current time: {datetime.now()}")
    
    try:
        # Import bot manager
        from bot_lenders import BotLenderManager
        
        # Create bot manager instance
        bot_manager = BotLenderManager()
        
        # Check if bots already exist, if not create them
        if not bot_manager.bots:
            logger.info("Creating bot lenders...")
            bot_manager.create_bot_lenders()
            logger.info(f"Created {len(bot_manager.bots)} bot lenders")
        else:
            logger.info(f"Found {len(bot_manager.bots)} existing bot lenders")
        
        # Display bot information
        for bot in bot_manager.bots:
            logger.info(f"Bot: {bot.name} - Strategy: {bot.strategy} - Capital: ${bot.capital}")
        
        # Start automated bidding
        logger.info("Starting automated bidding process...")
        bot_manager.start_automated_bidding(check_interval=30)  # Check every 30 seconds
        
        logger.info("Bot bidding system is now running!")
        logger.info("Press Ctrl+C to stop the system")
        
        # Keep the script running
        try:
            while True:
                time.sleep(60)  # Sleep for 1 minute
                
                # Print periodic status
                stats = bot_manager.get_bot_stats()
                logger.info(f"Status - Total Bots: {stats['total_bots']}, "
                          f"Active Bids: {stats['active_bids']}, "
                          f"Available Capital: ${stats['available_capital']:,.2f}")
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping bot system...")
            bot_manager.stop_automated_bidding()
            logger.info("Bot bidding system stopped successfully")
            
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        logger.error("Make sure all dependencies are installed and DynamoDB is configured")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error starting bot system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
