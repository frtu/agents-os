import sys
import os
# Add the directory containing 'activities' and 'workflows' to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
load_dotenv()

import openai  # for calling the OpenAI API
# Load your API key from an environment variable or secret management service
openai.api_key = os.getenv("OPENAI_API_KEY")

import logging
# Set up logging
logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO)

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from activities.openai_activities import OpenAIActivities
from workflows.openai_workflow import OpenAIWorkflow

async def run_worker() -> None:
    logger.info("Starting the Temporal worker...")
    try:
        client: Client = await Client.connect("localhost:7233", namespace="default")
        logger.info("Connected to Temporal server.")
        
        # Create an instance of OpenAIActivities
        openai_activities = OpenAIActivities()

        workflows = [OpenAIWorkflow]
        activities = [openai_activities.call_openai_api]

        # Run the worker
        worker_instance: Worker = Worker(
            client,
            task_queue="openai-task-queue",
            workflows=workflows,
            activities=activities,
        )

        logger.info("Worker instance created, now running...")
        await worker_instance.run()
        logger.info("Worker is running.")
    except Exception as e:
        logger.error(f"Error in running worker: {e}", exc_info=True)

def main():
    asyncio.run(run_worker())

if __name__ == "__main__":
    main()
