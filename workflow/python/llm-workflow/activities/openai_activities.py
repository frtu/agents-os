from dotenv import load_dotenv
load_dotenv()

import logging
# Set up logging
logger = logging.getLogger("OpenAIActivities")
logging.basicConfig(level=logging.INFO)

import asyncio
from temporalio import activity

class OpenAIActivities:
    @activity.defn(name="call_openai_api")  # Ensure the activity is decorated and named
    async def call_openai_api(self, prompt: str) -> str:
        logger.info(f"Calling OpenAI API with prompt: {prompt}")
        try:
            client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
            )
            result = response.choices[0].message.content.strip()
            logger.info(f"Received response: {result}")
            # result = 'Is this thing on'
            return result
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            raise

def test_openai_activities():
    async def run_test():
        activity_instance = OpenAIActivities()
        prompt = "What is the capital of France?"
        try:
            result = await activity_instance.call_openai_api(prompt)
            print(f"Test result: {result}")
        except Exception as e:
            print(f"Test failed with error: {e}")

    asyncio.run(run_test())

# Uncomment the following line to run the test function
if __name__ == "__main__":
    test_openai_activities()