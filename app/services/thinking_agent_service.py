"""ThinkingAgent Service - Core AI reasoning logic"""

import json
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.anthropic_client import AnthropicClient
from app.models.approval import ApprovalCheckpoint
from app.models.goal import Goal
from app.models.message import Message
from app.models.thinking_process import ThinkingProcess
from app.schemas.approval import ApprovalCheckpointCreate, OptionSchema
from app.services.approval_service import ApprovalService
from app.services.event_service import EventService
from app.services.message_service import MessageService
from app.services.prompts import SYSTEM_PROMPT, build_thinking_prompt

logger = logging.getLogger(__name__)


class ThinkingAgentService:
    """Service for AI-powered thinking and decision generation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_client = AnthropicClient()
        self.approval_service = ApprovalService(db)
        self.message_service = MessageService(db)
        self.event_service = EventService(db)

    async def process_user_message(
        self, session_id: UUID, user_message: Message
    ) -> Optional[ApprovalCheckpoint]:
        """
        Process a user message and generate strategic options

        Args:
            session_id: The session ID
            user_message: The user's message object

        Returns:
            ApprovalCheckpoint if options were generated, None otherwise
        """
        logger.info("=" * 80)
        logger.info("ThinkingAgent: Starting AI processing for user message")
        logger.info("=" * 80)
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Message ID: {user_message.id}")
        logger.info(f"User Message: {user_message.content}")
        logger.debug(f"Message Role: {user_message.role}")

        # Get conversation history for context
        logger.debug("Fetching conversation history...")
        conversation_history = await self.message_service.get_conversation_history(
            session_id, limit=5
        )
        logger.info(f"Retrieved {len(conversation_history)} previous messages for context")

        # Build the thinking prompt
        logger.debug("Building thinking prompt...")
        prompt = build_thinking_prompt(user_message.content, conversation_history)
        logger.debug(f"Prompt Length: {len(prompt)} chars")
        logger.debug(f"Prompt Preview: {prompt[:200]}...")

        # Use Claude to generate strategic options
        try:
            # Select appropriate model (Sonnet for balanced quality/speed)
            logger.debug("Selecting appropriate model for task...")
            model = await self.llm_client.select_model_for_task("approval_presentation")
            logger.info(f"Selected Model: {model.value}")

            # Call Claude API
            logger.info("Calling LLM API to generate strategic options...")
            response = await self.llm_client.generate(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                system_context=SYSTEM_PROMPT,
                use_cache=True,  # Cache system prompt for cost savings
            )

            logger.info("LLM API call successful")
            logger.debug(f"Response Model: {response.get('model')}")
            logger.debug(f"Response Latency: {response.get('latency_ms')}ms")
            logger.debug(f"Token Usage: {response.get('usage')}")
            logger.debug(f"Response Content Length: {len(response.get('content', ''))} chars")

            # Parse the JSON response
            logger.debug("Parsing AI response JSON...")
            thinking_result = self._parse_ai_response(response["content"])

            if not thinking_result or "options" not in thinking_result:
                logger.warning("Failed to parse AI response or no options generated")
                logger.debug(f"Thinking Result: {thinking_result}")
                return None

            logger.info(
                f"Successfully parsed AI response with {len(thinking_result.get('options', []))} options"
            )
            logger.debug(
                f"Options: {[opt.get('name') for opt in thinking_result.get('options', [])]}"
            )

            # Create thinking process record
            logger.debug("Creating thinking process record...")
            thinking_process = await self._create_thinking_process(
                session_id=session_id,
                input_data={"user_message": user_message.content, "prompt": prompt},
                reasoning_steps=thinking_result.get("analysis"),
                output_data=thinking_result,
            )
            logger.info(f"Thinking Process created: {thinking_process.id}")

            # Create approval checkpoint with the generated options
            logger.debug("Creating approval checkpoint...")
            approval_checkpoint = await self._create_approval_from_thinking(
                session_id=session_id,
                thinking_process_id=thinking_process.id,
                thinking_result=thinking_result,
                user_message=user_message.content,
            )
            logger.info(f"Approval Checkpoint created: {approval_checkpoint.id}")

            # Create assistant message with the analysis
            logger.debug("Creating assistant response message...")
            await self._create_assistant_response(
                session_id=session_id,
                thinking_result=thinking_result,
                approval_id=approval_checkpoint.id,
            )
            logger.info("Assistant response message created")

            # Log event
            logger.debug("Logging completion event...")
            await self.event_service.log_event(
                event_type="ai.thinking_completed",
                event_data={
                    "session_id": str(session_id),
                    "thinking_process_id": str(thinking_process.id),
                    "approval_id": str(approval_checkpoint.id),
                    "options_count": len(thinking_result["options"]),
                },
                session_id=session_id,
            )

            await self.db.commit()
            logger.info("Database transaction committed successfully")
            logger.info("=" * 80)
            logger.info("ThinkingAgent: AI processing completed successfully")
            logger.info("=" * 80)

            return approval_checkpoint

        except Exception as e:
            logger.error("=" * 80)
            logger.error("ThinkingAgent: AI processing FAILED")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            logger.error("=" * 80)

            await self.db.rollback()
            logger.debug("Database transaction rolled back")

            # Log error
            try:
                await self.event_service.log_event(
                    event_type="ai.thinking_failed",
                    event_data={"error": str(e), "user_message": user_message.content},
                    session_id=session_id,
                )
                logger.debug("Error event logged successfully")
            except Exception as log_error:
                logger.error(f"Failed to log error event: {log_error}")

            raise

    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the AI response JSON"""
        try:
            # Try to extract JSON from the response
            # Claude sometimes wraps JSON in markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()

            return json.loads(response_text)
        except json.JSONDecodeError:
            # If parsing fails, return None
            return None

    async def _create_thinking_process(
        self,
        session_id: UUID,
        input_data: Dict[str, Any],
        reasoning_steps: str,
        output_data: Dict[str, Any],
    ) -> ThinkingProcess:
        """Create a thinking process record"""
        thinking_process = ThinkingProcess(
            session_id=session_id,
            process_type="option_generation",
            input_data=input_data,
            reasoning_steps={"analysis": reasoning_steps},
            output_data=output_data,
            status="completed",
        )

        self.db.add(thinking_process)
        await self.db.flush()
        await self.db.refresh(thinking_process)

        return thinking_process

    async def _create_approval_from_thinking(
        self,
        session_id: UUID,
        thinking_process_id: UUID,
        thinking_result: Dict[str, Any],
        user_message: str,
    ) -> ApprovalCheckpoint:
        """Create an approval checkpoint from AI thinking results"""

        # Convert options to the schema format
        options = []
        for opt in thinking_result["options"]:
            options.append(
                OptionSchema(
                    name=opt["name"],
                    pros=opt.get("pros", []),
                    cons=opt.get("cons", []),
                    description=opt.get("description"),
                )
            )

        # Create the approval checkpoint
        approval_data = ApprovalCheckpointCreate(
            checkpoint_type="strategic_decision",
            decision_needed=f"Choose your approach: {user_message[:100]}",
            options=options,
            recommended_option=thinking_result.get("recommended_option", 0),
            thinking_process_id=thinking_process_id,
        )

        approval = await self.approval_service.create_checkpoint(session_id, approval_data)

        return approval

    async def _create_assistant_response(
        self,
        session_id: UUID,
        thinking_result: Dict[str, Any],
        approval_id: UUID,
    ) -> Message:
        """Create an assistant message with the analysis"""

        analysis = thinking_result.get("analysis", "I've analyzed your request.")
        options_summary = f"\n\nI've generated {len(thinking_result['options'])} strategic options for you to consider."

        message_content = f"{analysis}{options_summary}"

        # Create assistant message
        assistant_message = Message(
            session_id=session_id,
            role="assistant",
            content=message_content,
            extra_data={"approval_id": str(approval_id), "type": "thinking_response"},
        )

        self.db.add(assistant_message)
        await self.db.flush()
        await self.db.refresh(assistant_message)

        return assistant_message

    async def execute_approved_decision(
        self, session_id: UUID, approval_id: UUID, selected_option: int
    ) -> Dict[str, Any]:
        """
        Execute actions based on approved decision

        This is where you would implement actual execution logic
        based on the user's approved choice.
        """
        # Get the approval checkpoint
        approval = await self.approval_service.get_checkpoint(approval_id)
        if not approval:
            raise ValueError("Approval checkpoint not found")

        # Get the selected option
        if selected_option >= len(approval.options):
            raise ValueError("Invalid option selected")

        selected = approval.options[selected_option]

        # Create a goal based on the selected option
        goal = Goal(
            session_id=session_id,
            description=f"Execute: {selected['name']}",
            status="in_progress",
            priority=1,
            result={"selected_option": selected, "approval_id": str(approval_id)},
        )

        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)

        # Log execution started
        await self.event_service.log_goal_event(
            session_id=session_id,
            goal_id=goal.id,
            event_type="goal.execution_started",
            event_data={"option": selected["name"]},
        )

        await self.db.commit()

        return {
            "goal_id": str(goal.id),
            "selected_option": selected,
            "status": "execution_started",
        }
