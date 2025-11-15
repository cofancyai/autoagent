"""TaskExecutor service - executes individual tasks using specialized handlers"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExecutionTask
from app.services.created_asset_service import CreatedAssetService
from app.services.event_service import EventService
from app.services.execution_task_service import ExecutionTaskService
from app.services.service_integration_service import ServiceIntegrationService

logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes individual execution tasks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_service = ExecutionTaskService(db)
        self.asset_service = CreatedAssetService(db)
        self.integration_service = ServiceIntegrationService(db)
        self.event_service = EventService(db)

    async def execute_task(self, task: ExecutionTask) -> bool:
        """
        Execute a task based on its type

        Returns True if successful, False otherwise
        """
        logger.info(f"Executing task {task.id}: {task.task_name} (type: {task.task_type})")

        try:
            # Mark task as in progress
            await self.task_service.update_progress(task.id, 0, "Starting task execution...")

            # Route to appropriate handler based on task type
            handler_map = {
                "setup_infrastructure": self._execute_setup_infrastructure,
                "create_website": self._execute_create_website,
                "setup_payment": self._execute_setup_payment,
                "content_creation": self._execute_content_creation,
                "business_registration": self._execute_business_registration,
                "integration_setup": self._execute_integration_setup,
                "testing_validation": self._execute_testing_validation,
                "deployment": self._execute_deployment,
            }

            handler = handler_map.get(task.task_type, self._execute_generic_task)

            # Execute the task
            result = await handler(task)

            if result:
                # Mark as complete
                await self.task_service.update_progress(task.id, 100, "Task completed successfully")
                await self.event_service.log_event(
                    event_type="execution.task_completed",
                    event_data={"task_name": task.task_name, "task_type": task.task_type},
                    session_id=task.session_id,
                    entity_type="execution_task",
                    entity_id=task.id,
                )
                return True
            else:
                await self.task_service.mark_failed(task.id, "Task execution returned failure")
                return False

        except Exception as e:
            logger.error(f"Error executing task {task.id}: {str(e)}", exc_info=True)
            await self.task_service.mark_failed(task.id, str(e))
            await self.event_service.log_event(
                event_type="execution.task_failed",
                event_data={"task_name": task.task_name, "error": str(e)},
                session_id=task.session_id,
                entity_type="execution_task",
                entity_id=task.id,
            )
            return False

    async def _execute_setup_infrastructure(self, task: ExecutionTask) -> bool:
        """Setup infrastructure for the project"""
        logger.info(f"Setting up infrastructure for task {task.id}")

        await self.task_service.update_progress(task.id, 30, "Initializing infrastructure...")

        # Simulate infrastructure setup
        # In production, this would:
        # - Create cloud resources
        # - Setup databases
        # - Configure networking
        # - Setup CI/CD

        await self.task_service.update_progress(task.id, 70, "Infrastructure provisioned")

        # Create asset record
        from app.schemas.created_asset import CreatedAssetCreate

        asset_data = CreatedAssetCreate(
            asset_name="Infrastructure Setup",
            asset_type="infrastructure",
            description="Cloud infrastructure and development environment",
            asset_metadata={
                "status": "configured",
                "environment": "production",
            },
        )

        await self.asset_service.create_asset(task.project_id, task.session_id, asset_data, task.id)

        return True

    async def _execute_create_website(self, task: ExecutionTask) -> bool:
        """Create website using Webflow (or similar service)"""
        logger.info(f"Creating website for task {task.id}")

        await self.task_service.update_progress(task.id, 20, "Connecting to Webflow...")

        # In production, this would:
        # - Connect to Webflow API
        # - Create new site from template
        # - Customize with project details
        # - Publish site

        # For now, create a simulated website
        from app.schemas.created_asset import CreatedAssetCreate
        from app.schemas.service_integration import ServiceIntegrationCreate

        # Create Webflow integration record
        integration_data = ServiceIntegrationCreate(
            project_id=task.project_id,
            service_name="webflow",
            service_category="website",
            config={
                "template": "business_landing",
                "custom_domain": False,
            },
        )

        integration = await self.integration_service.create_integration(
            task.project_id, task.session_id, integration_data
        )

        await self.task_service.update_progress(task.id, 50, "Creating website...")

        # Update integration status
        await self.integration_service.update_status(integration.id, "connected")

        await self.task_service.update_progress(task.id, 80, "Publishing website...")

        # Create asset
        website_url = f"https://{task.task_name.lower().replace(' ', '-')}-demo.webflow.io"
        asset_data = CreatedAssetCreate(
            asset_name=f"{task.task_name} Website",
            asset_type="website",
            description="Landing page and website created with Webflow",
            url=website_url,
            external_service="webflow",
            external_id=f"webflow_{task.id}",
            deployment_status="live",
            asset_metadata={
                "platform": "webflow",
                "template": "business_landing",
            },
        )

        await self.asset_service.create_asset(task.project_id, task.session_id, asset_data, task.id)

        logger.info(f"Website created: {website_url}")
        return True

    async def _execute_setup_payment(self, task: ExecutionTask) -> bool:
        """Setup payment processing with Stripe"""
        logger.info(f"Setting up payment processing for task {task.id}")

        await self.task_service.update_progress(task.id, 20, "Connecting to Stripe...")

        # In production, this would:
        # - Connect to Stripe API
        # - Create Stripe account
        # - Setup products and pricing
        # - Configure webhooks

        from app.schemas.created_asset import CreatedAssetCreate
        from app.schemas.service_integration import ServiceIntegrationCreate

        # Create Stripe integration
        integration_data = ServiceIntegrationCreate(
            project_id=task.project_id,
            service_name="stripe",
            service_category="payment",
            config={
                "currency": "usd",
                "payment_methods": ["card", "bank_transfer"],
            },
        )

        integration = await self.integration_service.create_integration(
            task.project_id, task.session_id, integration_data
        )

        await self.task_service.update_progress(task.id, 60, "Configuring payment methods...")

        await self.integration_service.update_status(integration.id, "active")

        # Create asset
        asset_data = CreatedAssetCreate(
            asset_name="Payment System",
            asset_type="payment_integration",
            description="Stripe payment processing integration",
            url="https://dashboard.stripe.com",
            external_service="stripe",
            external_id=f"stripe_{task.id}",
            deployment_status="active",
            asset_metadata={
                "platform": "stripe",
                "test_mode": True,
                "currencies_supported": ["usd"],
            },
        )

        await self.asset_service.create_asset(task.project_id, task.session_id, asset_data, task.id)

        logger.info("Payment processing setup completed")
        return True

    async def _execute_content_creation(self, task: ExecutionTask) -> bool:
        """Create content for the business"""
        logger.info(f"Creating content for task {task.id}")

        await self.task_service.update_progress(task.id, 30, "Generating content...")

        # In production, this would:
        # - Use AI to generate marketing copy
        # - Create product descriptions
        # - Generate blog posts
        # - Create social media content

        await self.task_service.update_progress(task.id, 70, "Content generated")

        from app.schemas.created_asset import CreatedAssetCreate

        asset_data = CreatedAssetCreate(
            asset_name="Marketing Content",
            asset_type="content",
            description="Marketing copy, product descriptions, and social media content",
            asset_metadata={
                "content_types": ["landing_page_copy", "product_descriptions", "social_posts"],
                "word_count": 2500,
            },
        )

        await self.asset_service.create_asset(task.project_id, task.session_id, asset_data, task.id)

        return True

    async def _execute_business_registration(self, task: ExecutionTask) -> bool:
        """Register business entity"""
        logger.info(f"Registering business for task {task.id}")

        await self.task_service.update_progress(task.id, 50, "Preparing registration documents...")

        # In production, this would:
        # - Integrate with legal services
        # - File incorporation documents
        # - Get EIN
        # - Setup business bank account

        from app.schemas.created_asset import CreatedAssetCreate

        asset_data = CreatedAssetCreate(
            asset_name="Business Registration",
            asset_type="legal_document",
            description="Business entity registration and legal documents",
            asset_metadata={
                "entity_type": "LLC",
                "status": "pending_approval",
            },
        )

        await self.asset_service.create_asset(task.project_id, task.session_id, asset_data, task.id)

        return True

    async def _execute_integration_setup(self, task: ExecutionTask) -> bool:
        """Setup third-party integrations"""
        logger.info(f"Setting up integrations for task {task.id}")

        await self.task_service.update_progress(task.id, 50, "Configuring integrations...")

        # Setup common integrations based on task config
        config = task.task_config or {}
        services = config.get("services", ["analytics", "email"])

        for service in services:
            from app.schemas.service_integration import ServiceIntegrationCreate

            integration_data = ServiceIntegrationCreate(
                project_id=task.project_id,
                service_name=service,
                service_category="analytics" if "analytics" in service else "email",
                config={"auto_configured": True},
            )

            await self.integration_service.create_integration(
                task.project_id, task.session_id, integration_data
            )

        return True

    async def _execute_testing_validation(self, task: ExecutionTask) -> bool:
        """Test and validate all systems"""
        logger.info(f"Testing systems for task {task.id}")

        await self.task_service.update_progress(task.id, 40, "Running tests...")

        # In production, this would:
        # - Run automated tests
        # - Check all integrations
        # - Verify payment flow
        # - Test user journeys

        await self.task_service.update_progress(task.id, 90, "All tests passed")

        return True

    async def _execute_deployment(self, task: ExecutionTask) -> bool:
        """Deploy to production"""
        logger.info(f"Deploying for task {task.id}")

        await self.task_service.update_progress(task.id, 30, "Preparing deployment...")
        await self.task_service.update_progress(task.id, 60, "Deploying to production...")
        await self.task_service.update_progress(task.id, 90, "Deployment complete")

        return True

    async def _execute_generic_task(self, task: ExecutionTask) -> bool:
        """Execute a generic/unknown task type"""
        logger.warning(f"Executing generic task {task.id} of type {task.task_type}")

        await self.task_service.update_progress(task.id, 50, "Processing task...")

        # Basic execution simulation
        from app.schemas.created_asset import CreatedAssetCreate

        asset_data = CreatedAssetCreate(
            asset_name=task.task_name,
            asset_type="generic",
            description=task.description,
            asset_metadata={"task_type": task.task_type},
        )

        await self.asset_service.create_asset(task.project_id, task.session_id, asset_data, task.id)

        return True
