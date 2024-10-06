import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

async def main() -> None:
    client: Client = await Client.connect("localhost:7233", namespace="default")
    # Run the worker
    activities = BankingActivities()
    worker: Worker = Worker(
        client,
        task_queue="TASK_QUEUE_NAME",
        workflows=[],
        activities=[],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
