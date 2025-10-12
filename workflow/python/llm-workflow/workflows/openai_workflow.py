import logging
# Set up logging
logger = logging.getLogger("OpenAIWorkflow")
logging.basicConfig(level=logging.INFO)

import asyncio
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

from datetime import timedelta

@workflow.defn(name="OpenAIWorkflow") 
class OpenAIWorkflow:
    @workflow.run
    async def run(self, prompts: list) -> list:
        results = []
        futures = []

        for prompt in prompts:
            # Log the processing of each prompt at a high level
            # workflow.side_effect(lambda: logger.info(f"Processing prompt: {prompt}"))
            logger.info(f"Processing prompt: {prompt}")
            future = workflow.execute_activity(
                "call_openai_api",  # Use the activity by name
                args=[prompt],
                start_to_close_timeout=timedelta(seconds=30)
            )
            futures.append(future)
        
        results = await asyncio.gather(*futures)
        return results