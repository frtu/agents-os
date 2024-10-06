import logging
# Set up logging
logger = logging.getLogger("main")
logging.basicConfig(level=logging.INFO)

import asyncio
from temporalio import activity
from temporalio.client import Client

from workflows.openai_workflow import OpenAIWorkflow

async def main():
    temporal_client = await Client.connect("localhost:7233")

    prompts = ["What is the capital of Spain?", "What is the most common color of an apple?", "What is the meaning of life?"]
    try:
        result = await temporal_client.execute_workflow(
            OpenAIWorkflow.run,
            prompts,
            id="openai-workflow-id",
            task_queue="openai-task-queue"
        )
        logger.info(f"Workflow results: {result}")
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())