## Some MCP Servers to consider
- my git_manager_mcp
- Context7
- Git (maybe)
- Brave Search // Google Search Console??
DuckDuckGo ... or, can I just crawl4AI?
- Database?
- Email

- FileScopeMCP? - Analyzes your codebase identifying important files based on dependency relationships. Generates diagrams and importance scores per file, helping AI assistants understand the codebase. Automatically parses popular programming languages such as Python, C, C++, Rust, Zig, Lua.

- Hyperbrowser
- mcp-run-python
- 21st.dev Magic ? craftd UI components



Done through Library
- Crawl4AI
- File System


-- CONSIDERATIONS
-> we need to generate series of questions when creating and reviewing tasks (we seem to forget to actually hook things up together, like we made a memory system but didn't give it to the agent)
-> maybe some sort of sprint planning session between agents when we are breaking out tasks (could also use this to populate the tasks with descriptions and use GitHub Project Manager MCP to track)
-> Cursor agent seems to stop every so often, maybe we could have some sort of monitor - maybe the agent waiting for a response could subscribe to some sort of listen event, so it would know that the agents have stopped working and look into the issue






# AGENT ARCHITECTURE PLAN

## ORCHESTRATOR

@Overview
- my interface to my_coding_agent tool (who I talk to in the chat interface)
- Discusses what I want at a high level, ask clarifying questions, obtains my vision
- Does preliminary web search and gathers context
- Tasks Research Agent to start research on VISION
- Reviews research on the vision, and does additional web search based on research to gain more context
- Tasks Research Agent to refine research with additional context details to align with vision to gather intel on similar projects, lessons learned, gotchas, potential issues, research papers
- Reviews all of the additional research and summarizes it in a project_research.md file
- Consults SENIOR_ARCHITECT agent for high level architecture plan
- Reviews the results and gets Research Agent to do research on any gaps in understanding or questions from the architect
- Provides results and direction to the Senior Architect who will then generate the architecture_plan.md
- Will review the plan and approve or continue to gather research and re-engage Senior Architect until statisfied with plan
- Will provide vision, project_research.md, architecture_plan.md to PROJECT_PLANNING_AGENT
- will recieve back GOALS, HIGH-LEVEL-PRODUCT ROADMAP with milestones and deliverables broken out into RELEASES, each with a defined set of features to include
- will review the roadmap and ensure it addresses the vision and adheres to the direction given
- will review the release inputs and outputs to determine if each release will have the inputs it needs
- will provide the materials to the SYSTEM ARCHITECT for review and to update the architecture_plan.md
- will review the updated architecture to update the roadmap to include which portions of the system are impacted by each release
- will provide the updated roadmap and architecture plan back to the PROJECT_PLANNING_AGENT to review and to ensure features consider the system architecture and any changes that need to be made
- will direct RESEARCH_AGENT to research areas related to the ROADMAP and ARCHITECTURE PLAN and collect the information into the Project Research portion of the Database
- will create an overall project tracking document that just has releases and features listed with their current completion status
WHILE PROJECT IS NOT COMPLETE:
- will pick the next release and provide it and all of the materials to the RELEASE_PLANNING_AGENT and get the CURRENT_RELEASE_PLAN
- will receive and review the CURRENT_RELEASE_PLAN and determine if it is complete and makes sense when considering the updated research
- will update if necessary and then approve the CURRENT_RELEASE_PLAN (which is a PRD)
- will provide CURRENT_RELEASE_PLAN to Team Lead as a PRD, along with the design artefacts
- will respond to any questions from the Team Lead to provide direction and clarity and direct them to start processing the tasks
- will review the team leads report after the completion of each task
- will ensure the team lead is following the release plan and provide direction as needed to ensure the release plan is adhered to
- will update feature status as they are completed in the tracking document
- will review release report from team lead when release is complete
- will provide release report to research agent to ensure all database is updated if necessary
- will email the release report to me and wait for direction to continue or make changes
- will direct changes as requested
- will mark release complete

WHEN ALL RELEASES are complete
- will provide final project report to me via email and ask if for guidance
- will direct additional releases to be planned if necessary

@Capabilities
- Sequential Thought
- Web Search using CRAWL4AI



## RESEARCH_AGENT

@Overview
- will conduct research on requested topic by using sequential thinking and web search
-- >> When using sequential-thinking, use as many steps as possible. Each step of sequential-thinking must use branches, isRevision, and needsMoreThoughts, and each branch must have at least 3 steps. Before each step of sequential-thinking, use WEB_SEARCH_TOOL to search for 3 related web pages and then think about the content of the web pages. The final reply should be long enough and well-structured.
-- NOTE: I might just make a DeepResearch MCP server for this...
-- Based on preliminary research, provide query to Deep Research MCP Server
-- review the reply
-- populate the database
-- inform the orchestrator that the research is complete

-- >>

@Capabilities
- Sequential Thought
- Web Search
- DeepResearch MCP SERVER - BUILD THIS
- Database

## ARCHITECT

@Overview
- multi-agent workflow (probably will make this as a stand alone MCP server)
-- sends query to my architect mcp server
-- reviews results
-- formats results as requested
-- sends reply






HIGH_LEVEL_TO_DO:
[ ] Make a web search mcp server
[ ] Make sequential thought mcp server
[ ] Make deep research mcp server that uses my web search mcp server with sequential thought mcp server
[ ] Make orchestrator agent that has access to those MCP servers
[ ] Make software architect AI Agent
[ ] Make TDD software developer AI Agent (AI Agent with file reading ability and git/terminal ability that when given code base and a story, will write unit tests and passing code, verify that all tests pass) and inform when the story is complete with all passing tests
[ ] Make Team Lead AI Agent that can tasks TDD software developers
