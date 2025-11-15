"""ProjectOrchestrator service - coordinates business execution from approval to completion"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.anthropic_client import ModelType, anthropic_client
from app.models import ApprovalCheckpoint, Decision
from app.schemas.created_asset import CreatedAssetCreate
from app.schemas.execution_project import ExecutionProjectCreate
from app.schemas.execution_task import ExecutionTaskCreate
from app.services.created_asset_service import CreatedAssetService
from app.services.event_service import EventService
from app.services.execution_project_service import ExecutionProjectService
from app.services.execution_task_service import ExecutionTaskService
from app.services.message_service import MessageService
from app.services.service_integration_service import ServiceIntegrationService

logger = logging.getLogger(__name__)


class ProjectOrchestrator:
    """Orchestrates business execution projects from approval to completion"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.project_service = ExecutionProjectService(db)
        self.task_service = ExecutionTaskService(db)
        self.asset_service = CreatedAssetService(db)
        self.integration_service = ServiceIntegrationService(db)
        self.event_service = EventService(db)
        self.message_service = MessageService(db)

    async def execute_approved_decision(
        self, session_id: UUID, approval: ApprovalCheckpoint, decision: Decision
    ) -> Dict[str, Any]:
        """
        Execute approved decision - main entry point for execution

        This takes an approved strategic option and:
        1. Creates an ExecutionProject
        2. Breaks it down into tasks using AI
        3. Starts execution
        4. Returns project info
        """
        logger.info(f"Executing approved decision for session {session_id}")

        try:
            # Get selected option details
            selected_option = approval.options[decision.selected_option]
            logger.info(f"Selected option: {selected_option.get('title', 'Unknown')}")

            # Create execution project
            project = await self._create_project_from_decision(
                session_id, approval, selected_option, decision
            )

            # Log event
            await self.event_service.log_event(
                event_type="execution.started",
                event_data={
                    "project_id": str(project.id),
                    "project_name": project.project_name,
                    "business_type": project.business_type,
                },
                session_id=session_id,
                entity_type="execution_project",
                entity_id=project.id,
            )

            # Generate task breakdown using AI
            tasks = await self._generate_task_breakdown(project, selected_option, decision)

            # Send progress update to user
            await self.message_service.create_message(
                session_id,
                {
                    "role": "assistant",
                    "content": f"🚀 **Project Execution Started**\n\n"
                    f"**Project:** {project.project_name}\n"
                    f"**Type:** {project.business_type}\n"
                    f"**Tasks Created:** {len(tasks)}\n\n"
                    f"I'm now executing your business plan. I'll update you on progress!",
                },
            )

            # Start execution in background (non-blocking)
            asyncio.create_task(self._execute_project_tasks(project.id, session_id))

            return {
                "project_id": str(project.id),
                "project_name": project.project_name,
                "task_count": len(tasks),
                "status": "executing",
            }

        except Exception as e:
            logger.error(f"Error executing decision: {str(e)}", exc_info=True)
            await self.event_service.log_event(
                event_type="execution.error",
                event_data={"error": str(e)},
                session_id=session_id,
            )
            raise

    async def _create_project_from_decision(
        self,
        session_id: UUID,
        approval: ApprovalCheckpoint,
        selected_option: Dict[str, Any],
        decision: Decision,
    ) -> Any:
        """Create ExecutionProject from approved decision"""

        # Extract project details from option
        project_name = selected_option.get("title", "Business Project")
        description = selected_option.get("description", "")

        # Determine business type from context
        business_type = self._infer_business_type(selected_option, approval)

        # Create project data
        project_data = ExecutionProjectCreate(
            project_name=project_name,
            business_type=business_type,
            description=description,
            total_budget=None,  # Could be extracted from option if available
            estimated_completion_date=datetime.utcnow() + timedelta(days=30),
            requirements={
                "selected_option": selected_option,
                "decision_reasoning": decision.reasoning,
                "modifications": decision.modifications,
                "original_checkpoint": approval.decision_needed,
            },
            execution_plan=selected_option.get("execution_steps", []),
        )

        project = await self.project_service.create_project(session_id, project_data)
        await self.db.flush()
        logger.info(f"Created project: {project.id} - {project.project_name}")
        return project

    def _infer_business_type(
        self, selected_option: Dict[str, Any], approval: ApprovalCheckpoint
    ) -> str:
        """Infer business type from option and approval context"""
        # Check for keywords in option and approval text
        text = f"{selected_option.get('title', '')} {selected_option.get('description', '')} {approval.decision_needed}".lower()

        if "saas" in text or "software" in text or "app" in text:
            return "saas"
        elif "ecommerce" in text or "store" in text or "shop" in text:
            return "ecommerce"
        elif "marketplace" in text:
            return "marketplace"
        elif "service" in text or "consulting" in text:
            return "service_business"
        else:
            return "general"

    async def _generate_task_breakdown(
        self, project: Any, selected_option: Dict[str, Any], decision: Decision
    ) -> List[Any]:
        """Use AI to break down project into specific executable tasks"""

        logger.info(f"Generating task breakdown for project {project.id}")

        # Build prompt for AI
        prompt = f"""You are a business execution AI. Break down this business project into specific, executable tasks.

**Project:** {project.project_name}
**Type:** {project.business_type}
**Description:** {project.description}

**Selected Strategy:**
{json.dumps(selected_option, indent=2)}

**User Modifications:** {decision.modifications or "None"}

Generate a task breakdown with these task types:
- "setup_infrastructure": Setup technical infrastructure
- "create_website": Create website/landing page (using Webflow)
- "setup_payment": Setup payment processing (using Stripe)
- "content_creation": Create content/copy
- "business_registration": Register business entity
- "integration_setup": Setup third-party integrations
- "testing_validation": Test and validate everything
- "deployment": Deploy to production

For each task, provide:
1. task_name: Clear task name
2. task_type: One of the types above
3. description: What needs to be done
4. priority: 1-10 (higher = more urgent)
5. dependencies: List of task indices this depends on (empty array if none)
6. estimated_duration_hours: How long it will take
7. task_config: Specific configuration for this task type

Return a JSON array of tasks. Be specific and actionable.
"""

        try:
            response = await anthropic_client.generate(
                model=ModelType.SONNET,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )

            # Parse tasks from response
            tasks_json = self._extract_json_from_response(response["content"])
            if not tasks_json:
                raise ValueError("Failed to extract task breakdown from AI response")

            # Create tasks in database
            created_tasks = []
            for idx, task_data in enumerate(tasks_json):
                task_create = ExecutionTaskCreate(
                    task_name=task_data.get("task_name", f"Task {idx + 1}"),
                    task_type=task_data.get("task_type", "general"),
                    description=task_data.get("description", ""),
                    assigned_agent=f"{task_data.get('task_type', 'general')}_agent",
                    priority=task_data.get("priority", 5),
                    dependencies=task_data.get("dependencies", []),
                    blocking_tasks=None,
                    task_config=task_data.get("task_config", {}),
                    estimated_duration_hours=task_data.get("estimated_duration_hours", 2),
                )

                task = await self.task_service.create_task(
                    project.id, project.session_id, task_create
                )
                created_tasks.append(task)

            await self.db.flush()
            logger.info(f"Created {len(created_tasks)} tasks for project {project.id}")
            return created_tasks

        except Exception as e:
            logger.error(f"Error generating task breakdown: {str(e)}", exc_info=True)
            # Fallback: create basic tasks
            return await self._create_fallback_tasks(project)

    def _extract_json_from_response(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """Extract JSON array from AI response"""
        try:
            # Try to find JSON in the response
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON from response: {str(e)}")
            return None

    async def _create_fallback_tasks(self, project: Any) -> List[Any]:
        """Create basic fallback tasks if AI generation fails"""
        logger.warning(f"Using fallback tasks for project {project.id}")

        basic_tasks = [
            {
                "task_name": "Setup Project Infrastructure",
                "task_type": "setup_infrastructure",
                "description": "Initialize project infrastructure and environment",
                "priority": 10,
            },
            {
                "task_name": "Create Website",
                "task_type": "create_website",
                "description": f"Create website for {project.project_name}",
                "priority": 8,
            },
            {
                "task_name": "Setup Payment Processing",
                "task_type": "setup_payment",
                "description": "Configure payment processing system",
                "priority": 7,
            },
            {
                "task_name": "Test and Validate",
                "task_type": "testing_validation",
                "description": "Test all systems and validate functionality",
                "priority": 5,
            },
        ]

        created_tasks = []
        for task_data in basic_tasks:
            task_create = ExecutionTaskCreate(
                task_name=task_data["task_name"],
                task_type=task_data["task_type"],
                description=task_data["description"],
                assigned_agent=f"{task_data['task_type']}_agent",
                priority=task_data["priority"],
                dependencies=[],
                estimated_duration_hours=4,
            )

            task = await self.task_service.create_task(
                project.id, project.session_id, task_create
            )
            created_tasks.append(task)

        await self.db.flush()
        return created_tasks

    async def _execute_project_tasks(self, project_id: UUID, session_id: UUID):
        """Execute project tasks in order based on dependencies"""
        logger.info(f"Starting task execution for project {project_id}")

        try:
            # Import here to avoid circular dependency
            from app.services.task_executor_service import TaskExecutor

            executor = TaskExecutor(self.db)

            # Get all tasks for the project
            all_tasks = await self.task_service.list_tasks(project_id=project_id)

            while True:
                # Get tasks that are ready to execute
                ready_tasks = await self.task_service.get_ready_tasks(project_id)

                if not ready_tasks:
                    # Check if all tasks are complete
                    completed_count = sum(1 for t in all_tasks if t.status == "completed")
                    if completed_count == len(all_tasks):
                        logger.info(f"All tasks completed for project {project_id}")
                        await self._finalize_project(project_id, session_id)
                        break
                    else:
                        logger.info(f"No ready tasks, waiting... ({completed_count}/{len(all_tasks)} complete)")
                        await asyncio.sleep(5)
                        # Refresh task list
                        all_tasks = await self.task_service.list_tasks(project_id=project_id)
                        continue

                # Execute ready tasks (could be parallel in future)
                for task in ready_tasks[:1]:  # Execute one at a time for now
                    logger.info(f"Executing task: {task.task_name}")
                    try:
                        await executor.execute_task(task)
                    except Exception as e:
                        logger.error(f"Error executing task {task.id}: {str(e)}", exc_info=True)
                        await self.task_service.mark_failed(task.id, str(e))

                # Update project progress
                await self._update_project_progress(project_id)

                # Short delay before next iteration
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error in task execution loop: {str(e)}", exc_info=True)

    async def _update_project_progress(self, project_id: UUID):
        """Update project progress based on task completion"""
        tasks = await self.task_service.list_tasks(project_id=project_id)

        if not tasks:
            return

        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        progress = Decimal(str((completed_tasks / total_tasks) * 100))

        await self.project_service.update_progress(project_id, progress)

    async def _finalize_project(self, project_id: UUID, session_id: UUID):
        """Finalize project when all tasks are complete"""
        logger.info(f"Finalizing project {project_id}")

        project = await self.project_service.get_project(project_id)
        if not project:
            return

        # Get all created assets
        assets = await self.asset_service.list_assets(project_id=project_id)

        # Build results summary
        results = {
            "status": "completed",
            "completion_date": datetime.utcnow().isoformat(),
            "total_tasks": len(await self.task_service.list_tasks(project_id=project_id)),
            "assets_created": len(assets),
            "asset_summary": [
                {
                    "name": asset.asset_name,
                    "type": asset.asset_type,
                    "url": asset.url,
                }
                for asset in assets
            ],
        }

        # Update project
        await self.project_service.update_project(
            project_id, {"status": "completed", "results": results}
        )

        # Send completion message to user
        await self.message_service.create_message(
            session_id,
            {
                "role": "assistant",
                "content": f"🎉 **Project Complete!**\n\n"
                f"**{project.project_name}** is now live!\n\n"
                f"**Assets Created:**\n"
                + "\n".join([f"- [{a.asset_name}]({a.url})" for a in assets if a.url])
                + "\n\nYour business is ready to launch! 🚀",
            },
        )

        await self.db.commit()
        logger.info(f"Project {project_id} finalized successfully")
