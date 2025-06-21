"""
Command-line interface for the agent architecture.
"""

import argparse
import asyncio

from .orchestrator import AgentOrchestrator


async def async_main():
    """Async main function."""
    parser = argparse.ArgumentParser(description="Agent Architecture CLI")
    parser.add_argument("--query", "-q", help="Query to process")
    parser.add_argument("--files", "-f", nargs="*", help="Files to include")
    parser.add_argument("--working-dir", "-w", default=".", help="Working directory")

    args = parser.parse_args()

    if not args.query:
        print("Please provide a query with --query")
        return

    # Initialize orchestrator
    orchestrator = AgentOrchestrator(working_directory=args.working_dir)
    await orchestrator.start_all_agents()

    try:
        # Process query
        response = await orchestrator.process_query(
            query=args.query,
            files=args.files
        )

        print(f"Agent: {response.agent_type.value}")
        print(f"Status: {response.status.value}")
        print(f"Response: {response.content}")

        if response.metadata:
            print(f"Metadata: {response.metadata}")

    finally:
        await orchestrator.stop_all_agents()


def main():
    """CLI entry point for console scripts."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
