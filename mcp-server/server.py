#!/usr/bin/env python3
"""
Grandad Reminders MCP Server

An MCP server that allows ChatGPT/Claude to send messages
to grandad's display via the Railway app API.

Built with FastMCP for simplicity and clean code.
"""
import os
import logging
import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("grandad-mcp")

# Configuration
RAILWAY_APP_URL = os.environ.get(
    "GRANDAD_APP_URL",
    "https://gramps-production.up.railway.app"
)
API_ENDPOINT = f"{RAILWAY_APP_URL}/api/messages"

# Create FastMCP server instance
mcp = FastMCP("grandad-reminders")


@mcp.tool()
async def send_message_to_grandad(message: str) -> str:
    """
    Send a message to grandad's display screen.

    The message will appear on his screen at home. Accepts any language -
    typically used with Arabic messages. Use this when the user wants to
    send a message to their grandad.

    Args:
        message: The message to display to grandad. Can be in any language
                 (English, Arabic, etc.)

    Returns:
        Success message with details, or error message if something went wrong

    Examples:
        - send_message_to_grandad("العشاء الساعة 4 الليلة")
        - send_message_to_grandad("Doctor appointment tomorrow at 10am")
    """
    logger.info(f"Sending message to grandad: {message[:50]}...")

    try:
        # Send message to Railway app API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                API_ENDPOINT,
                json={"text": message},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            message_id = result.get("id", "unknown")
            timestamp = result.get("timestamp", "unknown")

            success_msg = (
                f"✅ Message sent successfully to grandad's display!\n\n"
                f"Message: {message}\n"
                f"Message ID: {message_id}\n"
                f"Timestamp: {timestamp}\n\n"
                f"Grandad will see this message on his screen."
            )

            logger.info(f"Message sent successfully. ID: {message_id}")
            return success_msg

    except httpx.HTTPStatusError as e:
        # Handle HTTP errors (4xx, 5xx)
        error_detail = ""
        try:
            error_detail = e.response.json().get("error", str(e))
        except Exception:
            error_detail = str(e)

        error_msg = (
            f"❌ Failed to send message to grandad's display.\n\n"
            f"Error: {error_detail}\n"
            f"Status code: {e.response.status_code}\n\n"
            f"Please try again or check if the app is running."
        )

        logger.error(f"HTTP error: {error_detail}")
        return error_msg

    except httpx.RequestError as e:
        # Handle connection errors
        error_msg = (
            f"❌ Could not connect to grandad's display app.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check:\n"
            f"1. Is the Railway app running?\n"
            f"2. Is the URL correct? ({RAILWAY_APP_URL})\n"
            f"3. Do you have internet connection?"
        )

        logger.error(f"Connection error: {e}")
        return error_msg

    except Exception as e:
        # Handle unexpected errors
        error_msg = (
            f"❌ Unexpected error while sending message.\n\n"
            f"Error: {str(e)}\n\n"
            f"Please check the MCP server logs for details."
        )

        logger.error(f"Unexpected error: {e}", exc_info=True)
        return error_msg


if __name__ == "__main__":
    # Run the MCP server
    logger.info(f"Starting Grandad Reminders MCP Server")
    logger.info(f"API Endpoint: {API_ENDPOINT}")

    # Check if we should run as HTTP server (for ChatGPT Desktop)
    # or stdio (for command line testing)
    import sys
    if "--http" in sys.argv or "-h" in sys.argv:
        # Run as HTTP server for ChatGPT Desktop connector
        port = int(os.environ.get("PORT", 8000))
        logger.info(f"Running in HTTP/SSE mode on port {port}")
        mcp.run(transport="sse", port=port)
    else:
        # Run as stdio server (default)
        logger.info(f"Running in stdio mode")
        mcp.run()